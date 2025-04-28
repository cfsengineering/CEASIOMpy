
/* ------------------------------------------------------------------------
 * file:       sectioneditor.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog for wing section properties
 * ------------------------------------------------------------------------ */

#ifndef SUMO_SECTIONEDITOR_H
#define SUMO_SECTIONEDITOR_H

#include "forward.h"
#include "ui_dlgeditsection.h"

/** Dialog for wing section properties.
  */
class SectionEditor : public QDialog, public Ui::DlgEditSection
{
  Q_OBJECT
  
  public:
    
    /// construct dialog widget, fill data fields
    SectionEditor(QWidget *parent, WingSectionPtr w);
    
    /// destructor
    ~SectionEditor() {}
    
    /// apply changes to wing section
    bool process();
    
    /// show error message if section generation failed
    void naca6error(int code);
    
  public slots:
    
    /// open a file dialog and try to load coordinates
    bool loadCoordinates();
    
    /// open a dialog for coordinate generation
    bool genCoordinates();
    
    /// save section coordinates to plain text file
    void saveCoordinates();

  private:
    
    /// pointer to wing section to process
    WingSectionPtr wsp;
    
    /// last directory where airfoils were loaded from 
    static QString lastdir;
};

#endif
