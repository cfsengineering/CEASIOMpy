
/* ------------------------------------------------------------------------
 * file:       frameshapes.cpp
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog: Fit body section to special shape function 
 * ------------------------------------------------------------------------ */

#include "frameshapes.h"

using namespace std;
using boost::dynamic_pointer_cast;

FrameShapes::FrameShapes(QWidget *parent, 
                         BodySkeletonPtr sp, 
                         BodyFramePtr bp) : QDialog(parent), bsp(sp), bfp(bp)
{
  // create user interface
  setupUi(this);
  retranslateUi(this);

  connect(pbApply, SIGNAL(clicked()), this, SLOT(applyConstraint()));
  connect(pbOK, SIGNAL(clicked()), this, SLOT(applyConstraint()));
  
  connect(rbNoConstraints, SIGNAL(released()), this, SLOT(changeConstraintType()));
  connect(rbCircular, SIGNAL(released()), this, SLOT(changeConstraintType()));
  connect(rbSuperellipse, SIGNAL(released()), this, SLOT(changeConstraintType()));
  connect(rbDoubleEllipse, SIGNAL(released()), this, SLOT(changeConstraintType()));
  connect(rbCubicEgg, SIGNAL(released()), this, SLOT(changeConstraintType()));

  connect(sbCircular, SIGNAL(editingFinished()), this, SLOT(changeParameter()));
  connect(sbSuperellipse, SIGNAL(editingFinished()), this, SLOT(changeParameter()));
  connect(sbDoubleEllipse, SIGNAL(editingFinished()), this, SLOT(changeParameter()));
  connect(sbCubicEgg, SIGNAL(editingFinished()), this, SLOT(changeParameter()));

  connect(sbNPoints, SIGNAL(editingFinished()), this, SLOT(changeParameter()));
  
  fillFields();
}
    
void FrameShapes::changeConstraintType()
{
  if (rbNoConstraints->isChecked()) {
    scp.reset();
  } else if (rbCircular->isChecked()) {
    CircularShapeConstraint *psc = new CircularShapeConstraint;
    psc->radius( sbCircular->value() );
    scp = ShapeConstraintPtr(psc);
  } else if (rbSuperellipse->isChecked()) {
    EllipticShapeConstraint *psc = new EllipticShapeConstraint;
    psc->exponent( sbSuperellipse->value() );
    scp = ShapeConstraintPtr(psc);
  } else if (rbDoubleEllipse->isChecked()) {
    DoubleEllipticConstraint *psc = new DoubleEllipticConstraint;
    psc->offset( sbDoubleEllipse->value() );
    scp = ShapeConstraintPtr(psc);
  } else if (rbCubicEgg->isChecked()) {
    HuegelschaefferConstraint *psc = new HuegelschaefferConstraint;
    psc->distortion( sbCubicEgg->value() );
    scp = ShapeConstraintPtr(psc);
  }
}
    
void FrameShapes::changeParameter()
{
  if (rbNoConstraints->isChecked()) {
    scp.reset();
  } else if (rbCircular->isChecked()) {
    CircularConstraintPtr psc;
    psc = dynamic_pointer_cast<CircularShapeConstraint>( scp );
    assert(psc);
    if (psc)
      psc->radius( sbCircular->value() );
    adapt(sbCircular, sbCircular->value());
  } else if (rbSuperellipse->isChecked()) {
    EllipticConstraintPtr psc;
    psc = dynamic_pointer_cast<EllipticShapeConstraint>( scp );
    assert(psc);
    if (psc)
      psc->exponent( sbSuperellipse->value() );
  } else if (rbDoubleEllipse->isChecked()) {
    DoubleEllipticConstraintPtr psc;
    psc = dynamic_pointer_cast<DoubleEllipticConstraint>( scp );
    assert(psc);
    if (psc)
      psc->offset( sbDoubleEllipse->value() );
  } else if (rbCubicEgg->isChecked()) {
    HuegelschaefferConstraintPtr psc;
    psc = dynamic_pointer_cast<HuegelschaefferConstraint>( scp );
    assert(psc);
    if (psc)
      psc->distortion( sbCubicEgg->value() );
  }
  
  if (scp) {
    scp->npoints( sbNPoints->value() );
  }
}
    
void FrameShapes::applyConstraint()
{
  if (scp) {
    changeParameter();
    bfp->shapeConstraint(scp);
    bsp->interpolate();
    emit frameShapeChanged();
  } else {
    bfp->eraseConstraint();
  }
}

void FrameShapes::fillFields()
{
  Real r = 0.5*(bfp->frameWidth() + bfp->frameHeight());
  adapt(sbCircular, r);
  
  ShapeConstraintPtr s = bfp->shapeConstraint();
  
  if (s)
    sbNPoints->setValue( s->npoints() );
  else
    return;
  
  {
    CircularConstraintPtr psc;
    psc = dynamic_pointer_cast<CircularShapeConstraint>(s);
    if (psc) {
      scp = s;
      rbCircular->setChecked(true);
      sbCircular->setValue( psc->radius() );
      return;
    } 
  }
  
  {
    EllipticConstraintPtr psc;
    psc = dynamic_pointer_cast<EllipticShapeConstraint>(s);
    if (psc) {
      scp = s;
      rbSuperellipse->setChecked(true);
      sbSuperellipse->setValue( psc->exponent() );
      return;
    } 
  }
  
  {
    DoubleEllipticConstraintPtr psc;
    psc = dynamic_pointer_cast<DoubleEllipticConstraint>(s);
    if (psc) {
      scp = s;
      rbDoubleEllipse->setChecked(true);
      sbDoubleEllipse->setValue( psc->offset() );
      return;
    } 
  }
  
  {
    HuegelschaefferConstraintPtr psc;
    psc = dynamic_pointer_cast<HuegelschaefferConstraint>(s);
    if (psc) {
      scp = s;
      rbCubicEgg->setChecked(true);
      sbCubicEgg->setValue( psc->distortion() );
      return;
    } 
  }
}

void FrameShapes::adapt(QDoubleSpinBox *sb, double v) const
{
  double lgv = ceil( -log10(fabs(v)) );
  sb->setDecimals( max(1, int(lgv+2)) );
  sb->setSingleStep( 0.2*v );
  sb->setValue(v);
}
