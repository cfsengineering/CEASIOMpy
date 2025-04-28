
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
 
#include "streamlinedlg.h"
#include "ui_streamlinedlg.h"
#include "plotcontroller.h"
#include "hedgehogplotter.h"
#include "meshplotter.h"
#include <genua/mxmeshfield.h>

using namespace std;

HedgehogDialog::HedgehogDialog(QWidget *parent) :
    QDialog(parent, Qt::Tool), m_pc(0), m_ui(new Ui::StreamlineDlg)
{
  m_ui->setupUi(this);
  m_ui->sbNeedleScale->setDecimals(3);

  connect(m_ui->pbApply, SIGNAL(clicked()), this, SLOT(apply()));
  connect(m_ui->cbOverlay, SIGNAL(clicked()), this, SLOT(apply()));

  // adapt user interface to selected mode
  connect(m_ui->rbAutoScale, SIGNAL(clicked()), this, SLOT(adaptUi()) );
  connect(m_ui->rbEqualLength, SIGNAL(clicked()), this, SLOT(adaptUi()) );
  connect(m_ui->rbScaleNeedles, SIGNAL(clicked()), this, SLOT(adaptUi()) );

  // set default scaling value when field selection changed
  connect(m_ui->cbSelectField, SIGNAL(currentIndexChanged(int)),
          this, SLOT(defaultScaling()));
}

HedgehogDialog::~HedgehogDialog()
{
  delete m_ui;
}

void HedgehogDialog::assign(PlotController *pc)
{
  m_pc = pc;
  if (not m_pc)
    return;

  const MxMeshPtr pmx( m_pc->pmesh() );
  if (not pmx)
    return;

  const int nf = pmx->nfields();
  m_ui->cbSelectField->clear();
  for (int i=0; i<nf; ++i) {
    const MxMeshField & f( pmx->field(i) );
    if (f.ndimension() == 3 or f.ndimension() == 6) {
      m_ivf.push_back(i);
      QString s = QString::fromStdString(f.name());
      m_ui->cbSelectField->addItem(s);
    }
  }

  adaptUi();
}

void HedgehogDialog::apply()
{
  if (not m_pc)
    return;

  if (m_ui->cbOverlay->isChecked()) {

    int kcb = m_ui->cbSelectField->currentIndex();
    float scale = m_ui->sbNeedleScale->value();

    // default is fixed needle length specified by user
    int mode = HedgehogPlotter::EqualLength;
    if (m_ui->rbScaleNeedles->isChecked())
      mode = HedgehogPlotter::ByMagnitude;
    else if (m_ui->rbAutoScale->isChecked())
      mode = HedgehogPlotter::LocalLength;

    m_pc->needleField( m_ivf[kcb], mode, scale );

  } else {
    m_pc->needleField(NotFound, 0, 1.0f);
  }

  emit redrawNeeded();
}

void HedgehogDialog::adaptUi()
{
  if (m_ui->rbAutoScale->isChecked()) {
    m_ui->lbScaleFactor->setText( tr("Length scale factor") );
  } else if ( m_ui->rbEqualLength->isChecked() ) {
    m_ui->lbScaleFactor->setText( tr("Absolute needle length") );
  } else if ( m_ui->rbScaleNeedles->isChecked() ) {
    m_ui->lbScaleFactor->setText( tr("Needle length/magnitude") );
  }
  defaultScaling();
}

void HedgehogDialog::defaultScaling()
{
  if (not m_pc)
    return;

  MeshPlotterPtr plotter = m_pc->plotter();
  if (not plotter)
    return;
  MxMeshPtr pmx = m_pc->pmesh();
  if (not pmx)
    return;

  float diag = norm( plotter->lowCorner() - plotter->highCorner() );
  if ( m_ui->rbEqualLength->isChecked() ) {
    m_ui->sbNeedleScale->setValue( 0.01*diag );
  } else if ( m_ui->rbScaleNeedles->isChecked() ) {
    int kcb = m_ui->cbSelectField->currentIndex();
    if (kcb < 0)
      return;

    Real vmin, vmax, vmean;
    const MxMeshField & field( pmx->field(m_ivf[kcb]) );
    field.stats( 0, vmin, vmax, vmean );
    float scale = std::max(0.1*diag/vmax, 0.01*diag/vmean);
    m_ui->sbNeedleScale->setValue( scale );
  }

}

void HedgehogDialog::changeEvent(QEvent *e)
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
