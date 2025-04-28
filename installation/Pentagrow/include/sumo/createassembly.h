
/* ------------------------------------------------------------------------
 * file:       createassembly.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog to select template or load from file
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CREATEASSEMBLY_H
#define SUMO_CREATEASSEMBLY_H

#include "ui_dlgcreateassembly.h"
#include "forward.h"
#include <QDialog>

/**
*/
class CreateAssembly : public QDialog, private Ui::DlgCreateAssembly
{
  Q_OBJECT
  
  public:
    
    /// setup dialog
    CreateAssembly(QWidget *parent);
    
    /// set last directory
    void setLastDir(const QString & s) {lastdir = s;}
    
    /// true if user selected template 
    bool useTemplate() const;
    
    /// name of file to load otherwise 
    const QString & file() const {return filename;}
    
    /// access selected assembly
    AssemblyPtr create();
   
  private slots:
    
    /// browse for file and check file format 
    void browse();
    
  private:
    
    /// from file
    QString lastdir, filename;
};

#endif
