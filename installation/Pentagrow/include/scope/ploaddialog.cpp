
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
 
#include "ploaddialog.h"
#include "transformationdialog.h"
#include "util.h"
#include <surf/fsimesh.h>
#include <surf/nstmesh.h>
#include <genua/timing.h>
#include <genua/configparser.h>
#include <genua/ioglue.h>
#include <genua/mxsolutiontree.h>
#include <QFileDialog>
#include <QFileInfo>
#include <QMessageBox>
#include <QTextStream>
#include <QDebug>
#include <sstream>

using std::string;
using std::stringstream;

PLoadDialog::PLoadDialog(QWidget *parent) : QDialog(parent, Qt::Tool)
{
  setupUi(this);

  // wire up buttons
  connect(pbBrowseNastran, SIGNAL(clicked()), this, SLOT(browseNastranMesh()));
  connect(pbBrowseOutput, SIGNAL(clicked()), this, SLOT(browseOutputFile()));
  connect(pbRun, SIGNAL(clicked()), this, SLOT(mapLoads()));
  connect(pbStoreSettings, SIGNAL(clicked()), this, SLOT(storeSettings()));
  connect(pbLoadSettings, SIGNAL(clicked()), this, SLOT(loadSettings()));
  connect(pbRotation, SIGNAL(clicked()), this, SLOT(rotationDialog()));

  // changing mapping settings invalidates interpolator
  connect( cbInwardNormals, SIGNAL(clicked()), this, SLOT(flagDirty()) );
  connect( sbNormalTolerance, SIGNAL(editingFinished()),
           this, SLOT(flagDirty()) );
  connect( sbCatchRadius, SIGNAL(editingFinished()),
           this, SLOT(flagDirty()) );
  connect( rbAgglomerate, SIGNAL(toggled(bool)),
           this, SLOT(toggleAgglomeration(bool)) );

  // signal top-level view to change displayed mesh
  connect( cbDisplayStructure, SIGNAL(toggled(bool)),
           this, SLOT(displayStructure(bool)) );

  // hide UI because ViewManager doesn't presently handle this
  cbDisplayStructure->hide();
  pbRotation->hide();
  adjustSize();

  staticMultiCase = false;
}

void PLoadDialog::meshFileName(const QString & s)
{
  leNastranMesh->setText(s);
}

void PLoadDialog::assign(MxMeshPtr & am, const Indices & fields,
                         const Vector & coef, bool multiCase)
{
  staticMultiCase = multiCase;
  if (amesh.get() != am.get())
    flagDirty();
  amesh = am;
  cpFields = fields;
  pfCoef = coef;
  timeSteps.clear();
  coefHist.clear();
  freqList.clear();
  fspec.clear();

  gbTransient->hide();
  adjustSize();
}

void PLoadDialog::assign(MxMeshPtr &am, const Indices &fields,
                         const Vector &t, const VectorArray &xt)
{
  if (amesh.get() != am.get())
    flagDirty();
  amesh = am;
  cpFields = fields;
  pfCoef.clear();
  coefHist = xt;
  timeSteps = t;
  freqList.clear();
  fspec.clear();

  pbBrowseNastran->setEnabled(true);
  leNastranMesh->setEnabled(true);

  lbFStart->hide();
  sbFStart->hide();
  lbFEnd->hide();
  sbFEnd->hide();

  lbNSolSteps->setText(tr("Number of time steps"));

  lbSkipSteps->show();
  sbSkipSteps->show();

  sbNSolSteps->setValue( t.size() );
  sbSkipSteps->setMaximum( t.size() );

  gbTransient->setTitle(tr("Direct Transient Analysis"));
  gbTransient->show();
  adjustSize();
}

void PLoadDialog::harmonic(MxMeshPtr & am, const Indices & fields,
                           const Vector & freq)
{
  if (amesh.get() != am.get())
    flagDirty();
  amesh = am;
  cpFields = fields;
  pfCoef.clear();
  timeSteps.clear();
  coefHist.clear();
  freqList = freq;
  fspec.clear();
  assert(fields.size() == 2*freqList.size());

  pbBrowseNastran->setEnabled(true);
  leNastranMesh->setEnabled(true);

  lbFStart->show();
  sbFStart->show();
  lbFEnd->show();
  sbFEnd->show();

  lbSkipSteps->hide();
  sbSkipSteps->hide();

  lbNSolSteps->setText(tr("Number of frequencies"));

  // set default values for the set of frequencies at which
  // direct response solutions are to be performed (number of factorizations)
  sbFStart->setValue( freqList.front() );
  sbFEnd->setValue( freqList.back() );
  sbNSolSteps->setValue( 2*freqList.size() );

  gbTransient->setTitle(tr("Frequency Response Analysis"));
  gbTransient->show();
  adjustSize();
}

void PLoadDialog::assign(const FRFSpec & s)
{
  tspec.clear();
  fspec = s;
  amesh = s.amesh;
  smesh = s.smesh;

  initStructure();

  pbBrowseNastran->setEnabled(false);
  leNastranMesh->setEnabled(false);

  // no further options required
  gbTransient->hide();
  adjustSize();
}

void PLoadDialog::assign(const TdlSpec & s)
{
  fspec.clear();
  tspec = s;
  amesh = s.amesh;
  smesh = s.smesh;

  initStructure();

  // pbBrowseNastran->setEnabled(false);
  // leNastranMesh->setEnabled(false);
  lbNastranMesh->hide();
  leNastranMesh->hide();
  pbBrowseNastran->hide();

  // no further options required
  gbTransient->hide();
  adjustSize();
}

void PLoadDialog::toggleAgglomeration(bool flag)
{
  if (flag) {
    lbNormalTolerance->hide();
    sbNormalTolerance->hide();
    lbCatchRadius->hide();
    sbCatchRadius->hide();
    cbInwardNormals->hide();
  } else {
    lbNormalTolerance->show();
    sbNormalTolerance->show();
    lbCatchRadius->show();
    sbCatchRadius->show();
    cbInwardNormals->show();
  }
  adjustSize();
}

void PLoadDialog::flagDirty()
{
  pfsi.reset();
}

void PLoadDialog::browseNastranMesh()
{
  cbDisplayStructure->setEnabled(false);
  cbDisplayStructure->setChecked(false);

  QString fn, filter, selected;
  filter = tr("ZML files (*.zml);;"
              "NASTRAN bulk data (*.blk *.bdf *.dat *.f06)");
  fn = QFileDialog::getOpenFileName(this, tr("Open structural mesh file"),
                                    lastdir, filter, &selected);
  if (fn.isEmpty())
    return;
  lastdir = QFileInfo(fn).absolutePath();

  leNastranMesh->setText( fn );
  bool ok = loadNastran();
  if (not ok) {
    leNastranMesh->setText("");
    return;
  }

  initStructure();

  if (cbDisplayStructure->isChecked())
    emit displayMesh( smesh );
}

bool PLoadDialog::loadNastran()
{
  const QString & fn = leNastranMesh->text();
  if (fn.isEmpty())
    return false;

  try {
    QApplication::setOverrideCursor(Qt::WaitCursor);
    smesh.reset();
    if (fn.toUpper().contains(".ZML")) {
      XmlElement xe;
      xe.read( str(fn) );
      smesh.reset( new MxMesh() );
      smesh->fromXml( xe );
    } else {
      NstMesh nsm;
      nsm.nstread( str(fn) );
      smesh.reset( new MxMesh() );
      nsm.toMx(*smesh);
    }
  } catch (Error & xcp) {
    QApplication::restoreOverrideCursor();
    QString title = tr("Loading aborted.");
    QString xmsg = QString::fromStdString(xcp.what());
    QString text = tr("<b>Could not load %1</b><br><hr> %2").arg(fn).arg(xmsg);
    QMessageBox::information( this, title, text );
    return false;
  }

  QApplication::restoreOverrideCursor();
  return true;
}

void PLoadDialog::initStructure()
{
  if (not smesh)
    return;

  // determine whether structural mesh has shell elements at all
  bool hasShells(false);
  for (uint j=0; j<smesh->nsections(); ++j)
    hasShells |= smesh->section(j).surfaceElements();

  if (hasShells) {
    rbIntegrate->setEnabled(true);
    rbIntegrate->setChecked(true);
  } else {
    rbAgglomerate->setChecked(true);
    rbIntegrate->setEnabled(false);
  }

  // allow switching mesh display
  cbDisplayStructure->setEnabled(true);

  // invalidate interpolator (new structural mesh)
  flagDirty();
}

void PLoadDialog::browseOutputFile()
{
  QString fn, filter, selected;
  filter = tr("All files (*)");
  fn = QFileDialog::getSaveFileName(this, tr("Select output bulk data file"),
                                    lastdir, filter, &selected);
  if (fn.isEmpty())
    return;
  lastdir = QFileInfo(fn).absolutePath();
  leOutputFile->setText(fn);
}

void PLoadDialog::buildInterpolator()
{
  inclPID.clear();
  if (rbInclude->isChecked()) {
    int pid;
    stringstream ss;
    ss.str( str(leIncludePID->text()) );
    while (ss >> pid)
      inclPID.push_back(pid);
  }
  sort_unique(inclPID);

  exclPID.clear();
  if (rbExclude->isChecked()) {
    int pid;
    stringstream ss;
    ss.str( str(leExcludePID->text()) );
    while (ss >> pid)
      exclPID.push_back(pid);
  }
  sort_unique(exclPID);

  pfsi.reset(new FsiMesh);
  if (cbInwardNormals->isChecked()) {
    pfsi->minNormalAngle( M_PI - rad(sbNormalTolerance->value()) );
    pfsi->maxNormalAngle( M_PI );
  } else {
    pfsi->minNormalAngle( 0.0 );
    pfsi->maxNormalAngle( rad(sbNormalTolerance->value()) );
  }
  pfsi->catchRadius( sbCatchRadius->value() );
  pfsi->mergeFluid(amesh);
  pfsi->mergeStruct(smesh, inclPID, exclPID);
  pfsi->buildInterpolator();

  // debug
  qDebug("Using %zu structural elements.",
         pfsi->structuralElements().size());
  qDebug("Using %zu aerodynamic elements.",
         pfsi->fluidElements().size());
}

void PLoadDialog::mapLoads()
{
  try {
    qDebug("Mapping loads...");
    if (isTransient())
      mapTransientLoads();
    else if (isHarmonic())
      mapHarmonicLoads();
    else if (not fspec.empty())
      mapFRFLoads();
    else if (not tspec.empty())
      mapTdlLoads();
    else if (staticMultiCase)
      mapMultiStaticLoads();
    else
      mapStaticLoads();
  } catch (Error & xcp) {
    QApplication::restoreOverrideCursor();
    QString title = tr("Load mapping aborted.");
    QString xmsg = QString::fromStdString(xcp.what());
    QString text = tr("Load mapping failed with error:"
                      "<br><hr> %1").arg(xmsg);
    QMessageBox::information( this, title, text );
  }

  if (cbStoreVisuMesh->isChecked()) {
    QString fn = QFileDialog::getSaveFileName(this,
                                              tr("Save load visualization mesh"),
                                              lastdir );
    if (not fn.isEmpty()) {
      smesh->writeAs(str(fn), Mx::NativeFormat, 1);
    }
  }
}

void PLoadDialog::mapStaticLoads()
{
  if (not amesh)
    return;
  if (not smesh)
    return;

  // write to nastran file
  string outfile = str(leOutputFile->text());
  if (outfile.empty()) {
    browseOutputFile();
    if (outfile.empty())
      return;
  }

  QApplication::setOverrideCursor(Qt::WaitCursor);

  Wallclock clck;
  clck.start();
  buildInterpolator();
  clck.stop();

  qDebug("Tree/map construction: %f", clck.elapsed());

  // assemble pressure vector
  Vector pf;
  pfsi->assemblePressure(1.0, cpFields, pfCoef, pf);

  // integrate over structural elements to obtain nodal forces
  PointList<6> fnod;
  clck.start();
  if (rbIntegrate->isChecked())
    pfsi->integrate(pf, fnod);
  else
    pfsi->agglomerate(pf, fnod);
  clck.stop();

  qDebug("Pressure integration: %d nodes, %f sec", fnod.size(), clck.elapsed());

  // write nodal forces and moments
  Real fscale = sbScaleForce->value();
  Real lscale = sbScaleLength->value();
  int sid = sbLoadSet->value();
  pfsi->exportForces(fnod, outfile, sid, fscale, lscale);

  // store forces in structural mesh for visualization
  string csn = str(leCaseName->text());
  pfsi->appendSifField(fnod, csn);

  // post updated structural mesh
  if (cbDisplayStructure->isChecked())
    emit displayMesh( smesh );

  QApplication::restoreOverrideCursor();
  pgProgress->setValue( pgProgress->maximum() );
}

void PLoadDialog::mapMultiStaticLoads()
{
  if (not amesh)
    return;
  if (not smesh)
    return;

  // write to nastran file
  string outfile = str(leOutputFile->text());
  if (outfile.empty()) {
    browseOutputFile();
    if (outfile.empty())
      return;
  }

  QApplication::setOverrideCursor(Qt::WaitCursor);

  buildInterpolator();

  Real fscale = sbScaleForce->value();
  Real lscale = sbScaleLength->value();

  // loop over fields
  Indices kfields(1);
  Vector kcoef(1);

  // SID for the first load case
  PointList<6> fnod;
  int sid = sbLoadSet->value();

  // apppend bulk data to stream; write include file
  ofstream outs(outfile);
  ofstream incs(outfile+".inc");

  MxSolutionTreePtr stree = amesh->solutionTree();

  const size_t ncase = cpFields.size();
  for (size_t icase=0; icase<ncase; ++icase) {

    // assemble pressure vector
    Vector pf;
    kfields[0] = cpFields[icase];
    kcoef[0] = pfCoef[icase];
    pfsi->assemblePressure(1.0, kfields, kcoef, pf);

    // integrate over structural elements to obtain nodal forces
    if (rbIntegrate->isChecked())
      pfsi->integrate(pf, fnod);
    else
      pfsi->agglomerate(pf, fnod);

    // append to stream
    pfsi->exportForces(fnod, outs, sid, fscale, lscale);

    // store forces in structural mesh for visualization
    pfsi->appendSifField(fnod, "Loadset SID "+str(sid));

    incs << "$" << endl;
    incs << "SUBCASE=" << sid << endl;
    incs << "LOAD=" << sid << endl;

    // generate a casename if possible
    string casename = "LOADCASE_"+str(sid);
    if (stree != nullptr) {
      MxSolutionTreePtr ptr = stree->findFirstWith(cpFields[icase]);
      if (ptr != nullptr)
        casename = ptr->name();
    }
    incs << "LABEL=" << casename << endl;

    ++sid;
  }

  // post updated structural mesh
  if (cbDisplayStructure->isChecked())
    emit displayMesh( smesh );

  QApplication::restoreOverrideCursor();
}

void PLoadDialog::mapTransientLoads()
{
  if (not amesh)
    return;
  if (not smesh)
    return;

  // fetch nastran load file name
  string outfile = str(leOutputFile->text());
  if (outfile.empty()) {
    browseOutputFile();
    if (outfile.empty())
      return;
  }

  // stream for transient loads
  ofstream tos(asPath(outfile).c_str());
  int sid = sbLoadSet->value();
  int nstep = sbNSolSteps->value();
  int nskip = sbSkipSteps->value();
  Real dt = (timeSteps.back() - timeSteps.front()) / nstep;
  tos << "TSTEP, 1, " << nstep << ", " << nstr(dt) << ", " << nskip << endl;
  tos << "DLOAD, " << sbLoadSet->value() << ", 1.0";
  const int nf = cpFields.size();
  for (int i=0; i<std::min(3,nf); ++i)
    tos << ", 1.0, " << sid+i;
  for (int i=3; i<nf; ++i) {
    if ( (i-3)%4 == 0 )
      tos << ", ";
    tos << "1.0, " << sid+i << ", ";
    if ( (i-3)%4 == 3 or i == nf-1)
      tos << endl;
  }

  QApplication::setOverrideCursor(Qt::WaitCursor);

  Wallclock clck;
  clck.start();
  buildInterpolator();
  clck.stop();

  qDebug("Tree/map construction: %f", clck.elapsed());

  // scaling coefficients
  Real fscale = sbScaleForce->value();
  Real lscale = sbScaleLength->value();

  // generate spatial load distribution entries for each cp field
  for (int i=0; i<nf; ++i) {
    Vector pf; // (amesh->field(cpFields[i]).realPointer(), amesh->nnodes());
    amesh->field(cpFields[i]).fetch(pf);
    PointList<6> fnod;
    clck.start();
    if (rbIntegrate->isChecked())
      pfsi->integrate(pf, fnod);
    else
      pfsi->agglomerate(pf, fnod);
    clck.stop();

    qDebug("Pressure integration: %f", clck.elapsed());

    int tload_sid = sid+i;
    int darea_sid = 100+tload_sid;
    int table_sid = 200+tload_sid;

    tos << "TLOAD1, " << tload_sid             // TLOAD SID
        << ", " << darea_sid             // EXCITEID -> DAREA SID
        << ", 0, LOAD, " << table_sid    // TABLE1D SID
        << endl;
    // rt180.transformList6D( fni );
    pfsi->exportDarea(darea_sid, fnod, tos, fscale, lscale);
    writeTable(table_sid, i, tos);

    // store forces in structural mesh for visualization
    string csn = "Projected: " + amesh->field(cpFields[i]).name();
    pfsi->appendSifField(fnod, csn);
  }

  // post updated structural mesh
  if (cbDisplayStructure->isChecked())
    emit displayMesh( smesh );

  QApplication::restoreOverrideCursor();
}

void PLoadDialog::writeTable(int tid, int jcol, std::ostream &os) const
{
#undef NZNSTR
#define NZNSTR(x)  nstr( (fabs((x)) > 1e-9) ? (x) : 0.0 )

  os << "TABLED1, " << tid << ", LINEAR, LINEAR" << endl << ", ";
  const int npoints = timeSteps.size();
  for (int i=0; i<npoints; ++i) {
    os << nstr(timeSteps[i]) << ", " << NZNSTR(coefHist[i][jcol]) << ", ";
    if ((i+1)%4 == 0)
      os << endl << ", ";
  }
  os << "ENDT" << endl;

#undef NZNSTR
}

void PLoadDialog::mapHarmonicLoads()
{
  qDebug("Frequency response, %u frequencies", (uint) freqList.size());
  if (not amesh)
    return;
  if (not smesh)
    return;

  // fetch nastran load file name
  string outfile = str(leOutputFile->text());
  if (outfile.empty()) {
    browseOutputFile();
    if (outfile.empty())
      return;
  }

  // DLOAD entry which specifies how to combine the RLOAD1 cards below
  ofstream tos(asPath(outfile).c_str());
  int sid = sbLoadSet->value();

  // header for information only
  const QString & subCase = leCaseName->text();
  if (not subCase.isEmpty()) {
    tos << '$' << endl << "$ " << str(subCase)
        << endl << '$' << endl;
  }

  // list of frequencies to analyse -- this entry must be referenced
  // by a FREQUENCY case control command
  uint ndf = sbNSolSteps->value();
  Real df = (sbFEnd->value() - sbFStart->value()) / ndf;
  tos << "FREQ1, " << sid
      << ", " << nstr(sbFStart->value())
      << ", " << nstr(df)
      << ", " << ndf << endl;

  QApplication::setOverrideCursor(Qt::WaitCursor);

  Wallclock clck;
  clck.start();
  buildInterpolator();
  clck.stop();

  qDebug("Tree/map construction: %f", clck.elapsed());

  // scaling coefficients
  Real fscale = sbScaleForce->value();
  Real lscale = sbScaleLength->value();

  // generate two spatial load distribution entries for each frequency
  Indices rload_sids;
  const int nf = freqList.size();
  for (int i=0; i<nf; ++i) {

    // post status
    emit statusMessage(
          tr("Mapping loads for frequency %1 Hz").arg(freqList[i]));

    uint rfi = cpFields[2*i+0];  // real field
    uint ifi = cpFields[2*i+1];  // imaginary field

    Vector pfr, pfi;
    PointList<6> fnodr, fnodi;
    clck.start();
    pfsi->extractPressure(1.0, rfi, pfr);

    if (rbIntegrate->isChecked())
      pfsi->integrate(pfr, fnodr);
    else
      pfsi->agglomerate(pfr, fnodr);

    pfsi->extractPressure(1.0, ifi, pfi);
    if (rbIntegrate->isChecked())
      pfsi->integrate(pfi, fnodi);
    else
      pfsi->agglomerate(pfi, fnodi);
    clck.stop();

    fmTrafo.transformList6D( fnodr );
    fmTrafo.transformList6D( fnodi );

    qDebug("Mapping Re field: %d named %s", rfi, amesh->field(rfi).name().c_str());
    qDebug("Mapping Im field: %d named %s", ifi, amesh->field(ifi).name().c_str());
    Vct6 fr = pfsi->sum(vct(0,0,0), fnodr);
    qDebug("Sum of nodal forces Re: %f %f %f", fr[0], fr[1], fr[2]);
    Vct6 fi = pfsi->sum(vct(0,0,0), fnodi);
    qDebug("Sum of nodal forces Im: %f %f %f", fi[0], fi[1], fi[2]);

    // timing
    qDebug("Pressure integration: %f", clck.elapsed());

    int rload_sid = 1+sid+2*i;
    int rdarea_sid = 100+sid+2*i+0;
    int idarea_sid = 100+sid+2*i+1;
    int table_sid = 200+rload_sid;

    // print hat function table for this frequency
    writeHatFunction(table_sid, i, tos);

    // number of DAREA rows written
    uint nout = 0;

    // real part
    tos << '$' << endl << "$ " << amesh->field(rfi).name()
        << endl << '$' << endl;
    nout = pfsi->exportDarea(rdarea_sid, fnodr, tos, fscale, lscale);
    if (nout > 0) {
      tos << "RLOAD1, " << rload_sid       // TLOAD SID
          << ", " << rdarea_sid            // EXCITEID -> DAREA SID
          << ", 0, 0, "                    // DELAY, DPHASE, TABLE TC
          << table_sid << ", 0"            // TABLE TC (real), TD (imag)
          << endl;
      rload_sids.push_back(rload_sid);
    }

    // imaginary part
    tos << '$' << endl << "$ " << amesh->field(ifi).name()
        << endl << '$' << endl;
    nout = pfsi->exportDarea(idarea_sid, fnodi, tos, fscale, lscale);
    if (nout > 0) {
      tos << "RLOAD1, " << rload_sid+1       // TLOAD SID
          << ", " << idarea_sid            // EXCITEID -> DAREA SID
          << ", 0, 0, "                    // DELAY, DPHASE, TABLE TC
          << "0, " << table_sid            // TABLE TC (real), TD (imag)
          << endl;
      rload_sids.push_back(rload_sid+1);
    }

    // store forces in structural mesh for visualization
    string csn = "Projected: " + amesh->field(rfi).name();
    pfsi->appendSifField(fnodr, csn);
    csn = "Projected: " + amesh->field(ifi).name();
    pfsi->appendSifField(fnodi, csn);
  }

  // DLOAD entry which combines the RLOAD1 entries above into a
  // single loadset which must be referenced by a DLOAD case control command
  // DLOAD set ID must differ from RLOAD SIDs
  tos << "DLOAD, " << sid << ", 1.0";
  const int nrl = rload_sids.size();
  for (int i=0; i<std::min(3,nrl); ++i)
    tos << ", 1.0, " << rload_sids[i];
  tos << endl;
  for (int i=3; i<nrl; ++i) {
    if ( (i-3)%4 == 0 )
      tos << ", ";
    tos << "1.0, " << rload_sids[i] << ", ";
    if ( (i-3)%4 == 3 or i == nrl-1)
      tos << endl;
  }

  // post updated structural mesh
  if (cbDisplayStructure->isChecked())
    emit displayMesh( smesh );

  QApplication::restoreOverrideCursor();
}

void PLoadDialog::writeHatFunction(int tid, int jcol, std::ostream &os) const
{
  os << "TABLED1, " << tid << ", LINEAR, LINEAR" << endl << ", ";
  const int npoints = freqList.size();
  for (int i=0; i<npoints; ++i) {
    Real c = (i == jcol) ? 1.0 : 0.0;
    os << nstr(freqList[i]) << ", " << nstr(c) << ", ";
    if ((i+1)%4 == 0)
      os << endl << ", ";
  }
  os << "ENDT" << endl;
}

void PLoadDialog::mapFRFLoads()
{
  if (fspec.subcase.empty())
    return;
  if ( (not smesh) or (not amesh) )
    return;

  // fetch nastran load file name
  string outfile = str(leOutputFile->text());
  if (outfile.empty()) {
    browseOutputFile();
    outfile = str(leOutputFile->text());
    if (outfile.empty())
      return;
  }
  ofstream os(asPath(outfile).c_str());

  // stream for case control statements
  string casefile = append_suffix(outfile, ".case");
  ofstream ocase(asPath(casefile).c_str());

  QApplication::setOverrideCursor(Qt::WaitCursor);

  Wallclock clck;
  clck.start();
  buildInterpolator();
  clck.stop();

  qDebug("Tree/map construction: %f", clck.elapsed());

  // scaling coefficients
  Real fscale = sbScaleForce->value();
  Real lscale = sbScaleLength->value();
  uint sid = sbLoadSet->value();

  // two subcases for each i, one real, one imag load vector
  Vector pfr, pfi, fcpReal, fcpImag;
  PointList<6> fnodr, fnodi, gfr(smesh->nnodes()), gfi(smesh->nnodes());

  // structural interface node subset
  const Indices & sifNodes( pfsi->structuralNodes() );
  const int nsif = sifNodes.size();

  clck.start();
  const int nsub = fspec.subcase.size();
  for (int i=0; i<nsub; ++i) {
    const FRFSubcase & sub( fspec.subcase[i] );

    qDebug("Processing subcase %d of %d at %f Hz", i, nsub, sub.f);
    emit statusMessage(tr("Processing subcase %1 of %2").arg(i).arg(nsub));

    const int ncoef = sub.cpCoef.size();
    assert(sub.cpFields.size() == (uint) 2*ncoef);
    fcpReal.resize(2*ncoef);
    fcpImag.resize(2*ncoef);
    for (int j=0; j<ncoef; ++j) {
      Real cr = sub.cpCoef[j].real();
      Real ci = sub.cpCoef[j].imag();

      fcpReal[2*j+0] = +cr;
      fcpReal[2*j+1] = -ci;
      fcpImag[2*j+0] = +ci;
      fcpImag[2*j+1] = +cr;
    }

    // construct real and imag pressure vectors
    pfsi->assemblePressure(1.0, sub.cpFields, fcpReal, pfr);
    pfsi->assemblePressure(1.0, sub.cpFields, fcpImag, pfi);

    // map to structural mesh
    if (rbIntegrate->isChecked()) {
      pfsi->integrate(pfr, fnodr);
      pfsi->integrate(pfi, fnodi);
    } else {
      pfsi->agglomerate(pfr, fnodr);
      pfsi->agglomerate(pfi, fnodi);
    }

    // apply transformation
    fmTrafo.transformList6D( fnodr );
    fmTrafo.transformList6D( fnodi );

    // scale aerodynamic forces/moments only, since structural
    // contributions are already in the appropriate units
    const int nfn = fnodr.size();
    //#pragma omp parallel for
    for (int j=0; j<nfn; ++j) {
      for (int k=0; k<3; ++k)
        fnodr[j][k] *= fscale;
      for (int k=3; k<6; ++k)
        fnodr[j][k] *= fscale*lscale;
      for (int k=0; k<3; ++k)
        fnodi[j][k] *= fscale;
      for (int k=3; k<6; ++k)
        fnodi[j][k] *= fscale*lscale;
    }

    // inertial loads
    std::copy(sub.finr.begin(), sub.finr.end(), gfr.pointer());
    std::copy(sub.fini.begin(), sub.fini.end(), gfi.pointer());

    // extend to full problem (all structural nodes)
    assert(fnodr.size() == sifNodes.size());
    //#pragma omp parallel for
    for (int j=0; j<nsif; ++j) {
      gfr[sifNodes[j]] += fnodr[j];
      gfi[sifNodes[j]] += fnodi[j];
    }

    // write out loadset
    pfsi->exportForces(gfr, os, sid, 1.0, 1.0);
    pfsi->exportForces(gfi, os, sid+1, 1.0, 1.0);

    // case control commands
    ocase << "$ Frequency " << sub.f << " Hz, real part" << endl;
    ocase << "SUBCASE = " << sid << endl;
    ocase << "  LOAD = " << sid << endl;
    ocase << "$ Frequency " << sub.f << " Hz, imag part" << endl;
    ocase << "SUBCASE = " << sid+1 << endl;
    ocase << "  LOAD = " << sid+1 << endl;

    // store aerodynamcic forces in structural mesh for visualization
    pfsi->appendSifField(fnodr, "Loadset: " + str(sid));
    pfsi->appendSifField(fnodi, "Loadset: " + str(sid+1));

    sid += 2;
  }

  clck.stop();
  qDebug("Load mapping: %f", clck.elapsed());

  // debug
  QString dbout = QFileInfo(QString::fromStdString(outfile)).absolutePath();
  smesh->toXml(true).zwrite(str(dbout) + "/loaded.zml");

  QApplication::restoreOverrideCursor();
}

void PLoadDialog::mapTdlLoads()
{
  if (tspec.states.empty())
    return;
  if ( (not smesh) or (not amesh) )
    return;

  // fetch nastran load file name
  string outfile = str(leOutputFile->text());
  if (outfile.empty()) {
    browseOutputFile();
    outfile = str(leOutputFile->text());
    if (outfile.empty())
      return;
  }
  ofstream os(asPath(outfile).c_str());

  // stream for case control statements
  string casefile = append_suffix(outfile, ".case");
  ofstream ocase(asPath(casefile).c_str());

  pgProgress->setMinimum(0);
  pgProgress->setMaximum( tspec.time.size()-1 );
  pgProgress->setValue(0);
  QApplication::setOverrideCursor(Qt::WaitCursor);

  Wallclock clck;
  clck.start();
  buildInterpolator();
  clck.stop();

  qDebug("Tree/map construction: %f", clck.elapsed());

  // scaling coefficients
  Real fscale = sbScaleForce->value();
  Real lscale = sbScaleLength->value();
  uint sid = sbLoadSet->value();

  // pressure fields and nodal forces for each subcase
  const int nstate = tspec.states.size();
  Matrix mpf(pfsi->fluidNodes().size(), nstate);
  Vector refpf(pfsi->fluidNodes().size());

  // collect pressure fields
  clck.start();
  if (tspec.irefcp != NotFound)
    pfsi->extractPressure(1.0, tspec.irefcp, refpf);

  for (int istate=0; istate<nstate; ++istate) {
    Vector ipf( pfsi->fluidNodes().size() );
    uint icp = tspec.states[istate].idcpfield;
    if (icp != NotFound) {
      qDebug("State %d uses aerodynamic field %s", istate,
             amesh->field(icp).name().c_str());
      pfsi->extractPressure(1.0, icp, ipf);
    }
    assert(ipf.size() == mpf.nrows());
    std::copy(ipf.begin(), ipf.end(), mpf.colpointer(istate));
  }
  clck.stop();

  qDebug("Pressure extraction: %f", clck.elapsed());

  // determine nodal forces and moments for pressure fields in
  // one pass for all states / load bases
  clck.start();
  PointGrid<6> fnodal;
  PointList<6> fpref;
  if (rbIntegrate->isChecked()) {
    pfsi->integrate(mpf, fnodal);
    if (tspec.irefcp != NotFound)
      pfsi->integrate(refpf, fpref);
  } else {
    pfsi->agglomerate(mpf, fnodal);
    if (tspec.irefcp != NotFound)
      pfsi->agglomerate(refpf, fpref);
  }
  if (fpref.size() != fnodal.nrows())
    fpref.resize( fnodal.nrows() );
  clck.stop();

  qDebug("Structural load integration: %f", clck.elapsed());

  // structural interface node subset
  const Indices & sifNodes( pfsi->structuralNodes() );
  const int nsif = sifNodes.size();

  // generate one subcase for each timestep
  clck.start();
  const int nsub = tspec.time.size();
  for (int isub=0; isub<nsub; ++isub) {

    pgProgress->setValue( isub );
    qDebug("Processing subcase %d of %d at t = %f", isub, nsub, tspec.time[isub]);
    emit statusMessage(tr("Processing subcase %1 of %2").arg(isub).arg(nsub));
    QApplication::processEvents();

    // assemble global load vector
    const int nvs = smesh->nnodes();
    PointList<6> fg(nvs);

    // dynamic pressure at this step
    Real qoo = tspec.qoo[isub];

    // initialize fg with reference pressure loads
    if (tspec.irefcp != NotFound) {
      for (int i=0; i<nsif; ++i)
        fg[sifNodes[i]] = qoo * fpref[i];
    }

    // linearly superimpose contributions from elastic states
    for (int j=0; j<nstate; ++j) {
      Real xi = tspec.states[j].xi[isub];
      for (int i=0; i<nsif; ++i)
        fg[sifNodes[i]] += qoo * xi * fnodal(i, j);
    }

    // scale aerodynamic forces/moments only, since structural
    // contributions are already in the appropriate units
    for (int j=0; j<nvs; ++j) {
      for (int k=0; k<3; ++k)
        fg[j][k] *= fscale;
      for (int k=3; k<6; ++k)
        fg[j][k] *= fscale*lscale;
    }

    // apply transformation to aerodynamic loads
    fmTrafo.transformList6D( fg );

    // store aerodynamic forces in structural mesh for visualization
    pfsi->appendSifField(fg, "Loadset: " + str(sid));

    // and add inertial loads where applicable;
    // for tis to work, set mggz member in TdlState
    // to empty for modes which do not cause inertial loads
    for (int j=0; j<nstate; ++j) {
      const Vector & mggz( tspec.states[j].mggz );
      if (mggz.size() == (uint) 6*nvs) {
        Real ddxi = tspec.states[j].ddxi[isub];
        for (int i=0; i<nvs; ++i)
          for (int k=0; k<6; ++k)
            fg[i][k] += ddxi * mggz[6*i+k];
      }
    }

    // write out loadset
    pfsi->exportForces(fg, os, sid, 1.0, 1.0);

    // case control commands
    ocase << "$ Timestep " << isub << ", t = " << tspec.time[isub] << endl;
    ocase << "SUBCASE = " << sid << endl;
    ocase << "  LOAD = " << sid << endl;

    ++sid;
  }
  clck.stop();
  qDebug("Load mapping/output: %f", clck.elapsed());

  // debug
  QString dbout = QFileInfo(QString::fromStdString(outfile)).absolutePath();
  smesh->toXml(true).zwrite(str(dbout) + "/loaded.zml");

  QApplication::restoreOverrideCursor();
}

void PLoadDialog::loadSettings()
{
  QString filter = tr("Plain text file (*.cfg);;"
                      "XML settings file (*.xml);;"
                      "All files (*)");
  QString selfilter;
  QString fn = QFileDialog::getOpenFileName(this, tr("Load settings from..."),
                                            lastdir, filter, &selfilter);
  if (fn.isEmpty())
    return;
  lastdir = QFileInfo(fn).absolutePath();

  if (selfilter.contains("XML")) {
    XmlElement xe;
    xe.read( str(fn) );
    configure(xe);
  } else {
    ConfigParser cfg( str(fn) );
    configure(cfg);
  }
}

void PLoadDialog::configure(const XmlElement &xe)
{
  ConfigParser cfg;
  const char cfgName[] = "PressureMapSettings";
  if (xe.name() == cfgName) {
    cfg.fromXml(xe);
  } else {
    XmlElement::const_iterator itr = xe.findChild(cfgName);
    if (itr != xe.end())
      cfg.fromXml(*itr);
  }
  configure(cfg);
}

void PLoadDialog::configure(const ConfigParser &cfg)
{
  if (cfg.hasKey("CaseName"))
    leCaseName->setText( QString::fromStdString(cfg["CaseName"]) );
  else
    leCaseName->setText("");

  if (cfg.hasKey("UsePID"))
    leIncludePID->setText( QString::fromStdString(cfg["UsePID"]) );
  else
    leIncludePID->setText("");

  if (cfg.hasKey("IgnorePID"))
    leExcludePID->setText( QString::fromStdString(cfg["IgnorePID"]) );
  else
    leExcludePID->setText("");

  if (cfg.hasKey("OutFile"))
    leOutputFile->setText( QString::fromStdString(cfg["OutFile"]) );
  else
    leOutputFile->setText("");

  if (cfg.hasKey("NastranMesh")) {
    leNastranMesh->setText( QString::fromStdString(cfg["NastranMesh"]) );
  } else {
    leNastranMesh->setText("");
  }
  loadNastran();

  double cr = cfg.getFloat("CatchRadius", sbCatchRadius->value());
  sbCatchRadius->setValue(cr);

  int sid = cfg.getFloat("LoadSet", sbLoadSet->value());
  sbLoadSet->setValue(sid);

  // this cannot be exactly translated from the CLI tool file format,
  // but that does not matter since it is only used as in the GUI
  double ndev1 = cfg.getFloat("MinNormalAngle", 0.0);
  double ndev2 = cfg.getFloat("MaxNormalAngle", 30.0);
  if (ndev1 < 15) {
    cbInwardNormals->setChecked(false);
    sbNormalTolerance->setValue( ndev2-ndev1 );
  } else {
    cbInwardNormals->setChecked(true);
    sbNormalTolerance->setValue( ndev2-ndev1 );
  }

  fmTrafo.identity();
  if (cfg.hasKey("ForceRotation")) {
    Vct3 rot = cfg.getVct3("ForceRotation");
    fmTrafo.rotate(rot[0], rot[1], rot[2]);
  }

  if (isHarmonic()) {
    sbFStart->setValue( cfg.getFloat("FirstFrequency", sbFStart->value()) );
    sbFEnd->setValue( cfg.getFloat("LastFrequency", sbFEnd->value()) );
    sbNSolSteps->setValue( cfg.getFloat("NumberOfFrequencies",
                                        sbNSolSteps->value()) );
  }
}

ConfigParser PLoadDialog::currentSettings() const
{
  ConfigParser cfg;

  const QString & caseName = leCaseName->text();
  if (not caseName.isEmpty())
    cfg["CaseName"] = str(caseName);

  if ((not leIncludePID->text().isEmpty()) and rbInclude->isChecked())
    cfg["UsePID"] = str(leIncludePID->text());
  if ((not leExcludePID->text().isEmpty()) and rbExclude->isChecked())
    cfg["IgnorePID"] = str(leExcludePID->text());

  double ndev = sbNormalTolerance->value();
  if (cbInwardNormals->isChecked()) {
    cfg["MinNormalAngle"] = str(180 - ndev);
    cfg["MaxNormalAngle"] = "180";
  } else {
    cfg["MinNormalAngle"] = "0";
    cfg["MaxNormalAngle"] = str(ndev);
  }

  cfg["CatchRadius"] = str(sbCatchRadius->value());
  cfg["LoadSet"] = str(sbLoadSet->value());
  if (not leOutputFile->text().isEmpty())
    cfg["OutFile"] = str(leOutputFile->text());

  if (not leNastranMesh->text().isEmpty())
    cfg["NastranMesh"] = str(leNastranMesh->text());

  cfg["ForceRotation"] = str( fmTrafo.rotation() );

  if (isHarmonic()) {
    cfg["FirstFrequency"] = sbFStart->text().toStdString();
    cfg["LastFrequency"] = sbFEnd->text().toStdString();
    cfg["NumberOfFrequencies"] = sbNSolSteps->text().toStdString();
  }

  return cfg;
}

void PLoadDialog::storeSettings()
{
  ConfigParser cfg( currentSettings() );

  QString filter = tr("Settings (*.cfg);; All files (*)");
  QString fn = QFileDialog::getSaveFileName(this, tr("Save settings to..."),
                                            lastdir, filter);
  if (fn.isEmpty())
    return;

  lastdir = QFileInfo(fn).absolutePath();
  ofstream os( asPath(fn).c_str() );
  cfg.write(os);
}

void PLoadDialog::displayStructure(bool flag)
{
  if (flag)
    emit displayMesh( smesh );
  else
    emit displayMesh( amesh );
}

void PLoadDialog::rotationDialog()
{
  TransformationDialog dlg;
  dlg.setTrafo(fmTrafo);
  dlg.useModal(true);
  dlg.enableTranslation(false);
  if (dlg.exec() == QDialog::Accepted) {
    fmTrafo = dlg.currentTrafo();
  }
}

void PLoadDialog::changeEvent(QEvent *e)
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
