
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

#include "plotcontroller.h"
#include "meshplotter.h"
#include "streamlineplotter.h"
#include "hedgehogplotter.h"
#include "util.h"
#include "splitridgedialog.h"
#include "surfacestreamlinedialog.h"
#include "streamlinedlg.h"
#include <genua/mxmesh.h>
#include <genua/xcept.h>

#include <QColorDialog>
#include <QDebug>

using std::string;

MxMeshPtr PlotController::load(const QString &fn)
{
  if (not m_plotter)
    m_plotter = boost::make_shared<MeshPlotter>();

  string fname = str(fn);

  // try to add fields first
  MxMeshPtr pmx = m_plotter->pmesh();
  bool addedFields = false;
  if ( pmx and (pmx->nnodes() > 1) and (pmx->nelements() > 1) ) {
    addedFields = m_plotter->addFields( fname );
  }

  if (not addedFields) {
    QString lof = fn.toLower();
    if (lof.endsWith(".stl") or lof.endsWith(".txt")) {
      SplitRidgeDialog dlg;
      dlg.exec();
      pmx = m_plotter->loadStl(fname,
                               dlg.featureAngle(),
                               dlg.mergeThreshold());
    } else {
      pmx = m_plotter->load(fname);
    }
  }

  init();
  return pmesh();
}

MxMeshPtr PlotController::loadFields(const QStringList &fns)
{
  if (m_plotter == nullptr)
    throw Error("Must load mesh first before datasets can be added.");

  MxMeshPtr pmx = m_plotter->pmesh();
  if ( pmx == nullptr or (pmx->nnodes() < 1) or (pmx->nelements() < 1) )
    throw Error("Must load mesh first before datasets can be added.");

  // try to add fields
  for (const QString &fn : fns) {
    bool addedFields = m_plotter->addFields( str(fn) );
    if (not addedFields)
      throw Error("Could not add data fields from file: "+str(fn));
  }

  init();
  return pmesh();
}

void PlotController::assign(MxMeshPtr pmx)
{
  if (not m_plotter)
    m_plotter.reset( new MeshPlotter() );

  qDebug("PlotController::assign");
  m_plotter->assign(pmx);

  init();
}

void PlotController::init()
{
  m_ficontour = NotFound;
  m_fideform = NotFound;
  m_changeFlags = NoChange;
  m_condensation = 0;

  colorBySection();
  updateDisplay();
  emit needBoxUpdate();
}

MxMeshPtr PlotController::pmesh() const
{
  if (m_plotter)
    return m_plotter->pmesh();
  else
    return MxMeshPtr();
}

bool PlotController::hasElements() const
{
  MxMeshPtr pmx = pmesh();
  return (pmx) and (pmx->nelements() > 0);
}

bool PlotController::hasVolume() const
{
  MxMeshPtr pmx = pmesh();
  if (not pmx)
    return false;

  bool flag = false;
  for (uint i=0; i<pmx->nsections(); ++i)
    flag |= pmx->section(i).volumeElements();

  return flag;
}

bool PlotController::hasFields() const
{
  MxMeshPtr pmx = pmesh();
  return (pmx and (pmx->nfields() > 0));
}

bool PlotController::hasVectorFields() const
{
  MxMeshPtr pmx = pmesh();
  if (not pmx)
    return false;

  const int nf = pmx->nfields();
  for (int i=0; i<nf; ++i) {
    const MxMeshField & f( pmx->field(i) );
    if (f.nodal() and f.ndimension() >= 3)
      return true;
  }

  return false;
}

bool PlotController::hasDisplacements() const
{
  MxMeshPtr pmx = pmesh();
  if (not pmx)
    return false;

  bool haveDisp = false;
  const int nf = pmx->nfields();
  for (int i=0; i<nf; ++i) {
    const MxMeshField & f( pmx->field(i) );
    MxMeshField::ValueClass vcl = f.valueClass();
    haveDisp |= (vcl == MxMeshField::ValueClass::Eigenmode);
    haveDisp |= (vcl == MxMeshField::ValueClass::Displacement);
    haveDisp |= (f.nodal() and f.ndimension() == 3);
    haveDisp |= (f.nodal() and f.ndimension() == 6);
  }

  return haveDisp;
}

void PlotController::draw() const
{
  if (m_plotter)
    m_plotter->draw();
}

// -- slots

void PlotController::openStreamlineDialog()
{
  if (pmesh() == nullptr)
    return;

  if (m_sldialog == nullptr) {
    m_sldialog = new SurfaceStreamlineDialog();
    connect(m_sldialog, SIGNAL(streamlinesChanged(bool)),
            this, SLOT(changeStreamlineDisplay(bool)));
    connect(m_sldialog, SIGNAL(requestColorChange()),
            this, SLOT(changeStreamlineColor()));
    connect(m_sldialog, SIGNAL(postStatusMessage(QString)),
            this, SIGNAL(postStatusMessage(QString)));
  }

  m_sldialog->assign(pmesh());
  m_sldialog->show();
}

void PlotController::openHedgehogDialog()
{
  if (pmesh() == nullptr)
    return;

  if (m_hhdialog == nullptr) {
    m_hhdialog = new HedgehogDialog();
    connect(m_hhdialog, SIGNAL(redrawNeeded()),
            this, SIGNAL(needRedraw()));
  }

  m_hhdialog->assign(this);
  m_hhdialog->show();
}

void PlotController::changeStreamlineDisplay(bool enabled)
{
  StreamlinePlotter &slp( m_plotter->streamlines() );
  if (m_sldialog != nullptr) {
    slp.visible(enabled);
    slp.assign( m_sldialog->lines() );
  } else {
    slp.visible(false);
  }
}

void PlotController::changeStreamlineColor()
{
  StreamlinePlotter &slp( m_plotter->streamlines() );
  Color clr( slp.solidColor() );
  QColor qc( clr.red(), clr.green(), clr.blue() );
  qc = QColorDialog::getColor(qc);
  if (qc.isValid()) {
    clr.assign( (float) qc.redF(), (float) qc.greenF(), (float) qc.blueF() );
    slp.solidColor(clr);
    if (slp.visible())
      emit needRedraw();
  }
}

void PlotController::closeAllDialogs()
{
  if (m_sldialog != nullptr)
    m_sldialog->close();
  if (m_hhdialog != nullptr)
    m_hhdialog->close();
}

void PlotController::reload()
{
  if (m_plotter)
    assign(m_plotter->pmesh());
}

void PlotController::autoUpdate(bool flag)
{
  m_autoUpdate = flag;
}

void PlotController::showSection(int isection, bool flag)
{
  if (m_plotter) {
    MxMeshPtr pmx = m_plotter->pmesh();
    if (pmx and uint(isection) < pmx->nsections()) {
      SectionPlotter & sp( m_plotter->section(isection) );
      if (sp.visible() != flag) {
        sp.visible(flag);
        m_plotter->updateNodeTree();
        emit needBoxUpdate();
        emit needRedraw();
        emit sectionShown(isection, flag);
      }
    }
  }
}

void PlotController::showBoco(int iboco, bool flag)
{
  if (m_plotter) {

    m_plotter->bocoVisible(iboco, flag);

    // after this operation, vertex colors must be re-established
    qDebug("Apply coloring to updated sections %d, %d",
           m_colorMode, m_ficontour);

    if ((m_colorMode == FieldContour) and (m_ficontour != NotFound)) {
      m_plotter->fieldColors(m_ficontour, m_vblue, m_vred, m_condensation);
      m_plotter->build();
    } else if (m_colorMode == ByBocos) {
      qDebug("Boco visibility changed while bc colors on, color = %s ",
             pmesh()->boco(iboco).displayColor().str().c_str() );
    }

    emit needBoxUpdate();
    emit needRedraw();
    emit bocoShown(iboco, flag);
  }
}

void PlotController::colorBySection(bool flag)
{
  if (not flag)
    return;
  if (m_plotter) {
    m_colorMode = BySections;
    m_ficontour = NotFound;
    m_plotter->sectionColors();
    m_plotter->build();
    emit needRedraw();
  }
}

void PlotController::colorByBoco(bool flag)
{
  if (not flag)
    return;
  if (m_plotter) {
    m_colorMode = ByBocos;
    m_ficontour = NotFound;
    m_ficontour = NotFound;
    m_plotter->bocoColors();
    m_plotter->build();
    emit needRedraw();
  }
}

void PlotController::changeSectionColor(int isection)
{
  MxMeshPtr pmx = pmesh();
  if ((isection < 0) or (not pmx))
    return;
  else if (uint(isection) >= pmx->nsections())
    return;

  MxMeshSection & sec(pmx->section(isection));
  Color clr( sec.displayColor() );
  QColor qc( clr.red(), clr.green(), clr.blue() );
  qc = QColorDialog::getColor(qc);
  if (qc.isValid()) {
    clr.assign( (float) qc.redF(), (float) qc.greenF(), (float) qc.blueF() );
    sec.displayColor(clr);
    if (m_colorMode == BySections) {
      m_plotter->section(isection).solidColor(clr);
      m_plotter->section(isection).build();
      emit needRedraw();
    }
  }
}

void PlotController::changeBocoColor(int iboco)
{
  MxMeshPtr pmx = pmesh();
  if ((iboco < 0) or (not pmx))
    return;
  else if (uint(iboco) >= pmx->nbocos())
    return;

  MxMeshBoco & bc(pmx->boco(iboco));
  Color clr( bc.displayColor() );
  QColor qc( clr.red(), clr.green(), clr.blue() );
  qc = QColorDialog::getColor(qc);
  if (qc.isValid()) {
    clr.assign( (float) qc.redF(), (float) qc.greenF(), (float) qc.blueF() );
    bc.displayColor(clr);
    if (m_colorMode == ByBocos) {
      uint isection = pmx->mappedSection(iboco);
      if (isection != NotFound) {
        m_plotter->section(isection).solidColor(clr);
        m_plotter->section(isection).build();
        emit needRedraw();
      } else {
        colorByBoco(true);
      }
    }
  }
}

void PlotController::uploadSectionColor(int isection)
{
  if (m_plotter == nullptr)
    return;

  if (isection < 0) {
    m_plotter->sectionColors();
    m_plotter->build();
  } else {
    MxMeshPtr pmx = pmesh();
    if (pmx != nullptr) {
      m_plotter->section(isection).solidColor(pmx->section(isection).displayColor());
      m_plotter->section(isection).build();
    }
  }
  emit needRedraw();
}

void PlotController::eraseSection(int isec)
{
  if (m_plotter and isec >= 0) {
    bool wasVisible = m_plotter->section(isec).visible();
    m_plotter->eraseSection(isec);
    emit structureChanged();
    if (wasVisible) {
      emit needBoxUpdate();
      emit needRedraw();
    }
  }
}

uint PlotController::addMappedBoco(int isec)
{
  uint ibc = NotFound;
  if (m_plotter and isec > 0) {
    ibc = m_plotter->addMappedBoco(isec);
    emit structureChanged();
  }
  return ibc;
}

void PlotController::eraseBoco(int iboco)
{
  if (m_plotter and iboco >= 0) {
    m_plotter->eraseBoco(iboco);
    emit structureChanged();
  }
}

void PlotController::contourSpread(float colorSpread)
{
  if (colorSpread == m_colorspread)
    return;

  m_colorspread = colorSpread;
  m_changeFlags |= SpreadFactor;
  updateColorLimits();
  if (m_autoUpdate)
    updateDisplay();
}

void PlotController::contourLimits(float blueValue, float redValue)
{
  if (m_vblue == blueValue and m_vred == redValue)
    return;
  m_vblue = blueValue;
  m_vred = redValue;
  m_changeFlags |= ColorLimits;
  if (m_autoUpdate)
    updateDisplay();
}

void PlotController::condensation(int vfm)
{
  if (vfm == m_condensation)
    return;
  m_condensation = vfm;
  m_changeFlags |= CondensationMode;

  updateBounds();
  updateColorLimits();

  if (m_autoUpdate)
    updateDisplay();
}

void PlotController::contourField(int ifield, bool updateClrLimits)
{
  if (not m_plotter)
    return;
  if (uint(ifield) == m_ficontour)
    return;

  m_colorMode = FieldContour;
  m_ficontour = (ifield >= 0) ? ifield : NotFound;
  m_changeFlags |= ContourIndex;

  updateBounds();
  if (updateClrLimits)
    updateColorLimits();

  if (m_autoUpdate)
    updateDisplay();
}

void PlotController::deformField(int ifield)
{
  if (m_fideform == uint(ifield))
    return;

  qDebug("Deform field: %d", ifield);

  m_tianim = NotFound;
  m_fideform = (ifield >= 0) ? ifield : NotFound;
  m_changeFlags |= DeformIndex;
  if (m_autoUpdate)
    updateDisplay();
}

void PlotController::trajectory(int itj)
{
  if (m_tianim == uint(itj))
    return;
  m_fideform = NotFound;
  m_tianim = (itj >= 0) ? itj : NotFound;
  m_changeFlags |= TrajectoryIndex;
  if (m_autoUpdate)
    updateDisplay();
}

void PlotController::deformScale(float s)
{
  // if (m_fideform != NotFound)
  //   m_plotter->prepareSingleMode(m_fideform, s);

  if (s == m_modescale)
    return;

  m_modescale = s;
  m_changeFlags |= ElasticScale;
  if (m_autoUpdate)
    updateDisplay();
}

void PlotController::rbScale(float s)
{
  if (s == m_rbscale)
    return;

  m_rbscale = s;
  m_changeFlags |= PathScale;
  if (m_autoUpdate)
    updateDisplay();
}

void PlotController::needleField(int ifield, int mode, float scale)
{
  m_fineedles = ifield;
  m_needleMode = mode;
  m_needleScale = scale;

  m_changeFlags |= NeedleIndex;
  if (m_autoUpdate)
    updateDisplay();
}

void PlotController::updateBounds()
{
  MxMeshPtr pmx = pmesh();
  if ((not pmx) or (m_ficontour > pmx->nfields()))
    return;

  Real minval, maxval, meanval;
  const MxMeshField & f( pmx->field(m_ficontour) );
  f.stats(m_condensation, minval, maxval, meanval);
  m_vmin = minval;
  m_vmax = maxval;
  m_vmean = meanval;
}

void PlotController::updateColorLimits()
{
  float t = 1.0f - sq( clamp(m_colorspread, 0.0f, 1.0f) );
  float vblue = (1.0f - t)*m_vmin + t*m_vmean;
  float vred = (1.0f - t)*m_vmax + t*m_vmean;
  m_changeFlags &= ~SpreadFactor;
  if (vblue != m_vblue or vred != m_vred) {
    m_vblue = vblue;
    m_vred = vred;
    m_changeFlags |= ColorLimits;
    emit blueLimitChanged(m_vblue);
    emit redLimitChanged(m_vred);
  }
}

void PlotController::animateDispField(float rtime)
{
  if ((m_plotter != nullptr) and (m_fideform != NotFound)) {

    // when looping, automatically use fractional time
    if (m_animode & LoopAnimation)
      rtime = rtime - int(rtime);
    else
      rtime = clamp(rtime, 0.0f, 1.0f);

    float rscale(1.0);
    if (m_animode & RampedDeformation)
      rscale = rtime;
    else
      rscale = std::sin( 2*M_PI*rtime );

    m_plotter->animateSingleMode(rscale);

    if ((rtime >= 1.0) and ((m_animode & LoopAnimation) == 0))
      emit animationDone();
    else
      emit animationAt( rtime );
  }
}

void PlotController::animate(float rpos)
{
  if (m_tianim != NotFound)
    animateTrajectory(rpos);
  else if (m_fideform != NotFound)
    animateDispField(rpos);
}

void PlotController::animateTrajectory(float rtime)
{
  MxMeshPtr pmx = pmesh();
  if (pmx == nullptr)
    return;

  if ((m_plotter != nullptr) and (m_tianim != NotFound)) {

    if (m_tianim >= pmx->ndeform())
      return;

    // adjust relative time for looping
    if (m_animode & LoopAnimation)
      rtime = rtime - int(rtime);
    else
      rtime = clamp(rtime, 0.0f, 1.0f);

    // convert to absolute time
    const MxMeshDeform &tj( pmx->deform(m_tianim) );
    Real time = tj.duration() * rtime;

    if (m_animode & TrajectoryFlightPath) {
      float rscale = (m_animode & TrajectoryDeformation) ? m_modescale : 0.0f;
      m_plotter->ipolTrajectory(m_tianim, time, rscale, m_rbscale);
    } else if (m_animode & TrajectoryDeformation) {
      m_plotter->ipolDeformation(m_tianim, time, m_modescale);
    }

    m_plotter->build(true);

    if ((rtime >= 1.0) and ((m_animode & LoopAnimation) == 0))
      emit animationDone();
    else
      emit animationAt( rtime );
  }
}

void PlotController::updateDisplay()
{
  if ( hint_unlikely(m_plotter == nullptr) )
    return;
  if (m_changeFlags == NoChange)
    return;

  MeshPlotter & plotter( *m_plotter );

  if (m_ficontour != NotFound) {

    // update surface contor colors if requested
    if (changed(ContourIndex) or changed(ColorLimits)
        or changed(CondensationMode)) {
      plotter.fieldColors(m_ficontour, m_vblue, m_vred, m_condensation);
    }

  } else if (changed(ContourIndex)) {
    colorBySection();
  }

  if (m_fideform != NotFound) {

    if (changed(DeformIndex) or changed(ElasticScale)) {
      // plotter.deformNodes(m_fideform, m_modescale);
      plotter.prepareSingleMode(m_fideform, m_modescale);
      plotter.animateSingleMode(1.0);
    }

  } else if (changed(DeformIndex)) {
    plotter.undeformedGeometry();
  }

  if (m_fineedles != NotFound) {
    if (changed(NeedleIndex))
      plotter.needleField(m_fineedles, m_needleMode, m_needleScale);
  } else {
    plotter.hedgehog().clear();
  }

  m_changeFlags = NoChange;

  plotter.build(false);
  emit needRedraw();
}
