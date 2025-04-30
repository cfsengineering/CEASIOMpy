/* ------------------------------------------------------------------------
 * project:    scope
 * file:       dlgmeshcut.cpp
 * copyright:  (c) 2009 by <dlr@kth.se>
 * ------------------------------------------------------------------------
 * Specify plane for volume mesh cuts
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */


#include "dlgmeshcut.h"
#include "plotcontroller.h"
#include "meshplotter.h"
#include "ui_dlgmeshcut.h"
#include <genua/plane.h>

MeshCutDialog::MeshCutDialog(QWidget *parent) :
  QDialog(parent, Qt::Tool), m_plc(0), m_ui(new Ui::DlgMeshCut)
{
  m_ui->setupUi(this);

  connect( m_ui->pbApply, SIGNAL(clicked()), this, SLOT(applyCut()) );
  connect( m_ui->pbClear, SIGNAL(clicked()), this, SLOT(clearCurrent()) );
  connect( m_ui->rbXPlane, SIGNAL(clicked()), this, SLOT(fillNormal()) );
  connect( m_ui->rbYPlane, SIGNAL(clicked()), this, SLOT(fillNormal()) );
  connect( m_ui->rbZPlane, SIGNAL(clicked()), this, SLOT(fillNormal()) );

  adjustSize();
}

void MeshCutDialog::assign(PlotController *plc)
{
  m_plc = plc;
  if (m_plc != 0) {
    MeshPlotterPtr plotter = m_plc->plotter();
    plotter->clearVolumeElements();
  }
}

void MeshCutDialog::fillNormal()
{
  if (m_ui->rbXPlane->isChecked()) {
    m_ui->sbNormalX->setValue(1.0);
    m_ui->sbNormalY->setValue(0.0);
    m_ui->sbNormalZ->setValue(0.0);
  } else if (m_ui->rbYPlane->isChecked()) {
    m_ui->sbNormalX->setValue(0.0);
    m_ui->sbNormalY->setValue(1.0);
    m_ui->sbNormalZ->setValue(0.0);
  } else if (m_ui->rbZPlane->isChecked()) {
    m_ui->sbNormalX->setValue(0.0);
    m_ui->sbNormalY->setValue(0.0);
    m_ui->sbNormalZ->setValue(1.0);
  }
}

void MeshCutDialog::applyCut()
{
  if (m_plc == 0)
    return;

  // construct plane from form data
  Vct3 pn;
  pn[0] = m_ui->sbNormalX->value();
  pn[1] = m_ui->sbNormalY->value();
  pn[2] = m_ui->sbNormalZ->value();
  Real dst = m_ui->sbOffset->value();

  MeshPlotterPtr plotter = m_plc->plotter();
  plotter->cutMesh( Plane(pn, dst) );
  emit needRedraw();
}

void MeshCutDialog::clearCurrent()
{
  if (m_plc == 0)
    return;

  MeshPlotterPtr plotter = m_plc->plotter();
  plotter->clearVolumeElements();
  emit needRedraw();
}

MeshCutDialog::~MeshCutDialog()
{
  delete m_ui;
}

void MeshCutDialog::changeEvent(QEvent *e)
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
