
/* ------------------------------------------------------------------------
 * file:       wingmanagerwidget.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Manages user input for wing skeleton modification
 * ------------------------------------------------------------------------ */

#ifndef SUMO_WINGMANAGERWIDGET_H
#define SUMO_WINGMANAGERWIDGET_H

#include "ui_dlgeditwing.h"
#include "forward.h"

class WingManagerWidget : public QDialog, public Ui::DlgEditWing
{
  Q_OBJECT
  
  public:

    /// create widget and setup
    WingManagerWidget(QWidget *parent, WingSkeletonPtr sp);
    
    /// destroy
    ~WingManagerWidget() {}

  public slots:

    /// create a new section and open a section edit dialog
    void newSection();
      
    /// open a section edit dialog
    void editSection();

    /// remove selected section
    void removeSection();

    /// activated section changed
    void sectionSelectionChanged(int isec);

    /// apply heuristic sorting to list of sections
    void sortSections();

    /// move currently selected section up one entry
    void moveSectionUp();

    /// move currently selected section down one entry
    void moveSectionDown();

    /// update list of sections
    void updateList();

    /// rebuild wing after changes have been applied 
    void rebuildWing();
    
    /// automatic symmetry, WL detection, cubic flag switched on/off 
    void buildFlagSwitched(bool f);
    
    /// apply remaining changes and close
    void saveAndClose();
    
    /// change surface color 
    void changeColor();
    
    /// show statistics 
    void showStats();
    
  signals:

    /// emitted whenever the wing skeleton is interpolated again
    void geometryChanged();

  private:

    /// retrieve selected section entry
    uint selectedSection();
    
    /// adapt range and step for spin box
    void adapt(QDoubleSpinBox *sb, double v) const;
    
  private:

    /// wing to modify
    WingSkeletonPtr wsp;
};

#endif

