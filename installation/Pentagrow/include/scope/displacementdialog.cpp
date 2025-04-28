
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
 
#include "displacementdialog.h"
#include "plotcontroller.h"
#include "view.h"
#include "util.h"
#include <genua/mxmesh.h>


DisplacementDialog::DisplacementDialog(QWidget *parent)
  : QDialog(parent, Qt::Tool), m_plc(0), m_animating(false)
{
  setupUi(this);

#ifdef Q_OS_MACX
  gbMode->setFlat(true);
  gbDeformation->setFlat(true);
  gbTrajectory->setFlat(true);
  gbAnimation->setFlat(true);
#endif

  connect(rbUndeformed, SIGNAL(toggled(bool)),
          this, SLOT(modeUndeformed(bool)));
  connect(rbDeformation, SIGNAL(toggled(bool)),
          this, SLOT(modeDeformation(bool)));
  connect(rbTrajectory, SIGNAL(toggled(bool)),
          this, SLOT(modeTrajectory(bool)));
  connect(tbPlay, SIGNAL(clicked()),
          this, SLOT(play()));
  connect(cbSelectField, SIGNAL(currentIndexChanged(int)),
          this, SLOT(deform()));
  connect(cbSelectTrajectory, SIGNAL(currentIndexChanged(int)),
          this, SLOT(deform()));
  connect(sbMeshDispScale, SIGNAL(editingFinished()),
          this, SLOT(deform()));
  connect(sbTjDispScale, SIGNAL(editingFinished()),
          this, SLOT(deform()));
  connect(sbTjPathScale, SIGNAL(editingFinished()),
          this, SLOT(deform()));

  connect(slScrub, SIGNAL(valueChanged(int)),
          this, SLOT(scrub(int)));
  connect(slAnimSpeed, SIGNAL(valueChanged(int)),
          this, SLOT(adaptAnimationSpeed(int)));

  gbDeformation->hide();
  gbTrajectory->hide();
  gbAnimation->hide();
  adjustSize();
}

void DisplacementDialog::assign(PlotController *plc)
{
  if (m_plc != 0)
    this->disconnect(m_plc);
  m_plc = plc;

  cbSelectField->clear();
  cbSelectTrajectory->clear();

  if (m_plc == 0)
    return;

  MxMeshPtr pmx = m_plc->pmesh();
  if (not pmx)
    return;

  const int nf = pmx->nfields();
  m_dsp.clear();
  for (int i=0; i<nf; ++i) {
    MxMeshField::ValueClass vcl = pmx->field(i).valueClass();
    if (vcl == MxMeshField::ValueClass::Displacement or
        vcl == MxMeshField::ValueClass::Eigenmode)
      m_dsp.push_back(i);
  }

  // only when there are no fields marked explicitely as deformations,
  // accept fields with 3 or 6 dimensions as well
  if (m_dsp.empty()) {
    for (int i=0; i<nf; ++i) {
      const MxMeshField & f( pmx->field(i) );
      if (not f.nodal())
        continue;

      // never use a field named 'velocity' as a displacement...
      if ( toLower( f.name() ) == "velocity" )
        continue;
      uint nd = f.ndimension();
      if (nd == 3 or nd == 6)
        m_dsp.push_back(i);
    }
  }

  int ndsp = m_dsp.size();
  if (ndsp == 0) {
    rbUndeformed->setChecked(true);
    rbDeformation->setEnabled(false);
    gbDeformation->hide();
  } else {
    rbDeformation->setEnabled(true);
    gbDeformation->setVisible( rbDeformation->isChecked() );
    for (int i=0; i<ndsp; ++i) {
      const std::string & s = pmx->field(m_dsp[i]).name();
      cbSelectField->addItem( qstr(s) );
    }
  }

  const int nd = pmx->ndeform();
  if (nd == 0) {
    if (rbTrajectory->isChecked())
      rbUndeformed->setChecked(true);
    rbTrajectory->setEnabled(false);
    gbTrajectory->hide();
  } else {
    rbTrajectory->setEnabled(true);
    gbTrajectory->setVisible( rbTrajectory->isChecked() );
    for (int i=0; i<nd; ++i) {
      const std::string & s = pmx->deform(i).name();
      cbSelectTrajectory->addItem( qstr(s) );
    }
  }

  float speed = ViewManager::animationTimeScale();
  slAnimSpeed->setValue( speedToSlider(speed) );

  // adapt UI when animation ongoing
  connect(m_plc, SIGNAL(animationAt(float)),
          this, SLOT(animationAt(float)));
  connect(m_plc, SIGNAL(animationDone()),
          this, SLOT(animationDone()));
}

void DisplacementDialog::selectField(int ifield)
{
  uint idx = sorted_index(m_dsp, uint(ifield));
  if (idx < uint(cbSelectField->count()))
    cbSelectField->setCurrentIndex(idx);
}

void DisplacementDialog::modeUndeformed(bool flag)
{
  if (flag) {
    gbDeformation->hide();
    gbTrajectory->hide();
    gbAnimation->hide();
    adjustSize();

    if (m_plc)
      m_plc->deformField(-1);
  }
}

void DisplacementDialog::modeDeformation(bool flag)
{
  if (flag) {
    gbDeformation->show();
    gbTrajectory->hide();
    gbAnimation->show();
    adjustSize();
    deform();
  }
}

void DisplacementDialog::modeTrajectory(bool flag)
{
  if (flag) {
    gbDeformation->hide();
    gbTrajectory->show();
    gbAnimation->show();
    adjustSize();
    deform();
  }
}

void DisplacementDialog::deform()
{
  if (not m_plc)
    return;

  MxMeshPtr pmx = m_plc->pmesh();
  if (rbDeformation->isChecked()) {

    const uint icb = cbSelectField->currentIndex();
    if (icb > m_dsp.size())
      return;

    uint ifield = m_dsp[icb];
    lbFieldType->setText(pmx->field(ifield).valueClass().str());

    Real scale = sbMeshDispScale->value() ;
    Real xmax, xmin, xmean;
    pmx->field(ifield).stats(0, xmin, xmax, xmean);
    lbMaxDisp->setText( QString::number(xmax*scale, 'e', 3) );

    m_plc->autoUpdate(false);
    m_plc->deformField( ifield );
    m_plc->deformScale( scale );
    m_plc->updateDisplay();
    m_plc->autoUpdate(true);

  } else if (rbTrajectory->isChecked()) {

    const uint icb = cbSelectTrajectory->currentIndex();
    if (icb > pmx->ndeform())
      return;

    m_plc->autoUpdate(false);
    m_plc->trajectory(icb);
    m_plc->animationMode( PlotController::LoopAnimation |
                          PlotController::TrajectoryDeformation );
    m_plc->deformScale( sbTjDispScale->value() );
    m_plc->rbScale( sbTjPathScale->value() );
    m_plc->animate( 0.0f );  // show initial position (t = 0)
    m_plc->updateDisplay();
    m_plc->autoUpdate(true);
  }
}

void DisplacementDialog::animationAt(float rtime)
{
  if (m_animating) {
    int left = slScrub->minimum();
    int right = slScrub->maximum();
    int ipos = left + rtime*(right - left);
    ipos = std::min(right, std::max(left, ipos));
    slScrub->setValue(ipos);
  }
}

void DisplacementDialog::scrub(int pos)
{
  if (not m_animating) {
    float rpos = float(pos) / ( slScrub->maximum() - slScrub->minimum() );
    if (m_plc) {
      m_plc->animate( rpos );
      emit needRedraw();
    }
  }
}

void DisplacementDialog::animationDone()
{
  tbPlay->setIcon( QIcon(":/icons/play.png") );
  m_plc->autoUpdate(true);
  slScrub->setValue( slScrub->maximum() );
  m_animating = false;
}

void DisplacementDialog::play()
{
  if (m_animating) {
    animationDone();
    slScrub->setEnabled(true);
    emit stopAnimation();
  } else {
    m_animating = true;
    // slScrub->setEnabled(false);
    int aniMode = 0;
    m_plc->autoUpdate(false);
    if (rbDeformation->isChecked()) {
      int ifield = cbSelectField->currentIndex();
      if (uint(ifield) >= m_dsp.size())
        return;
      const MxMeshField & field( m_plc->pmesh()->field(m_dsp[ifield]) );
      if (field.valueClass() == MxMeshField::ValueClass::Displacement)
        aniMode |= PlotController::RampedDeformation;
      if (cbLoop->isChecked())
        aniMode |= PlotController::LoopAnimation;

      m_plc->deformField( m_dsp[ifield] );
      m_plc->deformScale( sbMeshDispScale->value() );

    } else if (rbTrajectory->isChecked()) {
      aniMode = PlotController::TrajectoryDeformation;
      if (cbLoop->isChecked())
        aniMode |= PlotController::LoopAnimation;
      m_plc->trajectory( cbSelectTrajectory->currentIndex() );
      m_plc->deformScale( sbTjDispScale->value() );
      m_plc->rbScale( sbTjPathScale->value() );
    }

    m_plc->animationMode(aniMode);
    tbPlay->setIcon( QIcon(":/icons/stop.png") );
    emit startAnimation();
  }
}

void DisplacementDialog::adaptAnimationSpeed(int slider)
{
  ViewManager::animationTimeScale( sliderToSpeed(slider) );
}

int DisplacementDialog::speedToSlider(float speed) const
{
  const float defaultSpeed = 1.0f / 2048.0f;
  const float f = defaultSpeed / (std::pow(10.0f, 0.5f) - 1.0f);
  float x = std::log10( speed / f + 1.0f );
  float range = slAnimSpeed->maximum() - slAnimSpeed->minimum();
  return slAnimSpeed->minimum() + int(x*range);
}

float DisplacementDialog::sliderToSpeed(int pos) const
{
  // slider -> minimum : stand-still, no motion
  // slider -> maximum : very fast
  // halfway : medium speed, 2048 milliseconds
  const float defaultSpeed = 1.0f / 2048.0f;
  const float f = defaultSpeed / (std::pow(10.0f, 0.5f) - 1.0f);
  float range = slAnimSpeed->maximum() - slAnimSpeed->minimum();
  float x = float(pos - slAnimSpeed->minimum()) / range;
  return f * (std::pow(10.0f, x) - 1.0f);
}
