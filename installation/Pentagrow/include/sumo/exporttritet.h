
/* ------------------------------------------------------------------------
 * file:       exporttritet.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog to adjust settings for TRITET boundary mesh export
 * ------------------------------------------------------------------------ */
 
#ifndef SUMO_EXPORTTRITET_H
#define SUMO_EXPORTTRITET_H

#ifndef Q_MOC_RUN
#include <surf/tritetwriter.h>
#endif
#include "ui_dlgxptritet.h"

class Assembly;

/** Export mesh file to TRITET format
*/
class ExportTritet : public QDialog, private Ui::DlgExportTritet
{
  Q_OBJECT
  
  public:
  
    /// initialize with mesh 
    ExportTritet(QWidget *parent, Assembly & mdl);

    /// show dialog and save if OK
    bool execute(const QString & lastdir);
    
  public slots:
    
    /// show number of triangles
    void updateTriangleCount(int nref=0);
    
  private:
    
    /// link to assembly
    Assembly & asy;
    
    /// writer object
    TritetWriter twt;
};

#endif
