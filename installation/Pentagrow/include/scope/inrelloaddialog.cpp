
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
 
#include "inrelloaddialog.h"
#include "frfspec.h"
#include "ploaddialog.h"
#include "util.h"
#include <genua/xmlelement.h>
#include <genua/mxmesh.h>
#include <genua/csrmatrix.h>
#include <QFileDialog>
#include <QMessageBox>
#include <QFile>
#include <QTextStream>
#include <sstream>

using namespace std;

InrelLoadDialog::InrelLoadDialog(QWidget *parent)
  : QDialog(parent, Qt::Tool), cplDlg(0)
{
  setupUi(this);
  cbDefaultMapping->setChecked(true);

  // buttons
  connect(pbProceed, SIGNAL(clicked()), this, SLOT(proceed()));

  connect(pbLoadSettings, SIGNAL(clicked()),
          this, SLOT(loadSettings()));
  connect(pbStoreSettings, SIGNAL(clicked()),
          this, SLOT(storeSettings()));

  // files
  connect(lbStructuralMesh, SIGNAL(linkActivated(QString)),
          this, SLOT(browseNastranMesh()) );
  connect(lbStateHistory, SIGNAL(linkActivated(QString)),
          this, SLOT(browseStateFile()) );

  // input elements
  connect(sbStateIndex, SIGNAL(valueChanged(int)),
          this, SLOT(columnChanged(int)));
  connect(sbEigenmode, SIGNAL(editingFinished()),
          this, SLOT(updateMapping()));
  connect(cbExciteTag, SIGNAL(currentIndexChanged(int)),
          this, SLOT(updateMapping()));

  // disable input elements until files are loaded
  enableInput(false);

  // create child dialog
  cplDlg = new PLoadDialog(this);
  connect(cplDlg, SIGNAL(statusMessage(QString)),
          this, SIGNAL(statusMessage(QString)));
  connect(this, SIGNAL(rejected()), cplDlg, SLOT(reject()));
}

void InrelLoadDialog::enableInput(bool flag)
{
  sbStateIndex->setEnabled(flag);
  sbEigenmode->setEnabled(flag);
  cbExciteTag->setEnabled(flag);
}

void InrelLoadDialog::setStructuralMeshFile(const QString &fname)
{
  if (fname.isEmpty()) {
    strFileName.clear();
    lbStructuralMesh->setText( tr("<a href=\"#browseStateHistory\">"
                                "(click to browse) </a>") );
  } else {
    strFileName = fname;
    lbStructuralMesh->setText( QString("<a href=\"#browseStructuralMesh\">"
                                       " %1 </a>").arg(fname) );
  }
}

void InrelLoadDialog::setStateHistoryFile(const QString &fname)
{
  if (fname.isEmpty()) {
    stateFileName.clear();
    lbStateHistory->setText( tr("<a href=\"#browseStateHistory\">"
                                "(click to browse) </a>") );
  } else {
    stateFileName = fname;
    lbStateHistory->setText( QString("<a href=\"#browseStateHistory\">"
                                     " %1 </a>").arg(fname) );
  }
}

void InrelLoadDialog::assignFrf(MxMeshPtr pm)
{
  opm = FrqResponse;
  amesh = pm;
  if (not amesh)
    return;

  // identify excitation response pressure fields
  xcpFields.clear();
  xcpRedFreq.clear();
  xcpModeTag.clear();

  const string kkey = "k = ";
  const string mkey = "mode ";
  bool isRe(false), isIm(false);
  for (uint i=0; i<amesh->nfields(); ++i) {
    const MxMeshField & f( amesh->field(i) );
    if (not f.nodal())
      continue;
    if (f.ndimension() != 1)
      continue;
    if (not f.realField())
      continue;
    const string & fn = f.name();
    isRe = fn.find("Re(cp)") != string::npos;
    isIm = fn.find("Im(cp)") != string::npos;
    if (not (isRe or isIm))
      continue;

    string::size_type mpos, kpos = fn.find(kkey);
    if (kpos == string::npos)
      continue;
    Real k = Float( fn.substr(kpos + kkey.length()) );

    mpos = fn.find(mkey);
    if (mpos == string::npos)
      continue;
    string::size_type p1 = mpos + mkey.length();
    string::size_type n1 = kpos - p1;

    xcpFields.push_back(i);
    xcpRedFreq.push_back(k);
    xcpModeTag.push_back( Int(fn.substr(p1, n1)) );
  }

  xcpUniqueFreq = xcpRedFreq;
  sort_unique(xcpUniqueFreq);

  xcpUniqueTag = xcpModeTag;
  sort_unique(xcpUniqueTag);
  lbExcite->setText( QString::number(xcpUniqueTag.size()) );

  cbExciteTag->clear();
  if (xcpUniqueTag.empty())
    return;

  cbExciteTag->addItem("(unassigned)");
  for (uint i=0; i<xcpUniqueTag.size(); ++i)
    cbExciteTag->addItem( tr("Mode %1").arg(xcpUniqueTag[i]) );
  cbExciteTag->setCurrentIndex(0);

  lbStateFileIdentifier->setText( tr("Frequency reponse input") );
}

void InrelLoadDialog::assignTdl(MxMeshPtr pm)
{
  opm = TimeDomain;
  amesh = pm;
  if (not amesh)
    return;

  setStateHistoryFile( QString() );
  setStructuralMeshFile( QString() );
  gbReferenceValues->hide();

  // identify excitation response pressure fields
  xcpFields.clear();
  xcpRedFreq.clear();
  xcpModeTag.clear();

  for (uint i=0; i<amesh->nfields(); ++i) {
    const MxMeshField & f( amesh->field(i) );
    if (not f.nodal())
      continue;
    if (f.ndimension() != 1)
      continue;
    if (not f.realField())
      continue;
    if ( f.name().find("DeltaCp") == string::npos )
      continue;
    xcpFields.push_back(i);
  }
  cbExciteTag->clear();

  const uint nf = xcpFields.size();
  lbExcite->setText( QString::number(nf) );
  cbExciteTag->addItem("(unassigned)");
  for (uint i=0; i<nf; ++i)
    cbExciteTag->addItem( QString::fromStdString( amesh->field(xcpFields[i]).name() ) );
  cbExciteTag->setCurrentIndex(0);

  // extract reference dimensions from aerodynamic solution
  XmlElement::const_iterator rit;
  const XmlElement & note( amesh->note() );
  rit = note.findChild("Reference");
  if (rit == note.end()) {
    qDebug("No reference values found in flow solution.");
    tspec.refChord = tspec.refSpan = 1.0;
    tspec.refAlpha = tspec.refMach = 0.0;
  } else {
    tspec.refChord = rit->attr2float("chord", 1.0);
    tspec.refSpan = rit->attr2float("span", 1.0);
    tspec.refAlpha = rit->attr2float("alpha", 0.0);
    tspec.refMach = rit->attr2float("mach", 0.0);
  }

  lbStateFileIdentifier->setText( tr("State history file") );

  adjustSize();
}

struct MMNotePred
{
  bool operator() (const XmlElement & x){
    if (x.name() == "MassMatrix")
      return true;
    else
      return false;
  }
};

void InrelLoadDialog::browseNastranMesh()
{
  QString fn, filter, selfilter;
  filter = tr("MxMesh files (*.xml *.zml)");
  fn = QFileDialog::getOpenFileName(this, tr("Open structural mesh file"),
                                    lastdir, filter, &selfilter);
  if (fn.isEmpty())
    return;


  lastdir = QFileInfo(fn).absolutePath();
  setStructuralMeshFile( fn );
  loadNastran();
}

void InrelLoadDialog::loadNastran()
{
  const QString & fn = strFileName;
  if (fn.isEmpty())
    return;

  try {
    XmlElement xe;
    xe.read( str(fn) );
    smesh.reset( new MxMesh );
    smesh->fromXml(xe);
  } catch (Error & xcp) {
    QString title = tr("Aborted loading Nastran mesh.");
    QString xmsg = QString::fromStdString(xcp.what());
    QString text = tr("<b>Could not load %1</b><br><hr> %2").arg(fn).arg(xmsg);
    QMessageBox::information( this, title, text );
    setStructuralMeshFile( tr("(click to select file)") );
    smesh.reset();
    return;
  }

  // determine the number of eigenmodes
  iModeField.clear();
  for (uint i=0; i<smesh->nfields(); ++i) {
    if (smesh->field(i).valueClass() == MxMeshField::ValueClass::Eigenmode) {
      iModeField.push_back(i);
    }
  }

  // check if nastran mesh contains a mass matrix (required)
  QString msg = setupMZ();
  if (not msg.isEmpty()) {
    QString title = tr("Invalid file.");
    QString text = tr("Mesh loaded from file '%1' does not contain "
                      "a mass matrix. Please load another mesh.").arg(fn);
    text += tr("<br> Details: ") + msg;
    QMessageBox::information( this, title, text );
    setStructuralMeshFile(tr("(click to select file)"));
    smesh.reset();
    return;
  }

  if (nmodes() == 0) {
    QString title = tr("Invalid file.");
    QString text = tr("Mesh loaded from file '%1' does not contain "
                      "any eigenmodes. Please load another mesh.").arg(fn);
    QMessageBox::information( this, title, text );
    setStructuralMeshFile(tr("(click to select file)"));
    smesh.reset();
    return;
  }

  sbEigenmode->setMinimum(0);
  sbEigenmode->setMaximum(nmodes());
  sbEigenmode->setValue(0);
  lbEigenmodes->setText( QString::number(nmodes()) );

  // enable input elements if all data present
  enableInput( (freq.size() > 0) and (nmodes() > 0) and (xcpFields.size() > 0) );
}

QString InrelLoadDialog::setupMZ()
{
  if (not smesh)
    return tr("No structural mesh present.");
  if (iModeField.empty())
    return tr("No eigenmodes found in mesh.");

  // extract mass matrix
  CsrMatrix<Real> mgg;
  XmlElement::const_iterator itn, itm, nlast;
  nlast = smesh->noteEnd();
  for (itn = smesh->noteBegin(); itn != nlast; ++itn) {
    if (itn->name() == "MassMatrix") {
      itm = itn->findChild("CsrMatrix");
      if (itm == itn->end())
        return tr("Mass matrix not found in structural mesh.");
      mgg.fromXml(*itm);
    }
  }

  if (mgg.nrows() != 6*smesh->nnodes())
    return tr("Mass matrix embedded in mesh incompatible with "
              "mesh node count.");

  // compute M*Z
  const int nm = iModeField.size();
  const int ndof = mgg.nrows();
  mggz.resize(nm);
  Vector z(ndof);
  for (int i=0; i<nm; ++i) {
    mggz[i].resize( ndof );
    smesh->field(iModeField[i]).fetch(z);
    mgg.multiply(z, mggz[i]);
  }

  return QString();
}

void InrelLoadDialog::browseStateFile()
{
  QString fn;
  fn = QFileDialog::getOpenFileName(this, tr("Open state history file"),
                                    lastdir, tr("XML files (*.xml);;"
                                                "All files (*)"));
  if (fn.isEmpty())
    return;

  setStateHistoryFile(fn);
  if (opm == FrqResponse)
    parseFRF();
  else
    fetchFlightPath();
}

void InrelLoadDialog::parseFRF()
{
  const QString & fname = stateFileName;
  if (fname.isEmpty())
    return;

  // extract time steps and raw history
  freq.clear();
  frf.clear();

  Real f;
  Vector tmp;
  VectorArray raw;
  QString line;
  QFile file(fname);
  file.open( QIODevice::ReadOnly );
  QTextStream stream(&file);
  while (not stream.atEnd()) {
    line = stream.readLine();
    stringstream ss;
    ss.str( str(line) );
    if ( not (ss >> f) )
      continue;
    freq.push_back( f );
    tmp.clear();
    while (ss >> f)
      tmp.push_back( f );
    raw.push_back(tmp);
  }

  // convert to complex-valued matrix
  const int nfreq = freq.size();
  const int nstate = raw[0].size() / 2;
  frf.resize(nfreq, nstate);
  for (int i=0; i<nfreq; ++i) {
    for (int j=0; j<nstate; ++j)
      frf(i,j) = Complex( raw[i][2*j+0], raw[i][2*j+1] );
  }

  // initialize mappings
  eigenModes = Indices(nstate, 0);
  exciteTag.resize(nstate);

  // update GUI
  sbStateIndex->setEnabled( nstate > 0 );
  sbStateIndex->setMinimum(1);
  sbStateIndex->setMaximum( nstate );
  sbStateIndex->setValue(1);

  lbStates->setText( QString::number(frf.ncols()) );
  lbFrequencies->setText( QString::number(freq.size()) );
  enableInput( (freq.size() > 0) and (nmodes() > 0) and (xcpFields.size() > 0) );
}

void InrelLoadDialog::fetchFlightPath()
{
  const QString & fname =  stateFileName;
  if (fname.isEmpty())
    return;

  fpath.clear();
  try {
    XmlElement xe;
    xe.read( str(fname) );
    fpath.fromXml(xe);
  } catch (Error & xcp) {
    QString msg = tr("Cannot load flight path from %1; error message: %2")
                  .arg(fname).arg( QString::fromStdString(xcp.what()) );
    QMessageBox::warning(this, tr("Failed to load flight path."), msg);
    return;
  }

  const int nelast = fpath.elasticStates().size();
  const int naerc = fpath.controlStates().size();
  const int nxall = 5 + nelast + naerc;

  // initialize tspec, set flags etc
  fpath.initSpec(tspec);
  defaultMapping();

  // find reference state cp field
  tspec.irefcp = amesh->findField("CoefPressure");
  qDebug("Setting reference field to %d", tspec.irefcp);

  // update GUI
  sbStateIndex->setEnabled( nxall > 0 );
  sbStateIndex->setMinimum(1);
  sbStateIndex->setMaximum( nxall );
  sbStateIndex->setValue(1);
  qDebug("Found %d states.", nxall );

  lbStates->setText( QString::number(nxall) );
  lbFrequencies->setText( QString::number( fpath.niptime() ) );
  enableInput( true );
  columnChanged(0);
}

void InrelLoadDialog::defaultMapping()
{
  const int nelast = fpath.elasticStates().size();
  const int naerc = fpath.controlStates().size();
  const int nxall = 5 + nelast + naerc;

  uint modeCount(0), dcpCount(0);
  for (int i=0; i<nxall; ++i) {

    TdlState & state( tspec.states[i] );
    if (state.flag == TdlState::RigidBody) {
      state.imodefield = NotFound;
      state.idcpfield = xcpFields[dcpCount];
      ++dcpCount;
    } else if (state.flag == TdlState::Elastic) {
      state.imodefield = iModeField[modeCount];
      state.idcpfield = xcpFields[dcpCount];
      ++modeCount;
      ++dcpCount;
    } else if (state.flag == TdlState::AerodynControl) {
      state.imodefield = NotFound;
      state.idcpfield = xcpFields[dcpCount];
      ++dcpCount;
    }

  }

//  // initialize mappings
//  uint jmode(0), jexcite(0);
//  eigenModes.resize(nxall);
//  exciteTag.resize(nxall);
//  for (int i=0; i<nxall; ++i) {
//    if (tspec.states[i].flag == TdlState::RigidBody) {
//      eigenModes[i] = NotFound;
//      exciteTag[i] = xcpFields[i];
//      ++jexcite;
//      qDebug("Mapping rigid-body state %d to aerodynamic"
//             " field %s", i, amesh->field(exciteTag[i]).name().c_str());
//    } else if (tspec.states[i].flag == TdlState::Elastic) {
//      eigenModes[i] = iModeField[jmode];
//      exciteTag[i] = xcpFields[ 5 + jmode ];
//      ++jmode;
//      ++jexcite;
//      qDebug("Mapping elastic state %d to structural field %s and aerodynamic"
//             " field %s", i, smesh->field(eigenModes[i]).name().c_str(),
//             amesh->field(exciteTag[i]).name().c_str());
//    } else {
//      eigenModes[i] = NotFound;
//    }
//  }

//  // default mapping for aerodynamic control modes
//  for (int i=0; i<nxall; ++i) {
//    if (tspec.states[i].flag == TdlState::AerodynControl) {
//      eigenModes[i] = NotFound;
//      exciteTag[i] = xcpFields[ jexcite++ ];
//      qDebug("Mapping control state %d to aerodynamic"
//             " field %s", i, amesh->field(exciteTag[i]).name().c_str());
//    }
//  }

  columnChanged(0);
}

void InrelLoadDialog::columnChanged(int icol)
{
  if (xcpUniqueTag.empty() or eigenModes.empty())
    return;

  if (icol < 0 or uint(icol) > eigenModes.size())
    return;

  // stateIndex spin box shows columns as 1 to ncol
  uint istate = (icol - 1);

  // eigenmodes are indexed from 0 to nmodes()-1, but displayed
  // as 1 to nmodes, and QSpinBox is set to display 'unassigned' for 0
  uint ieig = eigenModes[istate];
  if (ieig == NotFound)
    sbEigenmode->setValue(0);
  else
    sbEigenmode->setValue(ieig+1);

  // same as above
  uint imt(NotFound);
  if (opm == FrqResponse)
    imt = sorted_index(xcpUniqueTag, exciteTag[istate]);
  else if (opm == TimeDomain)
    imt = sorted_index(xcpFields, exciteTag[istate]);

  if (imt == NotFound)
    cbExciteTag->setCurrentIndex(0);
  else
    cbExciteTag->setCurrentIndex(imt+1);
}

void InrelLoadDialog::updateMapping()
{
  if ( (opm == FrqResponse) and (xcpUniqueTag.empty() or eigenModes.empty()) )
    return;
  else if ( (opm == TimeDomain) and (xcpFields.empty() or eigenModes.empty()) )
    return;

  int icol = sbStateIndex->value();
  if (icol < 0 or uint(icol) > eigenModes.size())
    return;

  uint istate = icol - 1;

  int ieig = sbEigenmode->value();
  eigenModes[istate] = (ieig == 0) ? NotFound : ieig-1;

  int imt = cbExciteTag->currentIndex();
  if (imt == 0)
    exciteTag[istate] = NotFound;
  else if (opm == FrqResponse)
    exciteTag[istate] = xcpUniqueTag[imt-1];
  else if (opm == TimeDomain)
    exciteTag[istate] = xcpFields[imt-1];
}

void InrelLoadDialog::storeSettings()
{
  XmlElement xe("FRFSettings");
  xe["NastranMesh"] = str(strFileName);
  xe["StateFile"] =  str(stateFileName);
  xe["ReferenceChord"] = str( sbRefChord->value() );
  xe["ReferenceVelocity"] = str( sbRefVelocity->value() );
  xe["DynamicPressure"] = str( sbDynamicPressure->value() );

  if (not eigenModes.empty()) {
    XmlElement xf("EigenMode");
    xf["count"] = str(eigenModes.size());
    xf.asBinary(eigenModes.size(), &eigenModes[0]);
    xe.append(xf);
  }

  if (not exciteTag.empty()) {
    XmlElement xf("ExciteTag");
    xf["count"] = str(exciteTag.size());
    xf.asBinary(exciteTag.size(), &exciteTag[0]);
    xe.append(xf);
  }

  QString filter = tr("XML files (*.xml);;All files (*)");
  QString fn = QFileDialog::getSaveFileName(this, tr("Select settings file"),
                                            lastdir, filter);
  if (fn.isEmpty())
    return;

  lastdir = QFileInfo(fn).absolutePath();
  xe.write( str(fn), XmlElement::PlainText );
}

void InrelLoadDialog::loadSettings()
{
  QString filter = tr("XML files (*.xml);;All files (*)");
  QString fn = QFileDialog::getOpenFileName(this, tr("Select settings file"),
                                            lastdir, filter);

  if (fn.isEmpty())
    return;
  lastdir = QFileInfo(fn).absolutePath();

  XmlElement xe;
  xe.read( str(fn) );
  if (xe.name() != "FRFSettings" and
      xe.name() != "LoadReconstructionSettings")
    return;

  userSettings = xe;
  if (xe.hasAttribute("ReferenceVelocity"))
    sbRefVelocity->setValue(xe.attr2float("ReferenceVelocity", 1.0));
  if (xe.hasAttribute("ReferenceChord"))
    sbRefChord->setValue(xe.attr2float("ReferenceChord", 1.0));
  if (xe.hasAttribute("DynamicPressure"))
    sbDynamicPressure->setValue(xe.attr2float("DynamicPressure", 1.0));

  // load Nastran mesh
  if (xe.hasAttribute("NastranMesh")) {
    QString fname = QString::fromStdString(xe.attribute("NastranMesh"));
    if (QFileInfo(fname).exists()) {
      setStructuralMeshFile(fname);
      loadNastran();
    }
  }

  // load xi(f)
  if (xe.hasAttribute("StateFile")) {
    QString fname = QString::fromStdString(xe.attribute("StateFile"));
    if (QFileInfo(fname).exists()) {
      setStateHistoryFile(fname);
      if (opm == FrqResponse)
        parseFRF();
      else
        fetchFlightPath();
    }
  }

  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    if (itr->name() == "EigenMode") {
      uint n = Int( itr->attribute("count") );
      if (n == eigenModes.size())
        itr->fetch(n, &eigenModes[0]);
    } else if (itr->name() == "ExciteTag") {
      uint n = Int( itr->attribute("count") );
      if (n == exciteTag.size())
        itr->fetch(n, &exciteTag[0]);
    }
  }

  // force updating of GUI elements
  if (frf.ncols() > 0)
    sbStateIndex->setValue(1);
}

void InrelLoadDialog::proceed()
{
  if (opm == FrqResponse)
    proceedFrf();
  else if (opm == TimeDomain)
    proceedTdl();
}

void InrelLoadDialog::proceedFrf()
{
  // constants
  const Real b = 0.5 * sbRefChord->value();
  const Real uoo = sbRefVelocity->value();
  const Real qoo = sbDynamicPressure->value();

  // assemble subcases
  fspec = FRFSpec();
  fspec.amesh = amesh;
  fspec.smesh = smesh;
  fspec.modeMap = eigenModes;

  const int nf = freq.size();
  fspec.subcase.resize(nf);
  for (int i=0; i<nf; ++i) {
    FRFSubcase & sub( fspec.subcase[i] );
    sub.f = freq[i];
    Real omega = 2*M_PI*sub.f;
    Real rf = omega*b / uoo;

    // structural contribution omega^2 M Z xihat
    sub.finr.resize( 6*smesh->nnodes() );
    sub.fini.resize( 6*smesh->nnodes() );
    sub.fini = 0.0;
    sub.finr = 0.0;
    sub.cpFields.clear();
    sub.cpCoef.clear();

    // assemble contributions from states
    sub.xihat.allocate(frf.ncols());
    for (uint j=0; j<frf.ncols(); ++j) {

      Complex xij = frf(i,j);
      sub.xihat[j] = xij;
      uint jmode = eigenModes[j];
      if (jmode != NotFound) {
        axpby(sq(omega)*xij.real(), mggz[jmode], 1.0, sub.finr);
        axpby(sq(omega)*xij.imag(), mggz[jmode], 1.0, sub.fini);
      }

      // aerodynamic interpolation
      uint xct = exciteTag[j];
      if (xct == NotFound)
        continue;

      uint fi[2] = {0, 0};
      Real icf[2] = {0.0, 0.0};
      int ncf = linearCoefficients(xct, rf, fi, icf);

      // account for real and complex part
      for (int k=0; k<ncf; ++k) {
        if (fi[k] == NotFound or icf[k] == 0 or abs(xij) == 0)
          continue;
        uint fre = xcpFields[fi[k]+0];
        uint fim = xcpFields[fi[k]+1];
        sub.cpFields.push_back(fre);
        sub.cpFields.push_back(fim);

        // qoo multiplied into coef
        sub.cpCoef.push_back(qoo * icf[k] * xij);
        //        qDebug("ReField %d = '%s'\n ImField %d = '%s'\n coef %f, +i %f",
        //               fre, amesh->field(fre).name().c_str(),
        //               fim, amesh->field(fim).name().c_str(),
        //               real(sub.cpCoef.back()), imag(sub.cpCoef.back()));
      }
    }
  }

  cplDlg->meshFileName(  strFileName );
  cplDlg->assign(fspec);
  cplDlg->configure( userSettings );
  cplDlg->show();
}

void InrelLoadDialog::proceedTdl()
{
  // interpolate flight path, including time derivatives of all states,
  // for a subsampled vector of time values
  Vector ipt;
  fpath.resampledTime( sbNumSteps->value(), ipt );
  fpath.extractSpec( ipt, tspec );

  tspec.amesh = amesh;
  tspec.smesh = smesh;
  const int nstate = tspec.states.size();
  for (int j=0; j<nstate; ++j) {
    TdlState & state( tspec.states[j] );
    if ((state.flag == TdlState::Elastic) and (state.modeindex < mggz.size())) {
      state.mggz = mggz[ state.modeindex ];
    } else {
      state.mggz.clear();
    }
  }

  cplDlg->meshFileName( strFileName );
  cplDlg->assign(tspec);
  cplDlg->configure( userSettings );
  cplDlg->show();
}

uint InrelLoadDialog::linearCoefficients(uint k, Real rf,
                                         uint fi[], Real icf[]) const
{
  // frequency index
  uint jf = std::distance(xcpUniqueFreq.begin(),
                          std::lower_bound( xcpUniqueFreq.begin(),
                                            xcpUniqueFreq.end(), rf ));
  if (jf > 0)
    qDebug("k %f below %f above %f", rf, xcpUniqueFreq[jf-1], xcpUniqueFreq[jf]);

  // mode index
  uint jmode = std::distance( xcpUniqueTag.begin(),
                              std::lower_bound( xcpUniqueTag.begin(),
                                                xcpUniqueTag.end(), k ) );
  qDebug("mode %d below %d above %d", k, xcpUniqueTag[jmode], xcpUniqueTag[jmode+1]);

  // linearized index into grid of cp fields
  const uint nex = 2*xcpUniqueTag.size();
  uint jlo = nex * (jf - 1) + 2*jmode;
  uint jhi = nex * jf + 2*jmode;

  qDebug("Mode %d uses %d to %d (of %ld), jf = %d",
         k, jlo, jhi, xcpFields.size(), jf);

  //  if (jlo < xcpFields.size())
  //    qDebug("Field 0: '%s'", amesh->field(xcpFields[jlo+1]).name().c_str());
  //  if (jhi < xcpFields.size())
  //    qDebug("Field 1: '%s'", amesh->field(xcpFields[jhi+1]).name().c_str());

  // cut off beyond highest reduced frequency present in aerodynamic
  // data (no extrapolation)
  if (rf <= xcpUniqueFreq.front()) {
    fi[0] = jhi; // real part, im is +1
    icf[0] = 1.0;
    return 1;
  } else if (rf >= xcpUniqueFreq.back()) {
    fi[0] = jhi;
    icf[0] = 1.0;
    return 1;
  } else {
    Real flo = xcpUniqueFreq[jf-1];
    Real fhi = xcpUniqueFreq[jf];
    fi[0] = jlo; // real part, im is +1
    fi[1] = jhi;
    icf[1] = (rf - flo) / (fhi - flo);
    icf[0] = 1.0 - icf[1];
    return 2;
  }
}

void InrelLoadDialog::changeEvent(QEvent *e)
{
  QDialog::changeEvent(e);
  switch (e->type()) {
  case QEvent::LanguageChange:
    retranslateUi(this);
    break;
  default:
    break;
  }
}
