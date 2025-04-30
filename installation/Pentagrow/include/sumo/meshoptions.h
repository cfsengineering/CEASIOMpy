
/* ------------------------------------------------------------------------
 * file:       meshoptions.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Front-end for mesh generation facilities
 * ------------------------------------------------------------------------ */

#ifndef SUMO_MESHOPTIONS_H
#define SUMO_MESHOPTIONS_H

#include "ui_dlgmeshoptions.h"

class Assembly;
class Meshable;

class MeshOptions : public QDialog, public Ui::DlgMeshOptions
{
  Q_OBJECT
  
  public:
    
    /// initialize dialog
    MeshOptions(QWidget *parent, Assembly & a);
    
  private slots:
    
    /// display settings for surface i
    void showSettings(int i) const;
    
    /// update mesh generation properties after user change
    void mgValueChanged();
    
    /// enforce default settings
    void mgSetDefaults(bool flag);

    /// set defaults for all surfaces
    void mgSetAllDefaults(bool flag);
    
    /// set coarse mesh flag
    void mgSetCoarse(bool flag);
    
  private:
    
    /// adapt range and step for spin box
    void adapt(QDoubleSpinBox *sb, double v, double rstep=0.2) const;
    
  private:
    
    /// assembly to change
    Assembly & asy;
};

#endif
