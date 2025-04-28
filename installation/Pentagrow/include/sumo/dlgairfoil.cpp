
/* ------------------------------------------------------------------------
 * file:       dlgairfoil.cpp
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Updated airfoil dialog
 * ------------------------------------------------------------------------ */

#include "dlgairfoil.h"
#include "componentlibrary.h"
#include "util.h"
#include <genua/ioglue.h>
#include <surf/airfoilcollection.h>
#include <QFileDialog>

// ----------------- DlgAirfoil ---------------------------------------------

int DlgAirfoil::ipage = 0;
int DlgAirfoil::icollection = 2;
int DlgAirfoil::iairfoil = 0;

double DlgAirfoil::rpthick = 3.0;
double DlgAirfoil::n4thick = 15.0;
double DlgAirfoil::n6thick = 15.0;

double DlgAirfoil::n4camber = 2.0;
double DlgAirfoil::n4camberpos = 30.0;
double DlgAirfoil::n5designcl = 0.5;
double DlgAirfoil::n6designcl = 0.5;
double DlgAirfoil::n6a = 0.6;

int DlgAirfoil::n5meanline = 2;
int DlgAirfoil::n6family = 3;
int DlgAirfoil::n6camberline = 0;

DlgAirfoil::DlgAirfoil(QWidget* parent)  : QDialog(parent) 
{
  setupUi(this);
  retranslateUi(this);
  
  // populate airfoil collection combo box 
  int ncol = SumoComponentLib.nafcollect();
  cbCollection->clear();
  for (int i=0; i<ncol; ++i) 
    cbCollection->addItem( SumoComponentLib.collectionName(i) );
  
  for (int i=1; i<=5; ++i)
    cbSelectMeanline->addItem( QString::number(200 + 10*i) );
  
  // recover remembered settings
  tabWidget->setCurrentIndex( ipage );
  cbCollection->setCurrentIndex( icollection );
  
  sbRpThickness->setValue(rpthick);
  sbN4Thickness->setValue(n4thick);
  sbN6Thickness->setValue(n6thick);
  
  sbN4Camber->setValue(n4camber);
  sbN4CamberPos->setValue(n4camberpos);
  sbN5DesignCL->setValue(n5designcl);
  sbDesignCL1->setValue(n6designcl);
  sbChordLoad1->setValue(n6a);
  
  cbSelectMeanline->setCurrentIndex(n5meanline);
  cbN6Family->setCurrentIndex(n6family);
  cbN6CamberLine->setCurrentIndex(n6camberline);
  
  // setup connections
  connect( cbCollection, SIGNAL(currentIndexChanged(int)),
           this, SLOT(updateAirfoilListing(int)) );
  connect( pbSave, SIGNAL(clicked()),
           this, SLOT(saveAirfoil()) );

  updateAirfoilListing( cbCollection->currentIndex() );
  cbAirfoil->setCurrentIndex( iairfoil );
}

void DlgAirfoil::setCurrentAirfoil(const WingSectionPtr & wsp)
{
  lbAirfoilName->setText( QString::fromStdString(wsp->airfoilName()) );
  sbExtendXLE->setValue( wsp->dxNose() * 100.0 );
  sbExtendYLE->setValue( wsp->dyNose() * 100.0 );
  sbExtendXTE->setValue( wsp->dxTail() * 100.0 );
  sbExtendYTE->setValue( wsp->dyTail() * 100.0 );
}

void DlgAirfoil::remember()
{
  ipage = tabWidget->currentIndex();
  icollection = cbCollection->currentIndex();
  iairfoil = cbAirfoil->currentIndex();
  
  rpthick = sbRpThickness->value();
  n4thick = sbN4Thickness->value();
  n6thick = sbN6Thickness->value();
  
  n4camber = sbN4Camber->value();
  n4camberpos = sbN4CamberPos->value();
  n5designcl = sbN5DesignCL->value();
  n6designcl = sbDesignCL1->value();
  n6a = sbChordLoad1->value();
  
  n5meanline = cbSelectMeanline->currentIndex();
  n6family = cbN6Family->currentIndex();
  n6camberline = cbN6CamberLine->currentIndex();
}

void DlgAirfoil::updateAirfoilListing(int icol)
{
  const AirfoilCollection & afc( SumoComponentLib.collection(icol) );
  
  std::string s( afc.comment() );
  lbCollectionComment->setText( QString::fromUtf8(s.c_str()) );
  cbAirfoil->clear();
  int naf = afc.size();
  for (int i=0; i<naf; ++i)
    cbAirfoil->addItem( QString::fromStdString(afc.coordName(i)) );
}

void DlgAirfoil::setAirfoil(WingSectionPtr wsp) const
{
  int itab = tabWidget->currentIndex();
  
  // collection page
  if (itab == 0) {
    if (rbSelectLibrary->isChecked()) {
      int icol = cbCollection->currentIndex();
      int iaf = cbAirfoil->currentIndex();
      const AirfoilCollection & afc( SumoComponentLib.collection(icol) );
      wsp->fromCollection(afc, iaf);
    } else if (rbRoundedPlate->isChecked()) {
      double thick = 0.01*sbRpThickness->value();
      wsp->fromPlate(thick);
    }
  }
  
  // NACA 4/5 page 
  else if (itab == 1) {
    
    double thick = 0.01*sbN4Thickness->value();
    if (rbNaca4->isChecked()) {
      double cmbr = 0.01*sbN4Camber->value();
      double cmbpos = 0.01*sbN4CamberPos->value();
      wsp->fromNaca4(cmbr, cmbpos, thick);
    } else if (rbNaca5->isChecked()) {
      int iline = 210 + 10*cbSelectMeanline->currentIndex();
      double dcl = sbN5DesignCL->value();
      wsp->fromNaca5(iline, dcl, thick);
    }
    
  }

  // NACA 6-page 
  else if (itab == 2) {
    
    double thick = 0.01*sbN6Thickness->value();
    int iprofile, idx = cbN6Family->currentIndex();
    if (idx <= 4)
      iprofile = 63 + idx;
    else
      iprofile = 158 + idx;
    idx = cbN6CamberLine->currentIndex();
    int icamber = (idx == 0) ? 63 : 163;
    
    Vector dcl, a;
    if (cbMeanLine1->isChecked()) {
      dcl.push_back( sbDesignCL1->value() );
      a.push_back( sbChordLoad1->value() );
    } else {
      dcl.push_back(0.0);
      a.push_back(1.0);
    }
    if (cbMeanLine2->isChecked()) {
      dcl.push_back( sbDesignCL2->value() );
      a.push_back( sbChordLoad2->value() );
    }
    if (cbMeanLine3->isChecked()) {
      dcl.push_back( sbDesignCL3->value() );
      a.push_back( sbChordLoad3->value() );
    }
    wsp->fromNaca6(iprofile, icamber, thick, dcl, a);
  }
  
  wsp->dxNose( sbExtendXLE->value() * 0.01 );
  wsp->dyNose( sbExtendYLE->value() * 0.01 );
  wsp->dxTail( sbExtendXTE->value() * 0.01 );
  wsp->dyTail( sbExtendYTE->value() * 0.01 );

}

void DlgAirfoil::saveAirfoil()
{
  QString filter( tr("Plain text (*.txt *.dat);; All files (*)") );
  QString fn = QFileDialog::getSaveFileName(this, tr("Select airfoil file"),
                                            QString(), filter);
  if (fn.isEmpty())
    return;

  ofstream os( asPath(fn).c_str() );
  os << std::fixed;
  os.precision(15);

  WingSectionPtr wsp(new WingSection);
  setAirfoil(wsp);
  const PointList<2> & crd( wsp->riPoints() );
  const int np = crd.size();
  for (int i=0; i<np; ++i)
    os << crd[i][0] << "\t " << crd[i][1] << std::endl;
}
