
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
 
#include "transformdlg.h"
#include "ui_transformdlg.h"
#include <genua/trafo.h>

#define RO_XYZ  0
#define RO_XZY  1
#define RO_YXZ  2
#define RO_YZX  3
#define RO_ZXY  4
#define RO_ZYX  5

TransformDlg::TransformDlg(QWidget *parent, PointList<3> & pts) :
    QDialog(parent, Qt::Tool), vtx(pts),
    m_ui(new Ui::TransformDlg)
{
  m_ui->setupUi(this);

  // set rotation ordering options
  QString rtx[6];
  rtx[RO_XYZ] = "RX-RY-RZ";
  rtx[RO_XZY] = "RX-RZ-RY";
  rtx[RO_YXZ] = "RY-RX-RZ";
  rtx[RO_YZX] = "RY-RZ-RX";
  rtx[RO_ZXY] = "RZ-RX-RY";
  rtx[RO_ZYX] = "RZ-RY-RX";

  for (int k=0; k<6; ++k)
     m_ui->cbRotateMode->addItem(rtx[k]);

  connect(m_ui->pbApply, SIGNAL(clicked()), this, SLOT(apply()));

  unity(lasttfm);
  adjustSize();
}

TransformDlg::~TransformDlg()
{
  delete m_ui;
}

void TransformDlg::apply()
{
  Transformer trafo;

  if (m_ui->rbScale->isChecked()) {
    trafo.scale( m_ui->sbScale->value() );
  } else if (m_ui->rbRotate->isChecked()) {

    Real rx = rad(m_ui->sbRotX->value());
    Real ry = rad(m_ui->sbRotY->value());
    Real rz = rad(m_ui->sbRotZ->value());

    switch (m_ui->cbRotateMode->currentIndex()) {
      case RO_XYZ:
        trafo.rotate(rx, 0.0, 0.0);
        trafo.rotate(0.0, ry, 0.0);
        trafo.rotate(0.0, 0.0, rz);
        break;
      case RO_XZY:
        trafo.rotate(rx, 0.0, 0.0);
        trafo.rotate(0.0, 0.0, rz);
        trafo.rotate(0.0, ry, 0.0);
        break;
      case RO_YXZ:
        trafo.rotate(0.0, ry, 0.0);
        trafo.rotate(rx, 0.0, 0.0);
        trafo.rotate(0.0, 0.0, rz);
        break;
      case RO_YZX:
        trafo.rotate(0.0, ry, 0.0);
        trafo.rotate(0.0, 0.0, rz);
        trafo.rotate(rx, 0.0, 0.0);
        break;
      case RO_ZXY:
        trafo.rotate(0.0, 0.0, rz);
        trafo.rotate(rx, 0.0, 0.0);
        trafo.rotate(0.0, ry, 0.0);
        break;
      case RO_ZYX:
        trafo.rotate(0.0, 0.0, rz);
        trafo.rotate(0.0, ry, 0.0);
        trafo.rotate(rx, 0.0, 0.0);
        break;
    }
  } else if (m_ui->rbTranslate->isChecked()) {
    Real tx = m_ui->sbTransX->value();
    Real ty = m_ui->sbTransY->value();
    Real tz = m_ui->sbTransZ->value();
    trafo.translate(tx, ty, tz);
  }

  SMatrix<4,4> t = trafo.trafoMatrix();
  const int n = vtx.size();
#pragma omp parallel for
  for (int i=0; i<n; ++i) {
    Vct3 p;
    const Vct3 & v = vtx[i];
    for (int k=0; k<3; ++k)
      p[k] = t(k,3) + t(k,0)*v[0] + t(k,1)*v[1] + t(k,2)*v[2];
    vtx[i] = p;
  }
  lasttfm = t;

  emit geometryChanged();
}

void TransformDlg::revert()
{

}

void TransformDlg::changeEvent(QEvent *e)
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
