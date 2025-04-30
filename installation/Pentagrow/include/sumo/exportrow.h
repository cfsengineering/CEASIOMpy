
/* ------------------------------------------------------------------------
 * file:       exportrow.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Configurable export interface for unigraphics
 * ------------------------------------------------------------------------ */

#ifndef SUMO_EXPORTROW_H
#define SUMO_EXPORTROW_H

#include "ui_dlgexportrow.h"

class Assembly;

/** ROW format export.

  Shows options for export in ROW format and saves text file.

  */
class ExportRow : public QDialog, Ui::DlgExportRow
{
  Q_OBJECT
  
  public:
    
    /// create dialog with reference to model
    ExportRow(const Assembly & m, QWidget *parent);
    
    /// set surface index as active 
    void setSelected(int index);
    
    /// open file dialog and save result
    void store();
    
  public slots:
    
    /// activated when selected surface changed 
    void changeSurface(int index);
    
  private:
    
    /// surface to export
    const Assembly & msf;
    
    /// directory to remember
    QString lastdir;
};

#endif
