
/* ------------------------------------------------------------------------
 * file:       dlgsavemesh.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Display mesh details
 * ------------------------------------------------------------------------ */

#ifndef SUMO_DLGSAVEMESH_H
#define SUMO_DLGSAVEMESH_H

#include "ui_dlgsavemesh.h"

class SumoMain;
class TriMesh;

class DlgSaveMesh : public QDialog, public Ui::DlgSaveMesh
{
  Q_OBJECT
  
  public:
    
    /// construct dialog 
    DlgSaveMesh(SumoMain *parent, const TriMesh & tg);
    
  private slots:
    
    /// show message box
    void showMessage(const QString & link);
    
  private:
    
    /// pointer to main window
    SumoMain *pMain;
    
    /// message for info box
    QString msg;
};

#endif
