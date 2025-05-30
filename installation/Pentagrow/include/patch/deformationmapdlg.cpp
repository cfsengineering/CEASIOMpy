
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

#include "deformationmapdlg.h"
#include "util.h"
#include "signallinglogger.h"
#include <genua/mxmesh.h>
#include <genua/csrmatrix.h>
#include <genua/configparser.h>
#include <surf/nstmesh.h>
#include <QFileDialog>
#include <QFileInfo>
#include <QMessageBox>
#include <QDebug>
#include <sstream>
#include <fstream>

using std::string;

DeformationMapDlg::DeformationMapDlg(QWidget *parent)
  : QDialog(parent, Qt::Tool), m_autoRescale(false)
{
  setupUi(this);

  connect(cbUseLinesOnly, SIGNAL(clicked(bool)),
          this, SLOT(enableAeroBoundaries()));
  connect( cbUseLinesOnly, SIGNAL(toggled(bool)),
          this, SLOT(linesOnly(bool)) );
  connect(pbLoadSettings, SIGNAL(clicked()), this, SLOT(loadSettings()));
  connect(pbStoreSettings, SIGNAL(clicked()), this, SLOT(saveSettings()));
  connect(pbHelp, SIGNAL(clicked()), this, SLOT(contextHelp()));

  sbSmoothingIterations->setValue(0);
  sbSmoothingIterations->setMinimum(0);
  sbSmoothingIterations->setSpecialValueText("Direct Solution");

  sbScaleFactor->setValue(0.0);
  sbScaleFactor->setMinimum(0.0);
  sbScaleFactor->setSpecialValueText("Automatic");

  tabWidget->setTabText(0, tr("&Mapping"));
  tabWidget->setTabText(1, tr("&Settings"));
  tabWidget->setCurrentIndex(0);

#ifdef Q_OS_MACX
  gbSpjMethod->setFlat( true );
  gbRbfMethod->setFlat( true );
  gbStructuralMesh->setFlat( true );
  gbSmoothing->setFlat( true );
#endif

  pbApply->setEnabled(false);
  pbExport->setEnabled(false);

  connect( rbRbfMethod, SIGNAL(toggled(bool)),
           this, SLOT(changeMethod()) );
  connect( pbApply, SIGNAL(clicked()), this, SLOT(apply()) );
  connect( pbExport, SIGNAL(clicked()), this, SLOT(exportAs()) );
  connect( pbLoadStructure, SIGNAL(clicked()), this, SLOT(loadStructure()) );

  // RBF types
  cbRbfType->addItem( tr("Polyharmonic, k = 1") );
  cbRbfType->addItem( tr("Polyharmonic, k = 3") );
  cbRbfType->addItem( tr("Polyharmonic, k = 5") );
  cbRbfType->addItem( tr("Multiquadric") );
  cbRbfType->addItem( tr("Inverse Multiquadric") );

  // default: IMQ
  cbRbfType->setCurrentIndex(4);

  sbShapeParameter->setValue(1.0);
  sbMergeThreshold->setValue( gmepsilon );

  m_smesh.reset( new MxMesh );
  changeMethod();
}

bool DeformationMapDlg::haveStructure() const
{
  return (m_smesh->nnodes() > 0);
}

void DeformationMapDlg::assign(MxMeshPtr pmx)
{
  if (pmx == m_amesh)
    return;

  m_amesh = pmx;
  enableAeroBoundaries();
  tabWidget->setCurrentIndex(0);
  changeMethod();
}

void DeformationMapDlg::changeMethod()
{
  if (rbRbfMethod->isChecked()) {
    gbRbfMethod->show();
    gbSpjMethod->hide();
    gbSmoothing->hide();
  } else {
    gbSpjMethod->show();
    gbSmoothing->show();
    gbRbfMethod->hide();
  }
  int imin = cbUseLinesOnly->isChecked() ? 1 : 0;
  sbSmoothingIterations->setMinimum(imin);

  pbExport->setEnabled(false);
  adjustSize();
}

void DeformationMapDlg::enableAeroBoundaries()
{
  bool onlyLines = cbUseLinesOnly->isChecked();
  auto permittedElementSet = [&](int etype) {
    if (onlyLines)
      return etype == Mx::Line2;
    else
      return etype == Mx::Tri3;
  };

  // remove presently attached items
  for (int i=0; i<gridBoundaries->rowCount(); ++i) {
    for (int k=0; k<2; ++k) {
      gridBoundaries->removeItem( gridBoundaries->itemAtPosition(i, k) );
    }
  }
  qDeleteAll( m_bdBoxes );
  m_bdBoxes.clear();
  qDeleteAll( m_bdLabels );
  m_bdLabels.clear();

  // list aerodynamic boundaries
  const int nbc = m_amesh->nbocos();
  for (int i=0; i<nbc; ++i) {

    const MxMeshBoco &bc( m_amesh->boco(i) );
    string bname = bc.name() + " (" + str(bc.bocoType()) + ")";
    QLabel *label = new QLabel( qstr(bname) );
    gridBoundaries->addWidget(label, i, 0);

    QComboBox *combo = new QComboBox;
    combo->addItem(tr("Free Boundary"));          // 0
    combo->addItem(tr("Fixed Boundary"));         // 1
    combo->addItem(tr("Moving Boundary"));        // 2
    combo->addItem(tr("Sliding Boundary"));       // 3
    combo->addItem(tr("Ignore Boundary"));        // 4
    gridBoundaries->addWidget(combo, i, 1);

    if (bc.bocoType() == Mx::BcFarfield) {
      combo->setCurrentIndex(1);
    } else if (bc.bocoType() == Mx::BcWakeSurface) {
      combo->setCurrentIndex(0);
    } else if (bc.bocoType() == Mx::BcElementSet) {
      uint ims = m_amesh->findSection( bc.name() );
      if (ims < m_amesh->nsections()) {
        const MxMeshSection &mappedSec = m_amesh->section(ims);
        if (permittedElementSet(mappedSec.elementType())) {
          combo->setCurrentIndex(2);
          label->setEnabled(true);
        } else {
          combo->setCurrentIndex(4);
          label->setEnabled(false);
        }
      } else {
        combo->setCurrentIndex(4);
        label->setEnabled(false);
      }
    } else {
      combo->setCurrentIndex(2);
    }

    m_bdBoxes.append(combo);
    m_bdLabels.append(label);
  }
}

void DeformationMapDlg::loadStructure()
{
  // fetch structural model from file
  QString filter, selected;
  filter = tr("All supported files (*.zml *.f06 *.pch);; "
              "Nastran results (*.f06 *.pch);; "
              "Native mesh format (*.xml *.zml);; "
              "All files (*)");
  QString fn = QFileDialog::getOpenFileName(this,
                                            tr("Select structural analysis "
                                               "results to open"),
                                            m_lastdir, filter, &selected);
  if (fn.isEmpty()) {
    if (m_smesh)
      return;
    else
      reject();
  } else
    m_lastdir = QFileInfo(fn).absolutePath();

  try {

    if ( selected.contains("Nastran") or fn.endsWith(".f06") ) {
      NstMesh nsm;
      nsm.nstread( str(fn) );
      nsm.toMx(*m_smesh);
    } else {
      m_smesh->loadAny( str(fn) );
    }

    // when loading structural model, estimate suitable smoothing radius
    if ( sbSmoothingRadius->value() == 0 )
      sbSmoothingRadius->setValue( estimateSmoothingRadius() );

    lbStructureFile->setText( fn );
    emit userPathChanged( m_lastdir );

  } catch (Error & xcp) {
    QString title = tr("Failed to load structural model");
    QString xmsg = QString::fromStdString(xcp.what());
    QString text = tr("<b>Problem in file: %1</b><br><hr> %2").arg(fn).arg(xmsg);
    QMessageBox::information( this, title, text );
    return;
  }

  pbApply->setEnabled(true);
}

void DeformationMapDlg::apply()
{
  // erase existing displacements if requested
  if (cbRmOldDisp->isChecked()) {
    const int nf = m_amesh->nfields();
    for (int i=nf-1; i>=0; --i) {
      const MxMeshField & f( m_amesh->field(i) );
      MxMeshField::ValueClass vcl = f.valueClass();
      if (vcl == MxMeshField::ValueClass::Eigenmode or
          vcl == MxMeshField::ValueClass::Displacement)
        m_amesh->eraseField(i);
    }
  }

  try {

    if ( rbRbfMethod->isChecked() )
      mapRbf();
    else
      mapSpj();

  } catch (Error & xcp) {
    QString title = tr("Displacement interpolation failed.");
    QString xmsg = QString::fromStdString(xcp.what());
    QString text = tr("<b>Error message: </b><br><hr> %2").arg(xmsg);
    QMessageBox::information( this, title, text );
    return;
  }

}

void DeformationMapDlg::init(DispInterpolator &dispi)
{
  dispi.setAerodynamic( m_amesh );
  dispi.setStructural( m_smesh );

  uint maxModeCount = sbModeCount->value();
  Real minFreq = sbMinFreq->value();
  Real maxFreq = sbMaxFreq->value();
  dispi.useEigenmodes( maxModeCount, minFreq, maxFreq );

  Indices movingBocos, slidingBocos, fixedBocos, freeBocos;
  const int nbc = m_amesh->nbocos();
  for (int i=0; i<nbc; ++i) {
    if (i >= m_bdBoxes.size())
      continue;
    int idx = m_bdBoxes[i]->currentIndex();
    switch (idx) {
    case Free:
      freeBocos.push_back(i);
      break;
    case Fixed:
      fixedBocos.push_back(i);
      break;
    case Moving:
      movingBocos.push_back(i);
      break;
    case Sliding:
      slidingBocos.push_back(i);
      break;
    case Ignore:
      // do not add to any set
      break;
    }
  }

  if (not movingBocos.empty())
    dispi.collectWallBocos(movingBocos);

  Real scale = sbScaleFactor->value();
  m_autoRescale = (scale == 0.0);
  scale = (scale == 0.0) ? 1.0 : scale;
  dispi.dispScale( scale );
}

void DeformationMapDlg::mapSpj()
{
  if (not m_amesh)
    return;
  if (not m_smesh)
    return;

  try {

    m_sipol = SurfInterpolator();
    init(m_sipol);
//    m_sipol.onlyLines( cbUseLinesOnly->isChecked() );

    // collect PID sets
    Indices pidList;
    std::stringstream ss;
    ss.str( str(txtPidList->toPlainText()) );
    uint pid;
    while (ss >> pid)
      pidList.push_back(pid);

    // build element search tree
    if (pidList.empty())
      m_sipol.buildTreeFromSections();
    else if (rbExcludePID->isChecked())
      m_sipol.buildTreeByPid( Indices(), pidList );
    else
      m_sipol.buildTreeByPid( pidList, Indices() );

    // smoothing criteria
    Real nrmDev = M_PI;
    Real maxDst = 1e18;
    Real smRadius = 0.0;
    int smRing = 0;
    int nsmit = sbSmoothingIterations->value();
    if ( cbSmooth->isChecked() ) {
      if ( nsmit == 0 )
        nsmit = -1;
      if ( cbSmoothingRadius->isChecked() )
        smRadius = sbSmoothingRadius->value();
      if ( cbSmoothRing->isChecked() )
        smRing = sbSmoothRing->value();
      if ( cbNrmDev->isChecked() )
        nrmDev = rad( sbNrmDev->value() );
      if ( cbMaxDist->isChecked() )
        maxDst = sbMaxDist->value();
    } else {
      nsmit = 0;
    }

    int nsglob(0);
    if (cbSmoothGlobal->isChecked())
      nsglob = sbGlobalIterations->value();

    if (cbConcavityLimit->isChecked())
      m_sipol.concavityThreshold( sbConcavityCriterion->value() );

    m_sipol.jumpCriteria(nrmDev, maxDst);
    m_sipol.selectiveSmoothing(nsmit, smRing, smRadius, 0.5f);
    m_sipol.globalSmoothing(nsglob);

    uint nmodes = m_sipol.map();
    if (m_autoRescale)
      m_sipol.autoScale();

    // sipol.addDebugFields();

    pbExport->setEnabled(true);

    emit deformationsChanged(nmodes);

  } catch (Error & xcp) {
    QMessageBox::warning(this, tr("Error in libsurf"),
                         tr("The displacement mapping operation failed in"
                            "libsurf. Error message:\n %1")
                         .arg(qstr(xcp.what())));

  } catch (std::bad_alloc &) {
    QMessageBox::warning(this, tr("Error in libsurf"),
                         tr("The displacement mapping operation failed in"
                            "libsurf: Out of memory."));
  }
}

Real DeformationMapDlg::estimateSmoothingRadius()
{
  if (m_smesh == nullptr)
    return 0;

  Vct3 bblo, bbhi;
  m_smesh->nodes().bounds(bblo, bbhi, true);
  Real lsq = sq(bbhi - bblo);
  if (lsq > 0)
    return 0.006 * sqrt(lsq);
  else
    return 0;
}

void DeformationMapDlg::mapRbf()
{
  // check problem size first
  size_t nsn = m_smesh->nnodes();
  size_t nct = nsn;
  if (cbNodeSubset->isChecked())
    nct = sbTargetNodeCount->value();
  float gbytes = 1.25f * (8.e-9f*nsn) * nct;
  if (gbytes > 2.0f) {
    QString msg = tr("Using RBF interpolation on this model will require "
                     "the solution of a large, dense least-squares problem "
                     "with an estimated memory footprint of at least %1 "
                     "Gigabyte and possibly long runtime. Continue anyway?")
        .arg(gbytes, 0, 'f', 1);
    if ( QMessageBox::warning(this, tr("Problem size warning"), msg,
                              QMessageBox::Yes | QMessageBox::Abort,
                              QMessageBox::Abort )
         == QMessageBox::Abort )
      return;
  }

  m_rbipol = RbfInterpolator();
  init(m_rbipol);

  RbfInterpolator::RbfType rtype = RbfInterpolator::PolyHarmonic1;
  switch (cbRbfType->currentIndex()) {
  case 0:
    rtype = RbfInterpolator::PolyHarmonic1;
    break;
  case 1:
    rtype = RbfInterpolator::PolyHarmonic3;
    break;
  case 2:
    rtype = RbfInterpolator::PolyHarmonic5;
    break;
  case 3:
    rtype = RbfInterpolator::Multiquadric;
    break;
  case 4:
    rtype = RbfInterpolator::InvMultiquadric;
    break;
  default:
    rtype = RbfInterpolator::PolyHarmonic1;
  }

  try {

    m_rbipol.threshold( std::max( gmepsilon, sbMergeThreshold->value() ) );
    m_rbipol.rbfType( rtype, sbShapeParameter->value() );

    if (cbNodeSubset->isChecked()) {
      m_rbipol.centersFromTree( sbTargetNodeCount->value() );
    } else {
      m_rbipol.useStrNodes( cbUsePoints->isChecked(),
                          cbUseBeams->isChecked(),
                          cbUseShells->isChecked() );
    }

    m_rbipol.buildRbfBasis();
    uint nmodes = m_rbipol.map();

    if (m_autoRescale)
      m_rbipol.autoScale();

    pbExport->setEnabled(true);
    emit deformationsChanged(nmodes);

  } catch (Error & xcp) {
    QMessageBox::warning(this, tr("Error in libsurf"),
                         tr("The displacement mapping operation failed in"
                            "libsurf. Error message:\n %1")
                         .arg(qstr(xcp.what())));

  } catch (std::bad_alloc &) {
    QMessageBox::warning(this, tr("Error in libsurf"),
                         tr("The displacement mapping operation failed in"
                            "libsurf. Out of memory."));
  }

}

void DeformationMapDlg::exportAs()
{
  QString title = tr("Select base name for bdis files");
  QString filter = tr("Edge boundary displacements (*.bdis);;"
                      "Mapping matrix H (*.bmap);;"
                      "All files (*)");
  QString selfilter;
  QString fn = QFileDialog::getSaveFileName(this, title, m_lastdir,
                                            filter, &selfilter);
  if (fn.isEmpty())
    return;

  m_lastdir = QFileInfo(fn).absolutePath();

  if (selfilter.contains("bdis")) {
    // construct basename by chopping off .bdis
    if (fn.endsWith(".bdis"))
      fn.chop(5);
    if ( rbRbfMethod->isChecked() )
      m_rbipol.writeBdis( str(fn) );
    else
      m_sipol.writeBdis( str(fn) );
  } else {
    if ( rbRbfMethod->isChecked() ) {
      QMessageBox::warning(this, tr("Not implemented"),
                           tr("Mapping matrix export not yet implemented for "
                              "RBF interpolation"));
      return;
    }

    DispInterpolator::MapMatrix H;
    m_sipol.hmap(H);
    FFANodePtr fnp = m_sipol.mapToFFA(H);

    fnp->write( str(fn) );
  }

  emit userPathChanged(m_lastdir);
}

void DeformationMapDlg::saveSettings()
{
  ConfigParser cfg;
  cfg["Method"] = rbRbfMethod->isChecked() ? ("rbf") : ("projection");

  const QString &txt = txtPidList->toPlainText();
  if (not txt.isEmpty()) {
    if (rbExcludePID->isChecked())
      cfg["ExcludePID"] = str(txt);
    else
      cfg["IncludePID"] = str(txt);
  }

  if (cbUseLinesOnly->isChecked())
    cfg["OnlyEdgesAndLines"] = "true";
  else
    cfg["OnlyEdgesAndLines"] = "false";

  if (cbSmoothingRadius->isChecked())
    cfg["SmoothingRadius"] = str(sbSmoothingRadius->value());

  if (cbSmoothRing->isChecked())
    cfg["SmoothingRing"] = str(sbSmoothRing->value());

  if (cbConcavityLimit->isChecked())
    cfg["ConcavityCriterion"] = str( sbConcavityCriterion->value() );

  if (cbSmooth->isChecked()) {
    if (sbSmoothingIterations->value() == 0)
      cfg["PostSmoothing"] = "-1";
    else
      cfg["PostSmoothing"] = str(sbSmoothingIterations->value());
  } else {
    cfg["PostSmoothing"] = "0";
  }

  if (cbSmoothGlobal->isChecked()) {
    if (sbGlobalIterations->value() != 0)
      cfg["GlobalSmoothing"] = str(sbGlobalIterations->value());
  } else {
    cfg["GlobalSmoothing"] = "0";
  }

  if (sbScaleFactor->value() == 0)
    cfg["AutomaticScaling"] = "true";
  else
    cfg["DispScale"] = str(sbScaleFactor->value());

  cfg["MaxModeCount"] = str(sbModeCount->value());
  cfg["MinFrequency"] = str(sbMinFreq->value());
  cfg["MaxFrequency"] = str(sbMaxFreq->value());

  if (cbNrmDev->isChecked())
    cfg["MapNormalDeviation"] = str(sbNrmDev->value());
  if (cbMaxDist->isChecked())
    cfg["MapMaxDistance"] = str(sbMaxDist->value());

  cfg["UsePoints"] = cbUsePoints->isChecked() ? ("true") : ("false");
  cfg["UseBeams"] = cbUseBeams->isChecked() ? ("true") : ("false");
  cfg["UseShells"] = cbUseShells->isChecked() ? ("true") : ("false");
  cfg["MergeThreshold"] = str(sbMergeThreshold->value());
  cfg["RbfVariant"] = str(cbRbfType->currentText());
  if (cbNodeSubset->isChecked())
    cfg["TargetNodeCount"] = str(sbTargetNodeCount->value());

  // store boundary flags
  if (m_amesh != nullptr) {

    std::string freeBound, fixedBound, movingBound, slidingBound;
    for (int i=0; i<m_bdLabels.size(); ++i) {
      int idx = m_bdBoxes[i]->currentIndex();
      std::string bname = m_amesh->boco(i).name() + ", ";
      switch (idx) {
      case Free:
        freeBound += bname;
        break;
      case Fixed:
        fixedBound += bname;
        break;
      case Moving:
        movingBound += bname;
        break;
      case Sliding:
        slidingBound += bname;
        break;
      case Ignore:
        // do not add to any set
        break;
      }
    }

    if (not freeBound.empty())
      cfg["FreeBoundaries"] = freeBound;
    if (not fixedBound.empty())
      cfg["FixedBoundaries"] = fixedBound;
    if (not movingBound.empty())
      cfg["MovingBoundaries"] = movingBound;
    if (not slidingBound.empty())
      cfg["SlidingBoundaries"] = slidingBound;
  }

  QString fn = QFileDialog::getSaveFileName(this, tr("Save settings to file"),
                                            m_lastdir);
  if (fn.isEmpty())
    return;

  std::ofstream out(str(fn));
  cfg.write(out);
}

void DeformationMapDlg::loadSettings()
{
  QString fn = QFileDialog::getOpenFileName(this, tr("Load settings from file"),
                                            m_lastdir);
  if (fn.isEmpty())
    return;

  ConfigParser cfg(str(fn));
  if ( cfg.hasKey("ExcludePID") ) {
    rbExcludePID->setChecked(true);
    txtPidList->setPlainText( qstr(cfg["ExcludePID"]) );
  } else if ( cfg.hasKey("IncludePID") ) {
    rbIncludePID->setChecked(true);
    txtPidList->setPlainText( qstr(cfg["IncludePID"]) );
  }

  cbUseLinesOnly->setChecked( cfg.getBool("OnlyEdgesAndLines",
                                          cbUseLinesOnly->isChecked()) );
  linesOnly(cbUseLinesOnly->isChecked());

  int val = cfg.getInt("PostSmoothing", 0);
  cbSmooth->setChecked( val != 0 );
  sbSmoothingIterations->setValue( (val < 0) ? 0 : val );

  val = cfg.getInt("GlobalSmoothing", 0);
  cbSmoothGlobal->setChecked( val > 0 );
  sbGlobalIterations->setValue( val );

  val = cfg.getInt("MaxModeCount", sbModeCount->value());
  sbModeCount->setValue(val);

  Real xval = cfg.getFloat("MinFrequency", sbMinFreq->value());
  sbMinFreq->setValue(xval);

  xval = cfg.getFloat("MaxFrequency", sbMaxFreq->value());
  sbMaxFreq->setValue(xval);

  val = cfg.getInt("SmoothingRing", 0);
  cbSmoothRing->setChecked(val != 0);
  sbSmoothRing->setValue(val);

  xval = cfg.getFloat("SmoothingRadius", 0.0);
  cbSmoothingRadius->setChecked(xval != 0.0);
  if (xval != 0.0)
    sbSmoothingRadius->setValue(xval);

  xval = cfg.getFloat("ConcavityLimit", 0.0);
  cbConcavityLimit->setChecked(xval != 0.0);
  if (xval != 0)
    sbConcavityCriterion->setValue(xval);

  if (cfg.getBool("AutomaticScaling", false))
    sbScaleFactor->setValue(0.0);
  else
    sbScaleFactor->setValue( cfg.getFloat("DispScale", 0.0) );

  if (cfg.hasKey("MapNormalDeviation")) {
    cbNrmDev->setChecked(true);
    sbNrmDev->setValue( cfg.getFloat("MapNormalDeviation", sbNrmDev->value()) );
  } else {
    cbNrmDev->setChecked(false);
  }

  if (cfg.hasKey("MapMaxDistance")) {
    cbMaxDist->setChecked(true);
    sbMaxDist->setValue( cfg.getFloat("MapMaxDistance", sbMaxDist->value()) );
  } else {
    cbMaxDist->setChecked(false);
  }

  // set boundary flags
  loadBoundaryFlags(cfg, "FreeBoundaries", Free);
  loadBoundaryFlags(cfg, "FixedBoundaries", Fixed);
  loadBoundaryFlags(cfg, "MovingBoundaries", Moving);
  loadBoundaryFlags(cfg, "SlidingBoundaries", Sliding);

  xval = cfg.getFloat("MergeThreshold", sbMergeThreshold->value());
  sbMergeThreshold->setValue(xval);

  cbUsePoints->setChecked( cfg.getBool("UsePoints", cbUsePoints->isChecked()) );
  cbUseBeams->setChecked( cfg.getBool("UseBeams", cbUseBeams->isChecked()) );
  cbUseShells->setChecked( cfg.getBool("UseShells", cbUseShells->isChecked()) );

  val = cfg.getInt("TargetNodeCount", 0);
  if (val != 0) {
    cbNodeSubset->setChecked(true);
    sbTargetNodeCount->setValue(val);
  } else {
    cbNodeSubset->setChecked(false);
  }
}

void DeformationMapDlg::contextHelp()
{
  emit requestHelp("mapping/index.html");

//  if (tabWidget->currentIndex() == 0) {

//  } else {
//    if (rbRbfMethod->isChecked())
//      emit requestHelp("mapping/index.html#radial-basis-functions");
//    else
//      emit requestHelp("mapping/index.html#projection");
  //  }
}

void DeformationMapDlg::linesOnly(bool flag)
{
  if ( flag and cbSmooth->isChecked() ) {
    if ( sbSmoothingIterations->value() == 0 )
      sbSmoothingIterations->setValue(8);
  }
}

void DeformationMapDlg::loadBoundaryFlags(const ConfigParser &cfg,
                                          const std::string &key, int idx)
{
  if (cfg.hasKey(key)) {
    const std::string & val = cfg[key];
    for (int i=0; i<m_bdLabels.size(); ++i) {
      const string & bname = m_amesh->boco(i).name();
      if (val.find(bname) != string::npos)
        m_bdBoxes[i]->setCurrentIndex(idx);
    }
  }
}

void DeformationMapDlg::changeEvent(QEvent *e)
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
