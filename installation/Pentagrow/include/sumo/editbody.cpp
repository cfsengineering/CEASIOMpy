
/* ------------------------------------------------------------------------
 * file:       editbody.cpp
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog for editing body properties
 * ------------------------------------------------------------------------ */

#include <string>
#include <QLineEdit>
#include <QCheckBox>
#include <QColorDialog>

#include "util.h"
#include "editbody.h"
#include "endcapdlg.h"
#include "bodyskeleton.h"

using namespace std;

DlgEditBody::DlgEditBody(QWidget *parent, BodySkeletonPtr b) : 
    QDialog(parent), bsp(b) 
{
  setupUi( this );
  retranslateUi( this );
  
  // fill-in existing fields
  leName->setText(bsp->name().c_str());

  Real hmax, wmax, len;
  const Vct3 & org(bsp->origin());
  bsp->dimensions(hmax, wmax, len);
  
  adapt(sbPosX, org[0]);
  adapt(sbPosY, org[1]);
  adapt(sbPosZ, org[2]);
  
  adapt(sbHeight, hmax);
  adapt(sbWidth, wmax);
  adapt(sbLength, len);
  
  // sbFrontCap->setValue( bsp->southCapHeight() );
  // sbRearCap->setValue( bsp->northCapHeight() );
  
  cbVisible->setChecked(bsp->visible());
  cbKeepStraight->setChecked(bsp->keepStraightSegments());
  
  connect(pbChangeColor, SIGNAL(clicked()), 
          this, SLOT(changeColor()));
  connect(pbApply, SIGNAL(clicked()), 
          this, SLOT(changeBody()));
  connect(pbOk, SIGNAL(clicked()), 
          this, SLOT(changeBody()));

  connect(pbEndCaps, SIGNAL(clicked()), this, SLOT(editCaps()));
}

void DlgEditBody::changeBody()
{
  Vct3 pos;
  Real hmax, wmax, len;
  Real hnew, wnew, lnew;

  pos[0] = sbPosX->value();
  pos[1] = sbPosY->value();
  pos[2] = sbPosZ->value();
  hnew = sbHeight->value();
  wnew = sbWidth->value();
  lnew = sbLength->value();
  
  string sname = str(leName->text());
  bsp->rename(sname);
  bsp->visible(cbVisible->isChecked());
  bsp->keepStraightSegments(cbKeepStraight->isChecked());
    
  // bsp->southCapHeight( sbFrontCap->value() );
  // bsp->northCapHeight( sbRearCap->value() );
    
  bsp->origin(pos);
  bsp->dimensions(hmax, wmax, len);
  bsp->scale(hnew/hmax, wnew/wmax, lnew/len);
  bsp->interpolate();
  
  emit geometryChanged();
}

void DlgEditBody::changeColor()
{
  Vct4 c( bsp->pgColor() );
  QColor cinit = QColor::fromRgbF(c[0], c[1], c[2]);
  QColor cnew = QColorDialog::getColor(cinit, this);
  cnew.getRgbF(&c[0], &c[1], &c[2]);
  bsp->pgColor(c);
}

void DlgEditBody::editCaps()
{
  EndCapDlg dlg(this);
  dlg.attach(bsp);
  dlg.exec();
}

void DlgEditBody::adapt(QDoubleSpinBox *sb, double v) const
{
  double lgv = ceil( -log10(fabs(v)) );
  sb->setDecimals( max(3, int(lgv+2)) );
  sb->setSingleStep( 0.2*v );
  sb->setValue(v);
}

