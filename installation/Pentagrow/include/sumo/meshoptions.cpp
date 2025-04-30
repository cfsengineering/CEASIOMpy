
/* ------------------------------------------------------------------------
 * file:       meshoptions.cpp
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Front-end for mesh generation facilities
 * ------------------------------------------------------------------------ */
 
#include <QString>
#include <QDoubleSpinBox>
#include <QComboBox>
#include <QCheckBox>
#include <QPushButton>
 
#include <surf/dnwingcriterion.h>
#include "assembly.h"
#include "meshoptions.h"

using namespace std;
 
MeshOptions::MeshOptions(QWidget *parent, Assembly & a) : QDialog(parent), asy(a) 
{
  // create user interface
  setupUi(this);
  retranslateUi(this);

  // copy names into surface list 
  bool mgd, alldef = true;
  for (uint i=0; i<asy.ncomponents(); ++i) {
    string s = asy.sumoComponent(i)->name();
    cbBody->addItem( QString::fromStdString( s ) );
    mgd = asy.sumoComponent(i)->useMgDefaults();
    alldef &= mgd;
    if (mgd)
      asy.sumoComponent(i)->defaultCriterion();
  }
  cbAllDefaults->setChecked(alldef);
  
  // show appropriate settings whenever selected surface changes
  connect(cbBody, SIGNAL(activated(int)), this, SLOT(showSettings(int)));
  
  // update MG settings after user change
  connect(cbUseDefaults, SIGNAL(toggled(bool)), this, SLOT(mgSetDefaults(bool)));
  connect(cbStretchedMesh, SIGNAL(toggled(bool)), this, SLOT(mgSetCoarse(bool)));
  connect(cbAllDefaults, SIGNAL(toggled(bool)), this, SLOT(mgSetAllDefaults(bool)));
  
  connect(sbMaxLength, SIGNAL(editingFinished()), this, SLOT(mgValueChanged()));
  connect(sbMinLength, SIGNAL(editingFinished()), this, SLOT(mgValueChanged()));
  connect(sbMaxPhi, SIGNAL(editingFinished()), this, SLOT(mgValueChanged()));
  connect(sbMaxStretch, SIGNAL(editingFinished()), this, SLOT(mgValueChanged()));
  connect(sbLEFactor, SIGNAL(editingFinished()), this, SLOT(mgValueChanged()));
  connect(sbTEFactor, SIGNAL(editingFinished()), this, SLOT(mgValueChanged()));
  
  connect(sbStretchFactor, SIGNAL(editingFinished()), this, SLOT(mgValueChanged()));
  connect(sbGlobalMaxPhi, SIGNAL(editingFinished()), this, SLOT(mgValueChanged()));
  connect(sbIterations, SIGNAL(editingFinished()), this, SLOT(mgValueChanged()));
  
  // activate first entry 
  cbBody->setCurrentIndex(0);
  showSettings(0);
}

void MeshOptions::showSettings(int i) const
{
  ComponentPtr cp(asy.sumoComponent(i));
  DnRefineCriterionPtr mcp(cp->criterion());
  
  cbUseDefaults->setChecked( cp->useMgDefaults() );
  if ( asy.isWing(i) ) {
    
    // is a wing 
    cbStretchedMesh->setEnabled( true );
    cbStretchedMesh->setChecked( cp->stretchedMesh() );
    
    DnWingCriterionPtr wcr;
    wcr = boost::dynamic_pointer_cast<DnWingCriterion>( mcp );
    if (wcr) {
      sbLEFactor->setValue( 1.0/wcr->leRefinement() );
      sbTEFactor->setValue( 1.0/wcr->teRefinement() );
      if (not cp->useMgDefaults()) {
        lbLEFactor->setEnabled(true);
        lbTEFactor->setEnabled(true);
        sbLEFactor->setEnabled(true);
        sbTEFactor->setEnabled(true);
      } else {
        lbLEFactor->setEnabled(false);
        lbTEFactor->setEnabled(false);
        sbLEFactor->setEnabled(false);
        sbTEFactor->setEnabled(false);
      }
    }
    
  } else {
    
    // is a body 
    cbStretchedMesh->setChecked( false );
    cbStretchedMesh->setEnabled( false );
    sbLEFactor->setEnabled(false);
    sbTEFactor->setEnabled(false);
    lbLEFactor->setEnabled(false);
    lbTEFactor->setEnabled(false);
    
  }
  
  adapt( sbMaxLength, mcp->maxLength() );
  adapt( sbMinLength, mcp->minLength() );
  sbMaxPhi->setValue( deg(mcp->maxPhi()) );
  sbMaxStretch->setValue(mcp->maxStretch());
  
  adapt( sbStretchFactor, asy.ppStretch() );
  sbGlobalMaxPhi->setValue( deg(asy.ppGlobalMaxPhi()) );
  sbIterations->setValue( asy.ppIterations() );
}  

void MeshOptions::mgValueChanged()
{
  int idx = cbBody->currentIndex();
  
  ComponentPtr cp(asy.sumoComponent(idx));
  DnRefineCriterionPtr mcp(cp->criterion());
  
  if (asy.isWing(idx))
    cp->stretchedMesh( cbStretchedMesh->isChecked() );
  else
    cp->stretchedMesh( false );
  
  if (cbUseDefaults->isChecked()) {
    cp->useMgDefaults( true );
    cp->defaultCriterion();  
  } else {
    
    cp->useMgDefaults( false );
    
    mcp->maxLength( sbMaxLength->value() );
    mcp->minLength( sbMinLength->value() );
    mcp->maxPhi( rad(sbMaxPhi->value()) );
    mcp->maxStretch( sbMaxStretch->value() );
    
    DnWingCriterionPtr wcr;
    wcr = boost::dynamic_pointer_cast<DnWingCriterion>( mcp );
    if (wcr) {
      wcr->edgeRefinement( 1.0/sbLEFactor->value(),
                           1.0/sbTEFactor->value() );
    } 
  }

  // tell the mesh generator that this surface must
  // be completely remeshed
  cp->surfaceChanged();
  
  // global settings
  asy.ppIterations( sbIterations->value() );
  asy.ppGlobalMaxPhi( rad(sbGlobalMaxPhi->value()) );
  asy.ppStretch( sbStretchFactor->value() ); 
  
  showSettings(idx);
}

void MeshOptions::mgSetDefaults(bool flag)
{
  int item = cbBody->currentIndex();
  ComponentPtr cp(asy.sumoComponent(item));
  if (flag) {
    cp->useMgDefaults( true );
    cp->defaultCriterion();
    showSettings( item );
  } else {
    cp->useMgDefaults( false );
    showSettings( item );
    mgValueChanged();
  } 
}

void MeshOptions::mgSetAllDefaults(bool flag)
{
  const int nc = asy.ncomponents();
  for (int i=0; i<nc; ++i) {
    ComponentPtr cp(asy.sumoComponent(i));
    cp->useMgDefaults(flag);
    if (flag) 
      cp->defaultCriterion();
  }
}

void MeshOptions::mgSetCoarse(bool flag)
{
  int item = cbBody->currentIndex();
  ComponentPtr cp(asy.sumoComponent(item));
  
  // change defaults if setting changed 
  bool oldflag = cp->stretchedMesh();
  cp->stretchedMesh(flag);
  
  uint nsm = flag ? 0 : 2;
  Real wsm = flag ? 0.0 : 0.25;
  cp->smoothing(nsm, wsm);
  if (flag != oldflag) {
    mgSetDefaults( cbUseDefaults->isChecked() );
  }
  
//   lbLEFactor->setEnabled(!flag);
//   lbTEFactor->setEnabled(!flag);
//   sbLEFactor->setEnabled(!flag);
//   sbTEFactor->setEnabled(!flag);
}

void MeshOptions::adapt(QDoubleSpinBox *sb, double v, double rstep) const
{
  double lgv = ceil( -log10(fabs(v)) );
  sb->setDecimals( max(1, int(lgv+2)) );
  sb->setSingleStep( rstep*v );
  sb->setValue(v);
}

