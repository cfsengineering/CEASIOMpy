
/* ------------------------------------------------------------------------
 * file:       mgenprogressctrl.cpp
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Progress and interruption handler for mesh generation procedure
 * ------------------------------------------------------------------------ */

#include <QApplication>
#include <QProgressDialog>

#include "assembly.h"
#include "mgenprogressctrl.h"

using namespace std;

MGenProgressCtrl::MGenProgressCtrl(QWidget *parent, const Assembly & asy) : MgProgressCtrl()
{
  // construct message names
  int nasy = asy.ncomponents();
  for (int i=0; i<nasy; ++i)
    snames << QString::fromStdString( asy.sumoComponent(i)->name() );

  msg << QObject::tr("Initializing mesh generator...");
  
  for (int i=0; i<nasy; ++i)
    msg << (QObject::tr("Premeshing ") + snames.at(i) + QObject::tr(", generating caps...")); 
  
  msg << QObject::tr("Appending components to intersector...");
  msg << QObject::tr("Computing intersection lines...");
  msg << QObject::tr("Constructing intersection line topology...");
  
  for (int i=0; i<nasy; ++i) {
    for (int k=0; k<3; ++k)
      msg << (QObject::tr("Refining component ") + snames.at(i)); 
  }
  
  msg << QObject::tr("Merging component meshes...");
  msg << QObject::tr("Removing duplicated vertices...");
  // msg << QObject::tr("Dropping singly connected elements...");
  msg << QObject::tr("Removing internal elements...");
  msg << QObject::tr("Erasing vertices with edge degree 3...");
  msg << QObject::tr("Removing stretched triangles...");
  msg << QObject::tr("Surface mesh generation completed.");
  
  QString label = QObject::tr("Mesh generation progress");
  QString btext = QObject::tr("&Abort");
  dlg = new QProgressDialog(label, btext, 0, msg.size(), parent);

  dlg->setMinimumDuration(0);
  dlg->setValue(0);
  dlg->setVisible(true);
  dlg->raise();
  dlg->setFocus();
  
  QObject::connect( this, SIGNAL(updateNeeded()), this, SLOT(updateProgress()) );
}
    
MGenProgressCtrl::~MGenProgressCtrl()
{
  dlg->close();
  delete dlg;
}
    
void MGenProgressCtrl::inc(uint k)
{
  guard.lock();
  step += k;
  // qApp->processEvents();
  guard.unlock();
  emit updateNeeded();
}

void MGenProgressCtrl::updateProgress()
{
  int p = MgProgressCtrl::progress();
  if (p == lus)
    return;
  
  dlg->setValue( p );
  // dlg->setLabelText( msg.at( min(p, msg.size()-1) ) );
  
  dlg->setLabelText( QString("Step %1 of %2").arg(step).arg(nstep) );
  
  if (dlg->wasCanceled()) {
    interrupt(true);
    dlg->setLabelText("Aborting mesh generation...");
  }
  qApp->processEvents();
  
  lus = step;
}
    
void MGenProgressCtrl::nsteps(uint n)
{
  MgProgressCtrl::nsteps(n);
  dlg->setRange(0, n);
  dlg->setValue(0);
  dlg->setLabelText( msg.at(0) );
  lus = 0;
}
