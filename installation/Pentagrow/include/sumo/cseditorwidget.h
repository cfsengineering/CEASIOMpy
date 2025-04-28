
/* ------------------------------------------------------------------------
 * file:       cseditorwidget.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Modeless control surface editor
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CSEDITORWIDGET_H
#define SUMO_CSEDITORWIDGET_H

#include <QDialog>

#include "ui_dlgdefinecontrol.h"
#ifndef Q_MOC_RUN
#include "ctsystem.h"
#endif

class QDoubleValidator;

/**
  */
class CsEditorWidget : public QDialog, private Ui::DlgDefineControl
{
  Q_OBJECT
  
  public:
    
    /// create editor with reference to control system
    CsEditorWidget(QWidget *parent, Assembly & a);
    
    /// destroy 
    virtual ~CsEditorWidget();
    
  public slots:  
  
    /// switch off control system visualization
    virtual bool close();
    
  private slots:
    
    /// fill in data for hingepoint i 
    void showHingepoint(int i);
    
    /// add hinge point 
    void addHingepoint();
    
    /// modify hinge point 
    void changeHingepoint();
    
    /// insert data of surface i into table
    void showFlap(int i);
    
    /// create a new default control surface
    void newFlap();
    
    /// create a mirror copy of the current surface
    void mirrorFlap();
    
    /// delete current control surface
    void deleteFlap();
    
    /// change LEF/TEF status 
    void changeFlapType();
    
    /// called to change flap name 
    void renameFlap(const QString &s);
    
    /// change wing of current surface
    void changeWing(int iw);
    
    /// fill pattern table fields
    void showPattern(int i);
    
    /// change pattern coefficient
    void changePattern(int row, int col);
    
    /// create a new default control pattern
    void newPattern();
    
    /// delete current control pattern
    void deletePattern();
    
    /// change pattern name 
    void renamePattern(const QString &s);
    
    /// user switched tabs 
    void tabChanged(int itab);
    
  signals:
    
    /// emitted when 3D view needs redrawing
    void geometryChanged();
    
  private:
    
    /// reset display 
    void init();
    
  private:
    
    /// assembly to use 
    Assembly & asy;
    
    /// indicates that showXXX() is running 
    bool showing;
    
    /// validators for hinge position fields 
    QDoubleValidator *hpval;
};

#endif

