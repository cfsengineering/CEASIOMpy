
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
 
#include <QFileDialog>
#include <QMessageBox>
#include <QFileInfo>
#include <QPen>

#include "view.h"
#include "slicedlg.h"
#include "util.h"
#include "qcustomplot.h"
#include "segmentplot.h"
#include "util.h"
#include "ui_slicedlg.h"

SliceDlg::SliceDlg(QWidget *parent) : QDialog(parent, Qt::Tool),
                                      ui(new Ui::SliceDlg)
{
  botCol = leftCol = rightCol = -1;
  leftLastChanged = true;

  ui->setupUi(this);
#ifdef Q_OS_MACX
  ui->gbSlicePlane->setFlat(true);
  ui->gbPlotParam->setFlat(true);
  ui->gbPlotBox->setFlat(true);
#endif

  leftPlot = new SegmentPlot( ui->plotWdg->xAxis,
                              ui->plotWdg->yAxis );
  QPen lpen( QColor(0,0,100) );
  lpen.setCapStyle( Qt::RoundCap );
  lpen.setJoinStyle( Qt::RoundJoin );
  lpen.setWidth( 2 );
  leftPlot->setPen( lpen );

  QPen rpen( QColor(80,0,20) );
  rpen.setCapStyle( Qt::RoundCap );
  rpen.setJoinStyle( Qt::RoundJoin );
  rpen.setWidth( 2 );
  rightPlot = new SegmentPlot( ui->plotWdg->xAxis,
                               ui->plotWdg->yAxis2 );
  rightPlot->setPen( rpen );

  ui->plotWdg->addPlottable( leftPlot );
  ui->plotWdg->addPlottable( rightPlot );

  QPalette fp( ui->plotFrame->palette() );
  fp.setColor( QPalette::Window, Qt::white );
  ui->plotFrame->setPalette( fp );

  connect(ui->pbSlice, SIGNAL(clicked()), this, SLOT(slice()));
  connect(ui->pbSave, SIGNAL(clicked()), this, SLOT(savePlot()));
  connect(ui->rbNxPlane, SIGNAL(clicked()), this, SLOT(planeNx()));
  connect(ui->rbNyPlane, SIGNAL(clicked()), this, SLOT(planeNy()));
  connect(ui->rbNzPlane, SIGNAL(clicked()), this, SLOT(planeNz()));

  connect(ui->cbSelectX, SIGNAL(currentIndexChanged(int)),
          this, SLOT(bottomAxis(int)) );
  connect(ui->cbSelectLeft, SIGNAL(currentIndexChanged(int)),
          this, SLOT(leftAxis(int)) );
  connect(ui->cbSelectRight, SIGNAL(currentIndexChanged(int)),
          this, SLOT(rightAxis(int)) );
  connect(ui->cbManualScale, SIGNAL(clicked()),
          this, SLOT(showPlot()) );
  connect(ui->sbYScaleMin, SIGNAL(editingFinished()),
          this, SLOT(showPlot()) );
  connect(ui->sbYScaleMax, SIGNAL(editingFinished()),
          this, SLOT(showPlot()) );

  connect(ui->sbNxOffset, SIGNAL(valueChanged(double)),
          this, SLOT(planeNx(double)));
  connect(ui->sbNyOffset, SIGNAL(valueChanged(double)),
          this, SLOT(planeNy(double)));
  connect(ui->sbNzOffset, SIGNAL(valueChanged(double)),
          this, SLOT(planeNz(double)));

  bInPlane = false;
  adjustSize();
}

SliceDlg::~SliceDlg()
{
  delete ui;

  // don't delete this, plot widget destroys it already
  // delete plotSegments;
}

void SliceDlg::attach(MxMeshPtr pm, const Vct3f &plo, const Vct3f &phi)
{
  mslice = MxMeshSlice(pm);
  lobox = plo;
  hibox = phi;

  // clear out combo boxes
  ui->cbSelectX->clear();
  ui->cbSelectLeft->clear();
  ui->cbSelectRight->clear();
}

void SliceDlg::slice()
{
  Vct3 org, Su, Sv;

  org[0] = ui->sbOrgX->value();
  org[1] = ui->sbOrgY->value();
  org[2] = ui->sbOrgZ->value();

  Su[0] = ui->sbSuX->value();
  Su[1] = ui->sbSuY->value();
  Su[2] = ui->sbSuZ->value();

  Sv[0] = ui->sbSvX->value();
  Sv[1] = ui->sbSvY->value();
  Sv[2] = ui->sbSvZ->value();

  mslice.clear();
  mslice.slice(org, org+Su, org+Sv);

  if (ui->cbJoinSegments->isChecked())
    mslice.joinSegments( ui->sbJoinTol->value() );

  // extract column names
  StringArray coln;
  mslice.columns(coln);
  columnNames.clear();
  // columnNames.reserve(coln.size());  // Qt >= 4.7
  invertAxis.clear();
  invertAxis.resize(coln.size(), false);
  for (uint i=0; i<coln.size(); ++i) {
    columnNames.append( qstr(coln[i]) );
    invertAxis[i] = (coln[i] == "CoefPressure") or
                    (coln[i] == "pressure_coeff");
  }
  qDebug("%u columns in data slice.", (uint) coln.size());

  fillComboBox( ui->cbSelectX );
  fillComboBox( ui->cbSelectLeft );
  fillComboBox( ui->cbSelectRight );

  if (botCol < 0 and leftCol < 0)
    defaultColumns();
  showPlot();
}

void SliceDlg::showPlot()
{
  if (botCol < 0)
    return;

  QCustomPlot & plot( *(ui->plotWdg) );
  if (leftCol >= 0) {
    leftPlot->assign(mslice, botCol, leftCol);
    plot.yAxis->setRangeReversed( invertAxis[leftCol] );
    plot.yAxis->setLabel( columnNames.at(leftCol) );
    if (ui->cbManualScale->isChecked())
      plot.yAxis->setRange( ui->sbYScaleMin->value(),
                            ui->sbYScaleMax->value() );
  } else {
    leftPlot->clearData();
    plot.yAxis->setLabel( QString() );
  }
  if (rightCol >= 0) {
    rightPlot->assign(mslice, botCol, rightCol);
    plot.yAxis2->setRangeReversed( invertAxis[rightCol] );
    plot.yAxis2->setLabel( columnNames.at(rightCol) );
    if (ui->cbManualScale->isChecked())
      plot.yAxis2->setRange( ui->sbYScaleMin->value(),
                             ui->sbYScaleMax->value() );
  } else {
    rightPlot->clearData();
    plot.yAxis2->setLabel( QString() );
  }

  plot.xAxis->setLabel( columnNames.at(botCol) );
  plot.yAxis->setVisible(leftCol >= 0);
  plot.yAxis2->setVisible(rightCol >= 0);
  plot.replot();
}

void SliceDlg::defaultColumns()
{
  // select default : first axis direction
  Real ux = fabs( ui->sbSuX->value() );
  Real uy = fabs( ui->sbSuY->value() );
  Real uz = fabs( ui->sbSuZ->value() );

  int xcol(-1), ycol(-1);
  if (ux > uy and ux > uz)
    xcol = 0;
  else if (uy > ux and uy > uz)
    xcol = 1;
  else
    xcol = 2;

  const int ncol = columnNames.size();
  ycol = columnNames.indexOf("CoefPressure");
  if (ycol < 0)
    ycol = columnNames.indexOf("pressure_coeff");
  if (ycol < 0 and ncol > 3)
    ycol = 3;

  ui->cbSelectX->setCurrentIndex( xcol+1 );
  ui->cbSelectLeft->setCurrentIndex( ycol+1 );
  ui->cbSelectRight->setCurrentIndex(0);
}

void SliceDlg::bottomAxis(int col)
{
  if (col < 0)
    return;
  col -= 1;
  if (col != botCol) {
    botCol = col;
    showPlot();
  }
}

void SliceDlg::leftAxis(int col)
{
  if (col < 0)
    return;
  col -= 1;
  if (col != leftCol) {
    leftLastChanged = true;
    leftCol = col;
    showPlot();
  }
}

void SliceDlg::rightAxis(int col)
{
  if (col < 0)
    return;
  col -= 1;
  if (col != rightCol) {
     leftLastChanged = false;
    rightCol = col;
    showPlot();
  }
}

void SliceDlg::assignLeftField(int ifield)
{
  int col = columnIndex(ifield);
  if (col < 0)
    return;
  ui->cbSelectLeft->setCurrentIndex( col+1 );
  leftLastChanged = true;
}

void SliceDlg::assignRightField(int ifield)
{
  int col = columnIndex(ifield);
  if (col < 0)
    return;
  ui->cbSelectRight->setCurrentIndex( col+1 );
  leftLastChanged = false;
}

void SliceDlg::assignCurrentField(int ifield)
{
  if (leftLastChanged)
    assignLeftField(ifield);
  else
    assignRightField(ifield);
}

void SliceDlg::planeNx()
{
  allZero();
  Real minds = 0.01 * norm(hibox - lobox);
  ui->sbOrgX->setValue( ui->sbNxOffset->value() );
  ui->sbOrgY->setValue( lobox[1] - minds );
  ui->sbOrgZ->setValue( lobox[2] - minds );
  ui->sbSuY->setValue( hibox[1] - lobox[1] + 2*minds );
  ui->sbSvZ->setValue( hibox[2] - lobox[2] + 2*minds );
}

void SliceDlg::planeNx(double offs)
{
  ui->sbOrgX->setValue( offs );
}

void SliceDlg::planeNy()
{
  allZero();
  Real minds = 0.01 * norm(hibox - lobox);
  ui->sbOrgX->setValue( lobox[0] - minds );
  ui->sbOrgY->setValue( ui->sbNyOffset->value() );
  ui->sbOrgZ->setValue( hibox[2] + minds );
  ui->sbSuX->setValue(  hibox[0] - lobox[0] + 2*minds );
  ui->sbSvZ->setValue( -(hibox[2] - lobox[2]) - 2*minds );
}

void SliceDlg::planeNy(double offs)
{
  ui->sbOrgY->setValue( offs );
}

void SliceDlg::planeNz()
{
  allZero();
  Real minds = 0.01 * norm(hibox - lobox);
  ui->sbOrgX->setValue( lobox[0] - minds );
  ui->sbOrgY->setValue( lobox[1] - minds );
  ui->sbOrgZ->setValue( ui->sbNzOffset->value() );
  ui->sbSuX->setValue( hibox[0] - lobox[0] + 2*minds );
  ui->sbSvY->setValue( hibox[1] - lobox[1] + 2*minds );
}

void SliceDlg::planeNz(double offs)
{
  ui->sbOrgZ->setValue( offs );
}

void SliceDlg::allZero()
{
  ui->sbOrgX->setValue( 0.0 );
  ui->sbOrgY->setValue( 0.0 );
  ui->sbOrgZ->setValue( 0.0 );

  ui->sbSuX->setValue( 0.0 );
  ui->sbSuY->setValue( 0.0 );
  ui->sbSuZ->setValue( 0.0 );

  ui->sbSvX->setValue( 0.0 );
  ui->sbSvY->setValue( 0.0 );
  ui->sbSvZ->setValue( 0.0 );
}

int SliceDlg::columnIndex(int ifield) const
{
  MxMeshPtr pmx = mslice.mesh();
  if (pmx == nullptr)
    return -1;
  if (uint(ifield) < pmx->nfields())
    return columnNames.indexOf( qstr(pmx->field(ifield).name()) );
  else
    return -1;
}

void SliceDlg::savePlot()
{
  if (mslice.nsegments() > 0) {
    QString sfil, filter = tr( "Matlab M-file (*.m);;"
                               "Data as plain text (*.txt);;"
                               "Plot as PDF (*.pdf)");
    QString fileName = QFileDialog::getSaveFileName(this, tr("Save plot or data"),
                                                    lastdir, filter, &sfil);
    if (not fileName.isEmpty()) {
      QString funcName = QFileInfo(fileName).fileName();
      if ( sfil.contains("Matlab") ) {
        int idot = funcName.indexOf('.');
        if (idot != -1)
          funcName = funcName.left(idot);
        else
          fileName.append(".m");
        mslice.writeMatlab(str(funcName), str(fileName));
      } else if ( sfil.contains(tr("Data as plain text")) ){
        mslice.writePlain(append_suffix(fileName, ".txt"));
      } else {
        ui->plotWdg->savePdf( fileName, true, 640, 480 );
      }
    }
  } else {
    QString msg = tr("<b>Slicing plane outside mesh</b><br/><hr>");
    msg += tr("Slicing the present mesh with the plane specified ");
    msg += tr("does not yield any intersected elements. The plane ");
    msg += tr("is completely outside the volume occupied by the mesh.");
    QMessageBox::information(this, tr("Mesh Slice"), msg);
  }
}

void SliceDlg::fillComboBox(QComboBox *box) const
{
  int lastItem = box->currentIndex();

  box->clear();
  box->addItem( tr("Not Assigned") );
  const int ncol = columnNames.size();
  for (int i=0; i<ncol; ++i)
    box->addItem( columnNames.at(i) );

  if (lastItem >= 0 and lastItem < ncol)
    box->setCurrentIndex(lastItem);
}

void SliceDlg::changeEvent(QEvent *e)
{
  QDialog::changeEvent(e);
  switch (e->type()) {
  case QEvent::LanguageChange:
    ui->retranslateUi(this);
    break;
  default:
    break;
  }
}
