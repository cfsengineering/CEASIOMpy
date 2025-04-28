
/* ------------------------------------------------------------------------
 * file:       dlgtetgen.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Interface to tetgen volume mesh generator
 * ------------------------------------------------------------------------ */

#include "dlgtetgen.h"
#include "assembly.h"
#include "sumo.h"
#include "util.h"
#include <surf/pentagrow.h>
#include <surf/tgrefiner.h>
#include <genua/ioglue.h>
#include <genua/timing.h>
#include "reportingpentagrow.h"
#include <QLocale>
#include <QComboBox>
#include <QFileDialog>
#include <QMessageBox>
#include <ctime>
#include <cstdlib>

using namespace std;

DlgTetgen::DlgTetgen(QWidget *parent)
  : QDialog(parent, Qt::Tool), m_tgproc(this), m_rstat(Inactive), m_tetgenPass(0)
{
  setupUi(this);
  retranslateUi(this);

  sbFirstHeight->setDecimals(3);
  sbFirstHeight->setValue( 1e-5 );
  sbMaxAbsHeight->setDecimals(3);
  sbMaxSteinerPoints->setMinimum(0);
  sbMaxSteinerPoints->setValue(0);
  sbMaxSteinerPoints->setSpecialValueText(tr("Unlimited"));

  connect( sbFarfieldLevel, SIGNAL(valueChanged(int)),
           this, SLOT(updateFarTriCount(int)) );
  connect( pbCallTetgen, SIGNAL(clicked()),
           this, SLOT(startGeneration()) );
  connect( pbInterrupt, SIGNAL(clicked()),
           this, SLOT(abortGeneration()) );
  connect( &m_tgproc, SIGNAL(readyRead()),
           this, SLOT(updateTetgenOutput()) );
  connect( &m_tgproc, SIGNAL(finished(int, QProcess::ExitStatus)),
           this, SLOT(finishGeneration(int, QProcess::ExitStatus)) );
  connect( pbLocateTetgen, SIGNAL(clicked()),
           this, SLOT(locateTetgen()) );
  
  // change value of maximum tet volume
  connect( sbFarfieldRadius, SIGNAL(valueChanged(double)),
           this, SLOT(updateTetVolume()) );
  connect( sbFarfieldLevel, SIGNAL(valueChanged(int)),
           this, SLOT(updateTetVolume()) );
  
  // nothing to save or interrupt
  pbInterrupt->setEnabled(false);

  // temporary directory - simply use current if default not ok
  m_tmpdirpath = QDir::tempPath() + '/';
  if (not QFileInfo(m_tmpdirpath).isDir())
    m_tmpdirpath = QDir::current().absolutePath() + '/';

  // set path from app setting
  m_tetgenpath = SumoMain::setting("tetgenpath", QString()).value<QString>();
}

void DlgTetgen::assign(AssemblyPtr pasy)
{
  m_asy = pasy;

  // on startup, estimate parameters
  m_asy->estimateTgParameters();
  sbFarfieldRadius->setValue( m_asy->tgFarfieldRadius() );
  sbTetQuality->setValue( m_asy->tgTetQuality() );

  updateFarTriCount(sbFarfieldLevel->value());
  updateTetVolume();
}

void DlgTetgen::startGeneration()
{
  // store settings used in this run
  m_asy->tgTetQuality( sbTetQuality->value() );
  m_asy->tgFarfieldRadius( sbFarfieldRadius->value() );

  // reset counter to zero
  lbNodeCount->setText("0");
  lbBndTriCount->setText("0");
  lbTetCount->setText("0");
  lbPentaCount->setText("0");

  m_mgclk.start();
  if ( cbGenerateLayers->isChecked() )
    startHybridGeneration();
  else
    startTetGeneration();

  tabWidget->setCurrentIndex(2);
}

void DlgTetgen::finishGeneration(int exitCode, QProcess::ExitStatus exitStatus)
{
  if (exitCode != 0 or exitStatus != QProcess::NormalExit) {
    pbCallTetgen->setEnabled(true);
    pbInterrupt->setEnabled(false);

    m_rstat = Inactive;
    printLog(tr("===== Mesh generation failed ===== "));
    return;
  }

  // this stub is called when tetgen finishes
  // in case a second pass is requested, call again
  if (cbSecondPass->isChecked() and m_tetgenPass < 2) {
    runSecondTetgenPass();
    return;
  }

  if (m_rstat == Hybrid)
    finishHybridGeneration(exitCode, exitStatus);
  else if (m_rstat == TetGen)
    finishTetGeneration(exitCode, exitStatus);

  pbCallTetgen->setEnabled(true);
  pbInterrupt->setEnabled(false);

  m_rstat = Inactive;
  printLog(tr("===== Mesh generation completed ===== "));
  updateMeshStats();

  int ms = m_mgclk.elapsed();
  qDebug("%d milliseconds.", ms);
  QTime tmg(0,0,0);
  lbMgenTime->setText(tmg.addMSecs(ms).toString("HH:mm:ss"));
}

void DlgTetgen::updateFarTriCount(int nref)
{
  int ntri = int( 20.0*pow(4.0, double(nref)) );
  lbFarfieldTriangles->setText( QString::number(ntri) );
}

void DlgTetgen::updateMeshStats()
{
  const MxMesh & mx( m_asy->mxMesh() );
  qulonglong ntri(0), ntet(0), npenta(0), nnodes(0);
  nnodes = mx.nnodes();

  for (uint i=0; i<mx.nsections(); ++i) {
    if ( mx.section(i).elementType() == Mx::Tri3 )
      ntri += mx.section(i).nelements();
    else if ( mx.section(i).elementType() == Mx::Tet4 )
      ntet += mx.section(i).nelements();
    else if ( mx.section(i).elementType() == Mx::Penta6 )
      npenta += mx.section(i).nelements();
  }

  QLocale loc;
  lbNodeCount->setText( loc.toString(nnodes) );
  lbBndTriCount->setText( loc.toString(ntri) );
  lbTetCount->setText( loc.toString(ntet) );
  lbPentaCount->setText( loc.toString(npenta) );
}

void DlgTetgen::updateTetgenOutput()
{
  QString s(m_tgproc.readAll());
  tbOutput->append(s);
  qApp->processEvents();
}

void DlgTetgen::updateTetVolume()
{
  Real fradius = sbFarfieldRadius->value();
  Real nref = sbFarfieldLevel->value();
  Real ntri = 20.*pow(4., nref);
  Real elen = sqrt( (16.*PI*sq(fradius) / (ntri*sqrt(3.)) ) );
  Real fvol = sqrt(2.)/12. * cb(elen);
  
  // increase volume a little to allow for
  // stretched triangles
  fvol *= 1.25;
  
  sbTetVolume->setValue(fvol);
  sbTetVolume->setMaximum(8*fvol);
  sbTetVolume->setMinimum(fvol/8.);
  sbTetVolume->setSingleStep(fvol/4.);
  sbTetVolume->setDecimals( max(0, int(3 - log10(fvol))) );
}

void DlgTetgen::startTetGeneration()
{
  m_rstat = TetGen;

  // let the user find the executable
  if (not QFileInfo(m_tetgenpath).isExecutable()) {
    if (not locateTetgen())
      return;
  }

  TetMesh & tvm( m_asy->volumeMesh() );
  
  fetchConfig();

  // create new file name
  tempFileName();
  
  try {
    
    tvm.clear();
    m_asy->initMeshBoundaries( sbFarfieldRadius->value(), sbFarfieldLevel->value() );
    
    // write smesh file to tmp directory
    tvm.writeSmesh( str((m_tmpfilebase + ".smesh")) );

  } catch (Error & xcp) {
    QString msg( QString::fromStdString(xcp.what()) );
    QMessageBox::warning(this, tr("Volume mesh generation failed."), msg);
    m_rstat = Inactive;
    return;
  }
  
  runFirstTetgenPass();
}

void DlgTetgen::runFirstTetgenPass()
{
  // assemble options string requires number-string conversion
  QLocale cloc(QLocale::English, QLocale::UnitedStates);
  cloc.setNumberOptions(QLocale::OmitGroupSeparator);

  // convert radius-to-edge ratio to number using current locale
  double r2e = sbTetQuality->value();
  int dihedral(0);
  if (cbMinDihedral->isChecked())
    dihedral = int( sbMinDihedral->value() );

  // and write to string using 'C' locale
  QString tgopt = "-pq" + cloc.toString(r2e, 'f', 3);
  if (dihedral > 0)
    tgopt += QString("q%1").arg(dihedral);
  if (cbVerbose->isChecked())
    tgopt += "V";
  if (not cbSplitBoundary->isChecked())
    tgopt += "Y";
  if (cbMaxVolume->isChecked()) {
    // qDebug() << "Volume text: " << sbTetVolume->text();
    tgopt += "a" + cloc.toString( sbTetVolume->value(), 'f');
  }

  quint64 maxSteiner = sbMaxSteinerPoints->value();
  if (maxSteiner > 0)
    tgopt += QString("S%1").arg(maxSteiner);

  QStringList args;
  args << tgopt << " " << (m_tmpfilebase + ".smesh");

  m_tetgenPass = 1;
  m_tgproc.setWorkingDirectory(m_tmpdirpath);
  m_tgproc.setReadChannel(QProcess::StandardOutput);
  QIODevice::OpenMode mode = QIODevice::ReadOnly |
                             QIODevice::Unbuffered |QIODevice::Text ;
  m_tgproc.start(m_tetgenpath, args, mode);

  // write something into output window
  QString msg = tr("First pass: <b>tetgen %1</b> started...").arg(tgopt);
  // tbOutput->clear();
  tbOutput->append(tr("Path: %1").arg(m_tetgenpath));
#ifndef NDEBUG
  tbOutput->append(tr("tmp dir: %1, file: %2").arg(m_tmpdirpath)
                   .arg(m_tmpfilebase + ".smesh"));
#endif
  tbOutput->append(msg);

  // disable start button
  pbCallTetgen->setEnabled(false);
  pbInterrupt->setEnabled(true);
}

void DlgTetgen::runSecondTetgenPass()
{
  writeMetricFile();

  QString tgopt = "-rqmY";
  if (cbVerbose->isChecked())
    tgopt += "V";

  quint64 maxSteiner = sbMaxSteinerPoints->value();
  if (maxSteiner > 0)
    tgopt += QString("S%1").arg(maxSteiner);

  QStringList args;
  args << tgopt << " " << (m_tmpfilebase + ".1");

  m_tetgenPass = 2;
  m_tgproc.setWorkingDirectory(m_tmpdirpath);
  m_tgproc.setReadChannel(QProcess::StandardOutput);
  QIODevice::OpenMode mode = QIODevice::ReadOnly |
                             QIODevice::Unbuffered |QIODevice::Text ;
  m_tgproc.start(m_tetgenpath, args, mode);

  // write something into output window
  QString msg = tr("Second pass: <b>tetgen %1 </b>started...").arg(tgopt);
#ifndef NDEBUG
  tbOutput->append(tr("tmp dir: %1, file: %2").arg(m_tmpdirpath)
                   .arg(m_tmpfilebase + ".1"));
#endif
  tbOutput->append(msg);

  // enable interrupt button
  pbInterrupt->setEnabled(true);
}

void DlgTetgen::writeMetricFile()
{
  Wallclock clk;

  clk.start();
  MxMesh tmsh;
  DVector<uint> ftags;
  tmsh.readTetgen( str(m_tmpfilebase + ".1."), &ftags);
  tbOutput->append(QString("[t] Reading first-pass background mesh"
                           ": %1s").arg(clk.stop()));

  TgRefiner tgr;
  tgr.configure( m_cfg );

  clk.start();
  tgr.edgeLengths(tmsh);
  tbOutput->append(QString("[t] Compute tet region"
                           " size field: %1s").arg(clk.stop()));

  tgr.writeMetricFile( str(m_tmpfilebase + ".1.mtr") );
}

void DlgTetgen::finishTetGeneration(int exitCode,
                                    QProcess::ExitStatus exitStatus)
{
  printLog(tr("Attempting to read tetgen results..."));
  TetMesh & tvm( m_asy->volumeMesh() );
  if (exitCode == 0 and exitStatus == QProcess::NormalExit) {
    try {
      
      string fname;
      if (m_tetgenPass == 1)
        fname = str(m_tmpfilebase + ".1");
      else
        fname = str(m_tmpfilebase + ".2");
      tvm.readTetgen(fname);
      updateMeshStats();
      
      // remove tmp files
      QFile(m_tmpfilebase + ".smesh").remove();
      QFile(m_tmpfilebase + ".1.node").remove();
      QFile(m_tmpfilebase + ".1.ele").remove();
      QFile(m_tmpfilebase + ".1.face").remove();
      if (m_tetgenPass == 2) {
        QFile(m_tmpfilebase + ".1.mtr").remove();
        QFile(m_tmpfilebase + ".2.node").remove();
        QFile(m_tmpfilebase + ".2.ele").remove();
        QFile(m_tmpfilebase + ".2.face").remove();
        QFile(m_tmpfilebase + ".2.mtr").remove();
      }
      
      QString msg = tr("<b>tetgen terminated normally.</b>");
      tbOutput->append(msg);
      
    }  catch (Error & xcp) {
      QString msg( QString::fromStdString(xcp.what()) );
      QMessageBox::warning(this, tr("Volume mesh generation failed."), msg);
    }
  } else {
    QString msg = tr("<b>tetgen terminated with error %1.</b>").arg(exitCode);
    tbOutput->append(msg);
  }
  
  // convert/transfer
  printLog(tr("Converting mesh format..."));
  MxMeshPtr pmx = boost::make_shared<MxMesh>();
  tvm.toMx(*pmx);
  m_asy->mxMesh(pmx);

  emit volumeMeshAvailable(tvm.nelements() > 5);
}

void DlgTetgen::abortGeneration()
{
  // kill process
  m_tgproc.kill();
  
  QString msg = tr("<b>tetgen process killed.</b>");
  tbOutput->append(msg);
  
  // enable start button again
  pbCallTetgen->setEnabled(true);
  pbInterrupt->setEnabled(false);
}

bool DlgTetgen::locateTetgen()
{
  // by default, search for tetgen in sumo's bin directory
  QString def_tgpath = QCoreApplication::applicationDirPath() + "/tetgen";
  m_tetgenpath = SumoMain::setting("tetgenpath",
                                 def_tgpath).value<QString>();

  QString caption = tr("Locate tetgen executable");

  // test if tetgen really is here
  bool exists = QFileInfo(m_tetgenpath).exists();
  bool isexec = QFileInfo(m_tetgenpath).isExecutable();
  do {

    QFileDialog fd(this, caption);
    fd.setFileMode(QFileDialog::ExistingFile);
    if ( QFileInfo(m_tetgenpath).absoluteDir().exists() )
      fd.setDirectory( QFileInfo(m_tetgenpath).absoluteDir() );
    else
      fd.setDirectory( QCoreApplication::applicationDirPath() );
    if (fd.exec() == QDialog::Accepted) {
      QStringList selected = fd.selectedFiles();
      if (not selected.empty())
        m_tetgenpath = selected[0];
    } else {
      return false;
    }
    exists = QFileInfo(m_tetgenpath).exists();
    isexec = QFileInfo(m_tetgenpath).isExecutable();

  } while ( (not exists) or (not isexec) );

  if (exists and isexec) {
    SumoMain::changeSetting("tetgenpath", m_tetgenpath);
    return true;
  } else {
    return false;
  }
}

void DlgTetgen::printLog(const QString &s)
{
  tbOutput->append(s);
  QApplication::processEvents();
}

void DlgTetgen::fetchConfig()
{
  m_cfg["InitialHeight"] = str(sbFirstHeight->value());
  m_cfg["MaxLayerThickness"] = str(sbMaxAbsHeight->value());
  m_cfg["MaxRelativeHeight"] = str(sbMaxRelHeight->value());
  m_cfg["NLayers"] = str(sbNumLayers->value());
  m_cfg["MaxGrowthRatio"] = str( sbGrowthRate->value() );
  m_cfg["UntangleGrid"] = "true";
  m_cfg["MaxOptimizationTime"] = str( sbOptimizationTime->value() );
  m_cfg["FeatureAngle"] = str( sbFeatureAngle->value() );
  m_cfg["SharpEdgeAngle"] = str( sbSharpAngle->value() );
  m_cfg["SplineNormals"] = cbCurvedGrowth->isChecked() ? "true" : "false";
  m_cfg["WallNormalTransition"] = str( sbWallTransition->value() );
  m_cfg["TetGrowthFactor"] = str( sbGrowthRate->value() );

  int nls = sbDistribRange->value();
  m_cfg["TetEdgeSmoothing"] = str( nls );
  m_cfg["TetEdgeDistrib"] = str( std::min(16, nls/4) );
}

const QString & DlgTetgen::tempFileName()
{
  srand( (uint) clock());
  m_tmpfilebase = m_tmpdirpath + "sumotvm" + QString::number(rand());
  return m_tmpfilebase;
}

void DlgTetgen::startHybridGeneration()
{
  m_rstat = Hybrid;

  // let the user find the executable
  if (not QFileInfo(m_tetgenpath).isExecutable()) {
    if (not locateTetgen())
      return;
  }

  uint nhiter = sbHeightIterations->value();
  uint nniter = sbNormalIterations->value();
  uint neiter = sbEnvelopeIterations->value();

  // establish file names
  const QString & baseName = tempFileName();

  fetchConfig();

  try {

    m_pgrow = boost::make_shared<ReportingPentaGrow>( m_asy->mesh() );
    connect( m_pgrow->reporter(), SIGNAL(logMessage(const QString&)),
             this, SLOT(printLog(const QString&)));
    printLog(tr("Generating envelope surface..."));
    m_pgrow->configure(m_cfg);
    m_pgrow->generateShell( nhiter, nniter, 256, neiter );

    //    // debug
    //    pgrow->writeShell( "outermost.zml" );

    // generate farfield, write boundary file for tetgen
    {
      TriMesh farf;
      Vct3 farfCenter = m_asy->mesh().volumeCenter();
      Real farfRadius = sbFarfieldRadius->value();
      uint farfRefine = sbFarfieldLevel->value();
      farf.sphere(farfCenter, farfRadius, farfRefine);
      int fartag = PentaGrow::maximumTagValue();
      qDebug("Tagged farfield with %d", fartag);
      farf.faceTag( fartag );
      farf.reverse();

      PointList<3> holeList;
      m_asy->mesh().findInternalPoints(holeList);

      string fname = str(baseName + ".smesh");
      printLog(tr("Writing .smesh file for tetgen: %1").arg(fname.c_str()));
      m_pgrow->writeTetgen(fname, farf, holeList);
    }

  } catch (Error &xcp) {
    QString msg( QString::fromStdString(xcp.what()) );
    QMessageBox::warning(this,
                         tr("Hybrid volume mesh generation failed."), msg);
  }

  // call tetgen to generate external tet mesh
  runFirstTetgenPass();
}

void DlgTetgen::finishHybridGeneration(int exitCode,
                                       QProcess::ExitStatus exitStatus)
{
  printLog(tr("Attempting to read tetgen results..."));
  if (exitCode != 0 or exitStatus != QProcess::NormalExit) {
    QString msg = tr("<b>tetgen terminated with error %1.</b>").arg(exitCode);
    tbOutput->append(msg);
    return;
  }

  bool curvedNormals = cbCurvedGrowth->isChecked();

  try {

    // reread tet mesh from tetgen results file
    string basename;
    if (m_tetgenPass == 1)
      basename = str(m_tmpfilebase+".1.");
    else
      basename = str(m_tmpfilebase+".2.");
    printLog(tr("[i] Reading tet mesh and adapting wall..."));
    m_pgrow->clear();
    m_pgrow->readTets(basename);
    if (curvedNormals)
      printLog(tr("[i] Extrusion with curved directions, c_t = %1")
               .arg(sbWallTransition->value()));
    else
      printLog(tr("[i] Extrusion with straight directions..."));
    m_pgrow->extrude(curvedNormals);

    // reduce memory footprint - do not call anything from PentaGrow interface
    // after this point (only inherited MxMesh member functions).
    m_pgrow->shrink();

    printLog(tr("Fusing mesh sections..."));
    size_t ndp = m_pgrow->mergeNodes(gmepsilon);
    printLog(tr("Merged %1 duplicate nodes").arg(ndp));

  } catch (Error &xcp) {
    QString msg( QString::fromStdString(xcp.what()) );
    QMessageBox::warning(this, tr("Volume mesh generation failed."), msg);
  }

  // pass mesh to Assembly
  m_asy->mxMesh( boost::dynamic_pointer_cast<MxMesh>(m_pgrow) );

  stringstream ss;
  size_t nneg = m_pgrow->countNegativeVolumes(ss);
  if (nneg > 0) {
    printLog( QString::fromStdString(ss.str()) );
    printLog(tr("%1 tangled elements detected.").arg(nneg));
  }

  emit volumeMeshAvailable( m_pgrow->nelements() > 5 );
}

