
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
 
#include "transformationdialog.h"
#include <iostream>

using namespace std;

TransformationDialog::TransformationDialog(QWidget *parent) :
  QDialog(parent)
{
  setupUi(this);
  useModal(false);

  connect(rbAbsolute, SIGNAL(toggled(bool)),
          this, SLOT(displayAbsolute(bool)));
  connect(pbApply, SIGNAL(clicked()),
          this, SLOT(apply()));

  adjustSize();
}

void TransformationDialog::assign(MxMeshPtr msh)
{
  pmx = msh;
  gbMeshScope->setVisible( pmx != nullptr );
  adjustSize();
}

void TransformationDialog::enableRotation(bool flag)
{
  gbRotation->setEnabled(flag);
  gbPivot->setEnabled(flag);
}

void TransformationDialog::enableTranslation(bool flag)
{
  gbTranslation->setEnabled(flag);
}

void TransformationDialog::useModal(bool modal)
{
  if (modal) {
    pbApply->hide();
    pbOk->show();
  } else {
    pbApply->show();
    pbOk->hide();
  }
}

void TransformationDialog::setTrafo(const Trafo3d & t)
{
  trafo = t;
  displayAbsolute( rbAbsolute->isChecked() );
}

void TransformationDialog::displayAbsolute(bool flag)
{
  if (flag) {

    const Vct3 & rot( trafo.rotation() );
    const Vct3 & trn( trafo.translation() );
    const Vct3 & scl( trafo.scaling() );
    const Vct3 & piv( trafo.pivot() );

    sbRotX->setValue( deg(rot[0]) );
    sbRotY->setValue( deg(rot[1]) );
    sbRotZ->setValue( deg(rot[2]) );

    sbPivotX->setValue( piv[0] );
    sbPivotY->setValue( piv[1] );
    sbPivotZ->setValue( piv[2] );

    sbTransX->setValue( trn[0] );
    sbTransY->setValue( trn[1] );
    sbTransZ->setValue( trn[2] );

    sbScaleFactor->setValue( scl[0] );

  } else {

    sbRotX->setValue( 0.0 );
    sbRotY->setValue( 0.0 );
    sbRotZ->setValue( 0.0 );

    sbPivotX->setValue( 0.0 );
    sbPivotY->setValue( 0.0 );
    sbPivotZ->setValue( 0.0 );

    sbTransX->setValue( 0.0 );
    sbTransY->setValue( 0.0 );
    sbTransZ->setValue( 0.0 );

    sbScaleFactor->setValue( 1.0 );

  }
}

void TransformationDialog::apply()
{
  Vct3 rot, trn, piv, scl;

  rot[0] = rad(sbRotX->value());
  rot[1] = rad(sbRotY->value());
  rot[2] = rad(sbRotZ->value());

  piv[0] = sbPivotX->value();
  piv[1] = sbPivotY->value();
  piv[2] = sbPivotZ->value();

  trn[0] = sbTransX->value();
  trn[1] = sbTransY->value();
  trn[2] = sbTransZ->value();

  scl[0] = scl[1] = scl[2] = sbScaleFactor->value();

  if (rbAbsolute->isChecked()) {
    trafo.scale(scl[0], scl[1], scl[2]);
    trafo.pivot(piv);
    trafo.rotate(rot[0], rot[1], rot[2]);
    trafo.translate(trn[0], trn[1], trn[2]);
  } else {
    Trafo3d tmp;
    tmp.scale(scl[0], scl[1], scl[2]);
    tmp.rotate(rot[0], rot[1], rot[2]);
    tmp.translate(trn[0], trn[1], trn[2]);
    trafo.prepend(tmp);
  }

  if (pmx) {
    if (cbTransformNodes->isChecked())
      trafo.transformList( pmx->nodes() );
    if (cbTransformFields->isChecked()) {
#pragma omp parallel for schedule(dynamic,1)
      for (int i=0; i<int(pmx->nfields()); ++i)
        pmx->field(i).transform( trafo );
    }
  }

  emit trafoChanged();
}

void TransformationDialog::changeEvent(QEvent *e)
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
