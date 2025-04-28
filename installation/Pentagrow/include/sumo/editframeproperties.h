
/* ------------------------------------------------------------------------
 * file:       editframeproperties.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Change frame properties
 * ------------------------------------------------------------------------ */

#ifndef SUMO_EDITFRAMEPROPERTIES_H
#define SUMO_EDITFRAMEPROPERTIES_H

#ifndef Q_MOC_RUN
#include "bodyskeleton.h"
#include "bodyframe.h"
#endif
#include "ui_dlgeditframe.h"

/** Modify simple frame properties */
class EditFrameProperties : public QDialog, public Ui::DlgEditFrame
{
  Q_OBJECT
  
  public:
    
    /// create default dialog
    EditFrameProperties(QWidget *parent, BodySkeletonPtr sp, BodyFramePtr bp);
    
    /// set another frame
    void setFrame(BodyFramePtr bp);
    
  private slots:
    
    /// open a shape constraint dialog
    void shapeDialog();
    
    /// perform shape changes
    void changeShape();
    
    /// fill fields with frame values
    void fillFields();
    
  signals:
    
    /// notify higher level widgets of shape changes
    void frameShapeChanged();
    
    /// ask for the previous frame
    void previousFramePlease();
    
    /// ask for the next frame
    void nextFramePlease();
    
  private:
    
    /// adapt spin box settings to value
    void adapt(QDoubleSpinBox *sb, double v) const;
    
  private:
    
    /// body which changes with frame modification
    BodySkeletonPtr bsp;
    
    /// frame to modify
    BodyFramePtr bfp;
};

#endif
