
/* ------------------------------------------------------------------------
 * file:       editframeproperties.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Change frame properties
 * ------------------------------------------------------------------------ */

#include "frameshapes.h"
#include "util.h"
#include "editframeproperties.h"

using namespace std;

EditFrameProperties::EditFrameProperties(QWidget *parent, 
                                         BodySkeletonPtr sp, BodyFramePtr bp)
  : QDialog(parent), bsp(sp), bfp(bp)
{
  setupUi(this);
  retranslateUi(this);
  
  fillFields();
  
  connect(pbShapes, SIGNAL(clicked()), this, SLOT(shapeDialog()));
  connect(pbApply, SIGNAL(clicked()), this, SLOT(changeShape()));
  connect(pbOK, SIGNAL(clicked()), this, SLOT(changeShape()));
  connect(this, SIGNAL(frameShapeChanged()), this, SLOT(fillFields()) );
  connect(pbPrevious, SIGNAL(clicked()), this, SIGNAL(previousFramePlease()));
  connect(pbNext, SIGNAL(clicked()), this, SIGNAL(nextFramePlease()));
}

void EditFrameProperties::setFrame(BodyFramePtr bp)
{
  bfp = bp;
  fillFields();
}

void EditFrameProperties::changeShape()
{
  Vct3 pos;
  pos[0] = sbPosX->value();
  pos[1] = sbPosY->value();
  pos[2] = sbPosZ->value();
  
  bfp->rename( str(leName->text()) );
  bfp->origin(pos);
  bfp->setFrameWidth( sbWidth->value() );
  bfp->setFrameHeight( sbHeight->value() );
  bfp->interpolate();
  bsp->interpolate();
  
  emit frameShapeChanged();
}

void EditFrameProperties::shapeDialog()
{
  changeShape();
  FrameShapes dlg(this, bsp, bfp);
  connect(&dlg, SIGNAL(frameShapeChanged()), this, SIGNAL(frameShapeChanged()));
  dlg.exec();
  disconnect(&dlg, SIGNAL(frameShapeChanged()), this, SIGNAL(frameShapeChanged()));
}

void EditFrameProperties::fillFields()
{
  const Vct3 & org( bfp->origin() );
  adapt(sbPosX, org[0]);
  adapt(sbPosY, org[1]);
  adapt(sbPosZ, org[2]);
  
  adapt(sbHeight, bfp->frameHeight());
  adapt(sbWidth, bfp->frameWidth());
  
  leName->setText( QString::fromStdString(bfp->name()) );
}

void EditFrameProperties::adapt(QDoubleSpinBox *sb, double v) const
{
  double lgv = ceil( -log10( fabs(v) ) );
  sb->setDecimals( max(1, int(lgv+2)) );
  sb->setSingleStep( 0.2*v );
  sb->setValue(v);
}

