
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
 
#include "contourdialog.h"
#include "plotcontroller.h"
#include "meshplotter.h"
#include "util.h"
#include <genua/mxmesh.h>
#include <QDebug>

using namespace std;

ContourDialog::ContourDialog(QWidget *parent) : QDialog(parent, Qt::Tool), m_plc(0)
{
  setupUi(this);

#ifdef Q_OS_MACX
  gbHeader->setFlat(true);
  gbFieldSelection->setFlat(true);
  gbColorContours->setFlat(true);
#endif

  cbCondensation->addItem( tr("Magnitude") );
  cbCondensation->addItem( tr("X-Component") );
  cbCondensation->addItem( tr("Y-Component") );
  cbCondensation->addItem( tr("Z-Component") );

  // translate slider position to float spread value
  connect( slSpread, SIGNAL(valueChanged(int)),
           this, SLOT(changeSpread(int)) );

  // update GUI for change of field and condensation selection
  connect( cbFieldName, SIGNAL(currentIndexChanged(int)),
           this, SLOT(fieldSelected(int)) );
  connect( cbCondensation, SIGNAL(currentIndexChanged(int)),
           this, SLOT(condensationChanged(int)) );

  // update view
  connect( rbFieldColors, SIGNAL(toggled(bool)),
           this, SLOT(enableContourSettings(bool)) );

  // redraw on change of color limits
  connect( sbBlueValue, SIGNAL(editingFinished()),
           this, SLOT(applyLimits()) );
  connect( sbRedValue, SIGNAL(editingFinished()),
           this, SLOT(applyLimits()) );

  // change lock icon
  connect( tbLockRange, SIGNAL(toggled(bool)),
           this, SLOT(lockRange(bool)) );
}

void ContourDialog::assign(PlotController *plc)
{
  // disconnect if necessary
  if (m_plc != 0)
    this->disconnect( m_plc );

  m_plc = plc;
  if (not m_plc)
    return;

  MxMeshPtr pmx = m_plc->pmesh();
  if (not pmx)
    return;

  // remember selected field
  int prefield = cbFieldName->currentIndex();

  // list all fields in combo box
  cbFieldName->clear();
  for (uint i=0; i<pmx->nfields(); ++i) {
    const string & s( pmx->field(i).name() );
    cbFieldName->addItem( QString::fromStdString(s) );
  }

  // enable/disable depending on top-level selection
  connect( rbSectionColors, SIGNAL(toggled(bool)),
           m_plc, SLOT(colorBySection(bool)) );
  connect( rbBocoColors, SIGNAL(toggled(bool)),
           m_plc, SLOT(colorByBoco(bool)) );

  // propagate color limit changes from controller to GUI
  connect( m_plc, SIGNAL(blueLimitChanged(double)),
           sbBlueValue, SLOT(setValue(double)) );
  connect( m_plc, SIGNAL(redLimitChanged(double)),
           sbRedValue, SLOT(setValue(double)) );

  // tell controller about color spread changes
  connect( this, SIGNAL(spreadChanged(float)),
           m_plc, SLOT(contourSpread(float)) );

  // select previous field if possible
  if (prefield >= 0 and prefield < cbFieldName->count()) {
    selectField(prefield);
    fieldSelected(prefield);
  } else if ( cbFieldName->count() > 0 ) {
    uint fi = pmx->findField("CoefPressure");
    if (fi != NotFound) {
      selectField(fi);
      fieldSelected(fi);
    } else {
      selectField(0);
      fieldSelected(0);
    }
  }
}

void ContourDialog::enableContourSettings(bool flag)
{
  gbFieldSelection->setEnabled(flag);
  gbColorContours->setEnabled(flag);
}

void ContourDialog::selectField(int ifield)
{
  if (ifield < 0)
    return;
  if ( cbFieldName->currentIndex() != ifield )
    cbFieldName->setCurrentIndex( ifield );
}

void ContourDialog::fieldSelected(int ifield)
{
  if (not m_plc)
    return;
  if (ifield < 0)
    return;

  MxMeshPtr pmx = m_plc->pmesh();
  if (not pmx)
    return;

  const MxMeshField & field( pmx->field(ifield) );
  if (field.nodal() and field.ndimension() > 1) {
    cbCondensation->setEnabled(true);
    cbCondensation->clear();
    cbCondensation->addItem( tr("Magnitude") );
    for (uint j=0; j<field.ndimension(); ++j)
      cbCondensation->addItem( tr("Component ") + qstr(field.componentName(j)) );
  } else
    cbCondensation->setEnabled(false);

  if (tbLockRange->isChecked()) {
    m_plc->contourField(ifield, false);
    m_plc->contourLimits(  sbBlueValue->value(),
                           sbRedValue->value() );
  } else {
    m_plc->contourField(ifield, true);
    lbMaxValue->setText( QString::number( m_plc->maxFieldValue(), 'g', 3 ) );
    lbMinValue->setText( QString::number( m_plc->minFieldValue(), 'g', 3 ) );
  }
}

void ContourDialog::condensationChanged(int vfm)
{
  if (not m_plc)
    return;

  m_plc->condensation(vfm);
  lbMaxValue->setText( QString::number( m_plc->maxFieldValue(), 'g', 3 ) );
  lbMinValue->setText( QString::number( m_plc->minFieldValue(), 'g', 3 ) );
}

void ContourDialog::applyLimits()
{
  if (not m_plc)
    return;

  m_plc->autoUpdate(false);
  m_plc->contourLimits( sbBlueValue->value(), sbRedValue->value() );
  m_plc->updateDisplay();
  m_plc->autoUpdate(true);
}

void ContourDialog::changeSpread(int sliderPos)
{
  if (tbLockRange->isChecked())
    return;
  if (sliderPos < 0)
    sliderPos = slSpread->value();
  float range = slSpread->maximum() - slSpread->minimum();
  emit spreadChanged( float(sliderPos) / range );
}

void ContourDialog::lockRange(bool flag)
{
  slSpread->setEnabled( !flag );
  if ( flag )
    tbLockRange->setIcon( QIcon(":/icons/lock.png") );
  else
    tbLockRange->setIcon( QIcon(":/icons/unlock.png") );
}

