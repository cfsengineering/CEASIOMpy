
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
 
#include "meshqualitydialog.h"
#include "plotcontroller.h"
#include "meshplotter.h"
#include <genua/mxelementfunction.h>
#include <QTextStream>

MeshQualityDialog::MeshQualityDialog(QWidget *parent) :
  QDialog(parent), m_plc(0)
{
  setupUi(this);

#ifdef Q_OS_MACX
  gbCriteria->setFlat(true);
  gbResults->setFlat(true);
#endif

  connect( pbShow, SIGNAL(clicked()), this, SLOT(displayElements()) );
  connect( pbHide, SIGNAL(clicked()), this, SLOT(hideElements()) );

  gbResults->hide();
  adjustSize();
}

void MeshQualityDialog::assign(PlotController *plc)
{
  m_plc = plc;
  gbResults->hide();
  adjustSize();
}

void MeshQualityDialog::displayElements()
{
  if (m_plc == 0)
    return;

  MeshPlotterPtr mp = m_plc->plotter();
  if (not mp)
    return;

  MxMeshPtr pmx = mp->pmesh();
  if (not pmx)
    return;

  int ntangled(0), nmind(0), nmaxd(0);
  Indices gix;
  if ( cbDisplayTangled->isChecked() ) {
    MxTangledElement ef( pmx.get() );
    ef.elementsBelow(0.5, gix);
    ntangled = gix.size();
  }

  if ( cbDisplayTets->isChecked() ) {
    MxMinDihedralAngle fmin( pmx.get() );
    fmin.elementsBelow( rad(sbMinDihedral->value()), gix );
    nmind = gix.size() - ntangled;
    MxMaxDihedralAngle fmax( pmx.get() );
    fmax.elementsAbove( rad(sbMaxDihedral->value()), gix );
    nmaxd = gix.size() - nmind - ntangled;
  }
  postMessage(tr("%1 tangled elements, %2 sliver, %3 blunt tets.")
              .arg(ntangled).arg(nmind).arg(nmaxd));

  lbNoTangled->setText( QString::number(ntangled) );
  lbNoBadTets->setText( QString::number(nmind+nmaxd) );
  listBadElements(gix);
  if (not gbResults->isVisible()) {
    gbResults->show();
    adjustSize();
  }

  mp->displayVolumeElements(gix, true);
  emit requestRepaint();
}

void MeshQualityDialog::hideElements()
{
  if (m_plc == 0)
    return;

  MeshPlotterPtr mp = m_plc->plotter();
  if (not mp)
    return;

  mp->clearVolumeElements();
  txtElementList->clear();
  emit requestRepaint();
}

void MeshQualityDialog::listBadElements(const Indices &elx)
{
  if (m_plc == 0)
    return;

  MxMeshPtr pmx = m_plc->pmesh();
  if (not pmx)
    return;

  QString txt;
  QTextStream stream(&txt);
  for (size_t i=0; i<elx.size(); ++i) {
    uint nv, isec;
    const uint *v = pmx->globalElement(elx[i], nv, isec);
    stream << Mx::str( pmx->section(isec).elementType() ).c_str();
    stream << "  " << elx[i] << endl;
    for (uint j=0; j<nv; ++j) {
      stream << "   " << v[j] << " :  " << str(pmx->node(v[j])).c_str() << endl;
    }
  }

  txtElementList->clear();
  txtElementList->setText( txt );
}

void MeshQualityDialog::changeEvent(QEvent *e)
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
