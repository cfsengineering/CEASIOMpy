
/* ------------------------------------------------------------------------
 * file:       dlgairfoil.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Updated airfoil dialog
 * ------------------------------------------------------------------------ */

#ifndef SUMO_DLGAIRFOIL_H
#define SUMO_DLGAIRFOIL_H

#include "forward.h"
#include "ui_dlgairfoil.h"

/** Airfoil selection dialog.

*/
class DlgAirfoil : public QDialog, public Ui::DlgAirfoil
{
  Q_OBJECT
  
  public:
    
    /// create dialog and setup
    DlgAirfoil(QWidget* parent);
    
    /// set name to show for current foil 
    void setCurrentAirfoil(const WingSectionPtr & wsp);
    
    /// generate airfoil 
    void setAirfoil(WingSectionPtr wsp) const;
    
    /// remember current settings
    void remember();
    
  public slots:
    
    /// update the airfoil listing when collection changes 
    void updateAirfoilListing(int icol);
    
    /// save airfoil in standard format
    void saveAirfoil();

  private:
    
    /// remember last active settings
    static int ipage, icollection, iairfoil;
    
    /// thickness values 
    static double rpthick, n4thick, n6thick;
    
    /// float settings
    static double n4camber, n4camberpos, n5designcl, n6designcl, n6a;
     
    /// integer settings 
    static int n5meanline, n6family, n6camberline;
};

#endif
