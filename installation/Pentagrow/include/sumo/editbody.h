
/* ------------------------------------------------------------------------
 * file:       editbody.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog for editing body properties
 * ------------------------------------------------------------------------ */

#ifndef SUMO_EDITBODY_H
#define SUMO_EDITBODY_H

#include "forward.h"
#include "ui_dlgeditbody.h"

/**
  */
class DlgEditBody : public QDialog, private Ui::DlgEditBody
{
  Q_OBJECT
  
  public:
    
    /// setup dialog fields for body b
    DlgEditBody(QWidget *parent, BodySkeletonPtr b);
    
  signals:
    
    /// emit whenever the geometry was changed
    void geometryChanged();
    
  private slots:
    
    /// modify surface color 
    void changeColor();
    
    /// apply geometry changes
    void changeBody();
    
    /// launch cap editor
    void editCaps();

  private:
    
    /// adapt range and step for spin box
    void adapt(QDoubleSpinBox *sb, double v) const;
    
  private:
    
    /// pointer to body to edit 
    BodySkeletonPtr bsp;
};

#endif
