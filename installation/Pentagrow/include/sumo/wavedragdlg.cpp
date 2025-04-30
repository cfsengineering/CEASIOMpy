
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
 
#include "wavedragdlg.h"
#include "qcustomplot.h"
#include "util.h"
#include <genua/trimesh.h>
#include <genua/ioglue.h>
#include <QFileDialog>
#include <QApplication>

using std::string;

WaveDragDlg::WaveDragDlg(QWidget *parent) : QDialog(parent, Qt::Tool)
{
  setupUi(this);

  sbRefArea->setDecimals(3);
  sbCutoff->setDecimals(3);
  sbInletArea->setDecimals(3);
  sbInletCoordinate->setDecimals(3);

  SCdw = 0.0;

  connect(pbApply, SIGNAL(clicked()), this, SLOT(apply()));
  connect(pbSave, SIGNAL(clicked()), this, SLOT(saveDistribution()));
  connect(sbRefArea, SIGNAL(editingFinished()), this, SLOT(areaChanged()));
}

void WaveDragDlg::assign(const TriMesh &tm, const Indices &intakeTags)
{
  xv.clear();
  Sv.clear();
  lbDragCoef->setText(tr("(n/a)"));
  pbSave->setEnabled(false);
  vwd = VolWaveDrag(tm);

  inArea.clear();
  inCtr.clear();

  // determine approximate intake area
  Real inletArea = 0;
  Vct3 inletCtr;
  const int nf = tm.nfaces();
  for (int i=0; i<nf; ++i) {
    uint t = tm.face(i).tag();
    if (binary_search(intakeTags.begin(), intakeTags.end(), t)) {
      Real a = tm.face(i).area();
      Vct3 ctr = tm.face(i).center();
      inletArea += a;
      inletCtr += a*ctr;
      inCtr.push_back( ctr );
      inArea.push_back( a );
    }
  }
  inletCtr /= inletArea;

  sbInletArea->setValue( inletArea );
  sbInletCoordinate->setValue( inletCtr[0] );
}

void WaveDragDlg::assign(const MxMesh &mx)
{
  xv.clear();
  Sv.clear();
  lbDragCoef->setText(tr("(n/a)"));
  pbSave->setEnabled(false);
  vwd = VolWaveDrag(mx);

  // TODO : Compute inlet area from bocos
}

void WaveDragDlg::effectiveStreamtube(Real mach)
{
  const int nx = xv.size();
  const int nie = inArea.size();

  Svi.resize(nx);
  Svi = 0.0;

  if (nx == 0)
    return;

  if (rbExplicitIntake->isChecked()) {

    Real ain = sbInletArea->value();
    Real xin = sbInletCoordinate->value();
    for (int i=0; i<nx; ++i) {
      if (xv[i] > xin)
        Svi[i] += ain;
    }

  } else {

    // cotangent of the mach cone angle
    Real ctg = sqrt(sq(mach) - 1);

#pragma omp parallel for
    for (int i=0; i<nx; ++i) {
      Real xi = xv[i];
      for (int j=0; j<nie; ++j) {
        Real xj = inCtr[j][0];
        Real aj = inArea[j];
        Real rj = sqrt( sq(inCtr[j][1]) + sq(inCtr[j][2]) );
        if ( xj-xi < ctg*rj )
          Svi[i] += aj;
      }
    }

  }
}

void WaveDragDlg::apply()
{
  Real mach = sbMachNumber->value();
  Real Sref = sbRefArea->value();
  Real inletArea = sbInletArea->value();
  Real inletCoord = sbInletCoordinate->value();

  Real cutoff = sbCutoff->value();
  const int nsec = sbLongSec->value();
  const int nphi = sbCircSec->value();

  // notify UI that computation is running
  lbDragCoef->setText(tr("computing..."));
  QApplication::processEvents();

  Vct3 pn(1.0, 0.0, 0.0);
  vwd.meanAreaDistribution(pn, mach, nsec, nphi, xv, Sv);

  // substract inlet area from area distribution
  effectiveStreamtube( mach );
  const int nx = Sv.size();
  Vector Sff( nx );
  for (int i=0; i<nx; ++i)
    Sff[i] = std::max(0.0, Sv[i] - Svi[i]);

  Real cdw = VolWaveDrag::dragCoefficient(Sref, xv, Sff, cutoff);
  SCdw = cdw * Sref;

  pbSave->setEnabled(true);
  areaChanged();
  plotDistribution();
}

void WaveDragDlg::saveDistribution()
{
  QString caption = tr("Save area distribution to file");
  QString filter = tr("Plain text files (*.txt);; All files (*)");
  QString fn = QFileDialog::getSaveFileName(this, caption, lastdir, filter);
  if (not fn.isEmpty()) {
    lastdir = QFileInfo(fn).absolutePath();
    const int n = xv.size();
    assert(Sv.size() == size_t(n));
    ofstream os(asPath(fn).c_str());
    os.precision(12);
    for (int i=0; i<n; ++i)
      os << xv[i] << " " << Sv[i] << endl;
    os.close();
  }
}

void WaveDragDlg::areaChanged()
{
  Real cdw = SCdw / sbRefArea->value();
  lbDragCoef->setText( QString::number(cdw, 'f', 4) );
}

void WaveDragDlg::plotDistribution()
{
  // convert area distribution data for plotting widget
  const int np = xv.size();
  if (np == 0)
    return;

  QVector<double> xp(np), Sp(np), Spi(np);
  copy(xv.begin(), xv.end(), xp.begin());
  copy(Sv.begin(), Sv.end(), Sp.begin());
  for (int i=0; i<np; ++i)
    Spi[i] = std::max(0.0, Sv[i]-Svi[i]);

  double xmin = *(min_element(xv.begin(), xv.end()));
  double xmax = *(max_element(xv.begin(), xv.end()));
  double Smin = *(min_element(Sv.begin(), Sv.end()));
  double Smax = *(max_element(Sv.begin(), Sv.end()));

  QCPGraph *areaGraph, *stsGraph;
  if (plotWdg->graphCount() == 0) {

    QColor areaPen(0, 0, 100);
    QColor stsPen(82, 5, 5);

    areaGraph = plotWdg->addGraph();
    areaGraph->setPen(QPen(areaPen));
    //areaPen.setAlpha(20);
    //areaGraph->setBrush(QBrush(areaPen));

    stsGraph = plotWdg->addGraph();
    stsGraph->setPen(QPen(stsPen));
    stsPen.setAlpha(20);
    stsGraph->setBrush(QBrush(stsPen));
  } else {
    areaGraph = plotWdg->graph(0);
    stsGraph = plotWdg->graph(1);
  }

  areaGraph->setData(xp, Sp);
  stsGraph->setData(xp, Spi);

  plotWdg->xAxis->setRange( xmin, xmax );
  plotWdg->yAxis->setRange( 0.0, Smax + 0.1*(Smax-Smin));
  plotWdg->replot();
}

void WaveDragDlg::changeEvent(QEvent *e)
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
