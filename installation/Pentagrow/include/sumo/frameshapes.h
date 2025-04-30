
/* ------------------------------------------------------------------------
 * file:       frameshapes.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog: Fit body section to special shape function 
 * ------------------------------------------------------------------------ */

#ifndef SUMO_FRAMESHAPES_H
#define SUMO_FRAMESHAPES_H

#ifndef Q_MOC_RUN
#include "bodyframe.h"
#include "bodyskeleton.h"
#include "frameshapeconstraint.h"
#endif
#include "ui_dlgframeshapes.h"


/** Select frame shape constraints.

  This dialog presents a choice of anlytical cross section shapes which 
  can be enforced upon body frames.

*/
class FrameShapes : public QDialog, public Ui::DlgFrameShapes
{
  Q_OBJECT
  
  public:
  
    /// create a dialog to edit shape of *bfp
    FrameShapes(QWidget *parent, BodySkeletonPtr sp, BodyFramePtr bp);

  private slots:
    
    /// switch type of constraint 
    void changeConstraintType();
    
    /// set constraint parameter
    void changeParameter();
    
    /// apply change to frame
    void applyConstraint();
    
  signals:
    
    /// notify higher level widgets of shape changes
    void frameShapeChanged();
    
  private:
    
    /// set fields from frame
    void fillFields();
    
    /// adapt spin box settings to value
    void adapt(QDoubleSpinBox *sb, double v) const;
    
  private:
    
    /// skeleton to update
    BodySkeletonPtr bsp;
    
    /// frame to change
    BodyFramePtr bfp;
        
    /// working copy of frame constraint
    ShapeConstraintPtr scp;
};

#endif
