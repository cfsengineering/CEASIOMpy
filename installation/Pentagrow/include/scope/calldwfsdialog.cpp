
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#include <QProcess>
#include <QFileDialog>

#include <fstream>
#include <genua/sysinfo.h>
#include "scope.h"
#include "processmonitor.h"
#include "cfgeditor.h"
#include "calldwfsdialog.h"
#include "ui_calldwfsdialog.h"

#include <genua/mxmesh.h>

using namespace std;

QString CallDwfsDialog::workdir;
bool CallDwfsDialog::bShown = false;

CallDwfsDialog::CallDwfsDialog(QWidget *parent, MxMesh *mesh)
  : QDialog(parent, Qt::Tool), pmesh(mesh), m_ui(new Ui::CallDwfsDialog)
{
  m_ui->setupUi(this);
  QWidget::setAttribute(Qt::WA_DeleteOnClose);
  bShown = true;
  solverproc = new QProcess(this);
  pmoni = new ProcessMonitor(this, solverproc);
  connect(this, SIGNAL(rejected()), pmoni, SLOT(kill()) );

  simnames << tr("Check case");
  simnames << tr("Single steady case");
  simnames << tr("Rigid-body derivatives");

  simpos.resize(3);
  simpos[0] = "check";
  simpos[1] = "steady";
  simpos[2] = "coefficients";

  // solution types for which the UI has support
  m_ui->cbSimulation->addItem("Check case");
  m_ui->cbSimulation->addItem("Single steady case");
  m_ui->cbSimulation->addItem("Rigid-body derivatives");

  // connect button actions
  connect( m_ui->pbChangeSolver, SIGNAL(clicked()), SLOT(changeSolver()) );
  connect( m_ui->pbBrowse, SIGNAL(clicked()), this, SLOT(browseWorkDir()) );
  connect( m_ui->pbEditConfig, SIGNAL(clicked()), this, SLOT(editConfig()) );
  connect( m_ui->pbLoadConfig, SIGNAL(clicked()), this, SLOT(loadConfig()) );
  connect( m_ui->pbStart, SIGNAL(clicked()), this, SLOT(startProcess()) );
  connect( m_ui->leWorkDir, SIGNAL(editingFinished()), this, SLOT(changeWorkdir()) );

  // register finished slot
  connect( solverproc, SIGNAL(finished(int, QProcess::ExitStatus)),
           this, SLOT(finished()) );

  // set HostID field
  string pmac = SysInfo::primaryHardwareAddress();
  m_ui->lbHostID->setText( QString::fromStdString(pmac) );
  m_ui->lbHostID->setTextInteractionFlags(Qt::TextSelectableByMouse |
                                          Qt::TextSelectableByKeyboard);

  // set default logfile to stderr
  cfg["LogFile"] = "stderr";

  // fill in license key if present
  QString lkey = Scope::setting("dwfs-license-key").value<QString>();
  if (not lkey.isEmpty())
    m_ui->leLicenseKey->setText( lkey );

  // set reference dimensions in case these are stored
  XmlElement::const_iterator nit, nend = pmesh->noteEnd();
  for (nit = pmesh->noteBegin(); nit != nend; ++nit) {
    if (nit->name() == "GeometricReference") {
      m_ui->sbRefArea->setValue( nit->attr2float("area", 1.0) );
      m_ui->sbRefChord->setValue( nit->attr2float("chord", 1.0) );
      m_ui->sbRefSpan->setValue( nit->attr2float("span", 1.0) );
      Vct3 refpt;
      if (nit->hasAttribute("point"))
        fromString(nit->attribute("point"), refpt);
      m_ui->sbRefX->setValue(refpt[0]);
      m_ui->sbRefY->setValue(refpt[1]);
      m_ui->sbRefZ->setValue(refpt[2]);
    }
  }

  adjustSize();
}

CallDwfsDialog::~CallDwfsDialog()
{
  bShown = false;
  delete pmoni;
  delete solverproc;
  delete m_ui;
}

void CallDwfsDialog::meshFile(const QString & mf)
{
  mshfile = mf;
  m_ui->leCase->setText( QFileInfo(mf).baseName() );
}

void CallDwfsDialog::workDir(const QString & wd)
{
  workdir = wd;
  m_ui->leWorkDir->setText(workdir);
}

void CallDwfsDialog::browseWorkDir()
{
  QString dn = QFileDialog::getExistingDirectory(this, tr("Working directory for solver"), workdir);
  if (not dn.isEmpty()) {
    workdir = dn;
    m_ui->leWorkDir->setText(dn);
  }
}

void CallDwfsDialog::changeWorkdir()
{
  workdir = m_ui->leWorkDir->text();
}

void CallDwfsDialog::startProcess()
{
  // construct configuration file
  buildConfig();

  // copy mesh file to work directory
  QString mfilename = QFileInfo(mshfile).fileName();
  QString mtarget = workFile(mfilename);
  QFile::copy(mshfile, mtarget);
  cfg["MeshFile"] = mtarget.toStdString();

  // write configuration file
  string cfgfile = workFile(cfg["Case"] + ".cfg").toStdString();

  ofstream os(cfgfile.c_str());
  cfg.write(os);
  os.close();

  if (not locateSolver())
    return;

  QStringList args;
  args << QString::fromStdString(cfgfile);
  //solverproc->setProcessChannelMode(QProcess::MergedChannels);
  // solverproc.setReadChannel(QProcess::StandardOutput);
  QIODevice::OpenMode mode = QIODevice::ReadOnly |
                             QIODevice::Unbuffered |QIODevice::Text ;
  solverproc->setWorkingDirectory(workdir);
  solverproc->start(execpath, args, mode);

  // enable 'kill' button
  m_ui->pbStart->setEnabled(false);

  pmoni->clearDisplay();
  if (not pmoni->isVisible())
    pmoni->show();
}

void CallDwfsDialog::finished()
{
  if (solverproc->exitCode() == 0) {

    pmoni->appendOutput(tr("dwfs terminated successfully.\n"));

    // assemble result file path
    string sim(cfg["Simulation"]), vizfile;
    if (sim == "steady" or sim == "coefficients")
      vizfile = cfg["Case"] + "SteadyViz.xml";
    else if (sim == "check")
      vizfile = cfg["Case"] + "Wake.zml";

    // tell the receiver that we have a result file
    if (not vizfile.empty())
      emit solverFinished( workFile(vizfile) );
  } else {
    pmoni->appendOutput(tr("dwfs terminated with error.\n"
                           "See log for details.\n"));
  }

  m_ui->pbStart->setEnabled(true);
}

void CallDwfsDialog::loadConfig()
{
  QString caption = tr("Load configuration file");
  QString filter = tr("Config files (*.cfg);; All files (*.*)");
  QString fn = QFileDialog::getOpenFileName(this, caption, workdir, filter);
  if (not fn.isEmpty()) {
    ifstream in(fn.toUtf8().constData());
    cfg.read(in);
    fillForm();
  }
}

void CallDwfsDialog::editConfig()
{
  buildConfig();
  CfgEditor edit(this, cfg);
  if (edit.exec() == QDialog::Accepted) {
    edit.apply();
    fillForm();
  }
}

void CallDwfsDialog::fillForm()
{
  ConfigParser::iterator itr, last(cfg.end());
  for (itr = cfg.begin(); itr != last; ++itr) {
    const string & key = itr->first;
    QString val = QString::fromStdString(itr->second);
    if (key == "Case") {
      m_ui->leCase->setText(val);
    } else if (key == "Mach") {
      m_ui->rbMach->setChecked(true);
      m_ui->sbMach->setValue( val.toDouble() );
    } else if (key == "Speed") {
      m_ui->rbVelocity->setChecked(true);
      m_ui->sbVelocity->setValue( val.toDouble() );
    } else if (key == "Alpha") {
      m_ui->sbAlpha->setValue( val.toDouble() );
    } else if (key == "Beta") {
      m_ui->sbBeta->setValue( val.toDouble() );
    } else if (key == "ReferenceArea") {
      m_ui->sbRefArea->setValue( val.toDouble() );
    } else if (key == "ReferenceSpan") {
      m_ui->sbRefSpan->setValue( val.toDouble() );
    } else if (key == "ReferenceChord") {
      m_ui->sbRefChord->setValue( val.toDouble() );
    } else if (key == "ReferencePoint") {
      Vct3 rpt = cfg.getVct3(key);
      m_ui->sbRefX->setValue( rpt[0] );
      m_ui->sbRefY->setValue( rpt[1] );
      m_ui->sbRefZ->setValue( rpt[2] );
    } else if (key == "Simulation") {
      int nsim = simpos.size();
      for (int i=0; i<nsim; ++i) {
        if (itr->second == simpos[i]) {
          m_ui->cbSimulation->setCurrentIndex(i);
          break;
        }
      }
    } else if (key == "LicenseKey") {
      if (m_ui->leLicenseKey->text().isEmpty())
        m_ui->leLicenseKey->setText(val);
    }
  }
}

void CallDwfsDialog::buildConfig()
{
  cfg["Case"] = m_ui->leCase->text().toStdString();
  cfg["Simulation"] = simpos[ m_ui->cbSimulation->currentIndex() ];
  if (m_ui->rbMach->isChecked()) {
    cfg.erase("Speed");
    cfg["Mach"] = str(m_ui->sbMach->value());
  } else {
    cfg.erase("Mach");
    cfg["Speed"] = str(m_ui->sbVelocity->value());
  }

  // set alpha, beta
  cfg["Alpha"] = str(m_ui->sbAlpha->value());
  cfg["Beta"] = str(m_ui->sbBeta->value());

  // store reference data in mesh file for future use
  XmlElement xr("GeometricReference");

  Vct3 rpt;
  rpt[0] = m_ui->sbRefX->value();
  rpt[1] = m_ui->sbRefY->value();
  rpt[2] = m_ui->sbRefZ->value();
  xr["point"] = cfg["ReferencePoint"] = str(rpt);
  xr["area"] = cfg["ReferenceArea"] = str(m_ui->sbRefArea->value());
  xr["span"] = cfg["ReferenceSpan"] = str(m_ui->sbRefSpan->value());
  xr["chord"] = cfg["ReferenceChord"] = str(m_ui->sbRefChord->value());

  pmesh->annotate(xr);

  const QString & lkey = m_ui->leLicenseKey->text();
  if (not lkey.isEmpty()) {
    cfg["LicenseKey"] = lkey.toStdString();
    Scope::changeSetting("dwfs-license-key", lkey);
  }
}

bool CallDwfsDialog::locateSolver()
{
  // by default, search for dwfs in app folder
  QString defpath = QCoreApplication::applicationDirPath();
  execpath = Scope::setting("dwfs-executable-path", defpath + "/dwfs").value<QString>();

  // test if dwfs really is here
  QFileInfo info(execpath);
  bool exists = info.exists();
  bool isexec = info.isExecutable() and info.isFile();
  while ( (not exists) or (not isexec) ) {
    QString caption = tr("Locate dwfs executable");
    QFileDialog fd(this, caption);
    fd.setFileMode(QFileDialog::ExistingFile);
    fd.setDirectory(defpath);
    if (fd.exec() == QDialog::Accepted) {
      QStringList selected = fd.selectedFiles();
      if (not selected.empty())
        execpath = selected[0];
    } else {
      return false;
    }
    defpath = fd.directory().absolutePath();
    info = QFileInfo(execpath);
    exists = info.exists();
    isexec = info.isExecutable() and info.isFile();
  }

  // save for next time
  if (exists and isexec)
    Scope::changeSetting("dwfs-executable-path", execpath);

  return (exists and isexec);
}

void CallDwfsDialog::changeSolver()
{
  QString defpath = QCoreApplication::applicationDirPath();
  QString caption = tr("Locate dwfs executable");
  QFileDialog fd(this, caption);
  fd.setFileMode(QFileDialog::ExistingFile);
  fd.setDirectory(defpath);
  if (fd.exec() == QDialog::Accepted) {
    QStringList selected = fd.selectedFiles();
    if (not selected.empty())
      execpath = selected[0];
  }

  QFileInfo info(execpath);
  bool exists = info.exists();
  bool isexec = info.isExecutable() and info.isFile();

  if (exists and isexec)
    Scope::changeSetting("dwfs-executable-path", execpath);
}

QString CallDwfsDialog::workFile(const QString & f)
{
  QDir dir(workdir);
  return dir.toNativeSeparators(dir.path()) + dir.separator() + f;
}

void CallDwfsDialog::changeEvent(QEvent *e)
{
    QDialog::changeEvent(e);
    switch (e->type()) {
    case QEvent::LanguageChange:
        m_ui->retranslateUi(this);
        break;
    default:
        break;
    }
}
