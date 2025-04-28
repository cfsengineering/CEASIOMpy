
/* ------------------------------------------------------------------------
 * file:       meshdrawoptions.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Modify settings for TriMeshView
 * ------------------------------------------------------------------------ */

#ifndef SUMO_MESHDRAWOPTIONS_H
#define SUMO_MESHDRAWOPTIONS_H

#include "ui_dlgdrawoptions.h"

class TriMeshView;

/** Modify settings for TriMeshView
*/
class MeshDrawOptions : public QDialog, public Ui::DlgDrawOptions
{
  Q_OBJECT
  
  public:
  
    /// setup dialog
    MeshDrawOptions(TriMeshView *v);

    /// run non-modal dialog on its own
    void execute();
 
  private slots:
    
    /// apply geometry changes
    void applyChanges();
    
  private:
    
    /// modify settings on this one
    TriMeshView *tmv;
};

#endif
