
/* ------------------------------------------------------------------------
 * file:       mgenprogressctrl.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Progress and interruption handler for mesh generation procedure
 * ------------------------------------------------------------------------ */

#ifndef SUMO_MGENPROGRESSCTRL_H
#define SUMO_MGENPROGRESSCTRL_H

#include <QString>
#include <QStringList>
#include <QObject>
#ifndef Q_MOC_RUN
#include "forward.h"
#include <surf/meshgenerator.h>
#endif

class Assembly;
class QProgressDialog;

/**
*/
class MGenProgressCtrl : public QObject, public MgProgressCtrl
{
  Q_OBJECT
  
  public:
    
    /// initialize progress controller 
    MGenProgressCtrl(QWidget *parent, const Assembly & asy);
    
    /// destroy dialog explicitely
    virtual ~MGenProgressCtrl();
    
    /// log steps as complete
    void inc(uint k=1);
    
    /// register number of steps to perform
    void nsteps(uint n);
    
  private slots:
    
    /// update progress dialogue
    void updateProgress();
    
  signals:
    
    void updateNeeded();
    
  private:
    
    /// step at which we last updated
    int lus;
    
    /// progress dialog
    QProgressDialog *dlg;
    
    /// messages to display
    QStringList snames, msg;
};



#endif
