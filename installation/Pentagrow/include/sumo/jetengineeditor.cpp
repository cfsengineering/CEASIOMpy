/* ------------------------------------------------------------------------
 * file:       jetengine.cpp
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Assign jet engine boundary conditions to mesh triangles
 * ------------------------------------------------------------------------ */

#include <QComboBox>
#include <QLineEdit>
#include <QPushButton>
#include "jetengineeditor.h"

using namespace std;

JetEngineEditor::JetEngineEditor(QWidget *parent, Assembly & a) :
      QDialog(parent), asy(a)
{
  setupUi(this);
  retranslateUi(this);

  init();
  
  // to do when changing tabs
  connect( tabWidget, SIGNAL(currentChanged(int)), 
           this, SLOT(changeTab(int)) );
  
  // engine definition tab 
  connect( rbUseTFModel, SIGNAL(clicked()), this, SLOT(defineEngine()) );
  connect( rbUseVel, SIGNAL(clicked()), this, SLOT(defineEngine()) );
  connect( pbNewEngine, SIGNAL(clicked()), this, SLOT(newEngine()) );
  connect( pbDeleteEngine, SIGNAL(clicked()), this, SLOT(deleteEngine()) );
  connect( cbEngineName, SIGNAL(activated(int)), 
           this, SLOT(displayEngine(int)) );
  connect( cbEngineName, SIGNAL(editTextChanged(const QString&)),
           this, SLOT(renameEngine(const QString&)) );
  connect( cbSelectTurbofan, SIGNAL(activated(int)),
           this, SLOT(defineEngine()) );
  connect( sbMassFlow, SIGNAL(editingFinished()),
           this, SLOT(defineEngine()) );
  connect( sbIntakeVelocity, SIGNAL(editingFinished()),
           this, SLOT(defineEngine()) );
  connect( sbNozzleVelocity, SIGNAL(editingFinished()),
           this, SLOT(defineEngine()) );
  connect( cbIntakeRegion, SIGNAL(currentIndexChanged(int)),
           this, SLOT(changeIntakeRegion(int)) );
  connect( cbSecondIntake, SIGNAL(currentIndexChanged(int)),
           this, SLOT(changeSplitIntake(int)) );
  connect( cbSplitIntake, SIGNAL(toggled(bool)),
           this, SLOT(splitIntake(bool)) );
  connect( cbNozzleRegion, SIGNAL(currentIndexChanged(int)),
           this, SLOT(changeNozzleRegion(int)) );
  
  // turbofan property editor 
  connect( cbTurbofanName, SIGNAL(activated(int)), 
           this, SLOT(displayTurbofan(int)) );
  connect( cbTurbofanName, SIGNAL(editTextChanged(const QString&)),
           this, SLOT(renameTurbofan(const QString&)) );
  connect( pbNewTFModel, SIGNAL(clicked()), this, SLOT(newTurbofan()) );
  connect( pbDeleteTFModel, SIGNAL(clicked()), this, SLOT(deleteTurbofan()) );
  
  connect( sbBpr, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
  connect( sbTit, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
  connect( sbOpr, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
  connect( sbFpr, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
  
  connect( sbPolytropic, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
  connect( sbComb, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
  connect( sbDpComb, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
  connect( sbInlet, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
  connect( sbNozzle, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
  connect( sbSpool, SIGNAL(editingFinished()), this, SLOT(storeTurbofan()) );
}

void JetEngineEditor::init()
{
  initEngineLib();
  
  const uint nj(asy.njet());
  for (uint i=0; i<asy.njet(); ++i) 
    cbEngineName->addItem( QString::fromStdString(asy.jetEngine(i).name()) );
  
  const uint nb(asy.nbodies());
  for (uint i=0; i<nb; ++i) {
    cbIntakeRegion->addItem( QString::fromStdString( asy.body(i)->name() ) );
    cbSecondIntake->addItem( QString::fromStdString( asy.body(i)->name() ) );
    cbNozzleRegion->addItem( QString::fromStdString( asy.body(i)->name() ) );
  }
  
  if (nj > 0)
    displayEngine(0);
}

void JetEngineEditor::initEngineLib()
{
  // generate built-in engine models 
  uint nbim = TfSpec::nBuiltinTFModels();
  for (uint i=0; i<nbim; ++i) {
    TfSpec s = TfSpec::createBuiltinTFModel(i);
    tflib.push_back(s);
  }
  
  // search for further models in engine specs 
  const uint nj(asy.njet());
  for (uint i=0; i<nj; ++i) {
    const JetEngineSpec & js(asy.jetEngine(i));
    if (js.massflow() != 0.0) {
      const TfSpec & s(js.turbofan());
      if (findTFModel(s.name()) == NotFound) {
        tflib.push_back(s);
      }
    }
  } 
  
  updateTFModels();
}

uint JetEngineEditor::findTFModel(const std::string & id) const
{
  const uint nlib(tflib.size());
  for (uint i=0; i<nlib; ++i) {
    if (tflib[i].name() == id)
      return i;
  }
  return NotFound;
}

void JetEngineEditor::newEngine()
{
  if (asy.nbodies() < 1)
    return;
  
  JetEngineSpec spec;
  spec.rename("NewEngine");
  spec.intakeRegion() = JeRegion(asy.body(0), JeRegion::JerNose);
  spec.nozzleRegion() = JeRegion(asy.body(0), JeRegion::JerTail);
  asy.addJetEngine( spec );
  cbEngineName->addItem(QString::fromStdString(spec.name()));
  displayEngine(asy.njet()-1);
}
    
void JetEngineEditor::deleteEngine()
{
  uint idx = cbEngineName->currentIndex();
  if (idx < asy.njet()) {
    asy.removeJetEngine(idx);
    cbEngineName->removeItem(idx);
    if (idx > 0) {
      displayEngine(idx-1);
    } else if (asy.njet() > 0) {
      displayEngine(0);
    } 
  }
}
    
void JetEngineEditor::renameEngine(const QString &s)
{
  uint idx = cbEngineName->currentIndex();
  if (idx < asy.njet()) {
    asy.jetEngine(idx).rename( s.toStdString() );
  }
}

void JetEngineEditor::defineEngine()
{
  uint idx = cbEngineName->currentIndex();
  if (idx >= asy.njet())
    return;
  
  if (rbUseTFModel->isChecked()) {
    asy.jetEngine(idx).massflow( sbMassFlow->value() );
    uint itf = cbSelectTurbofan->currentIndex();
    asy.jetEngine(idx).turbofan() = tflib[itf];
  } else {
    Real vin = sbIntakeVelocity->value();
    Real vnz = sbNozzleVelocity->value();
    asy.jetEngine(idx).setTranspiration(vin, vnz);
  }
}
    
void JetEngineEditor::changeIntakeRegion(int bi)
{
  uint idx = cbEngineName->currentIndex();
  if (idx >= asy.njet())
    return;
  
  asy.jetEngine(idx).intakeRegion().body( asy.body(bi) );
}

void JetEngineEditor::changeSplitIntake(int bi)
{
  uint idx = cbEngineName->currentIndex();
  if (idx >= asy.njet())
    return;
  
  JetEngineSpec & js(asy.jetEngine(idx));
  if (cbSplitIntake->isChecked()) {
    if (js.nintake() > 1) {
      js.intakeRegion(1).body( asy.body(bi) );
    } else {
      js.addIntakeRegion( JeRegion(asy.body(bi), JeRegion::JerNose) );
    }
  } else {
    if (js.nintake() > 1) {
      js.removeIntakeRegion(1);
    }
  }
}

void JetEngineEditor::splitIntake(bool)
{
  changeSplitIntake(0);
}
    
void JetEngineEditor::changeNozzleRegion(int bi)
{
  uint idx = cbEngineName->currentIndex();
  if (idx >= asy.njet())
    return;
  
  asy.jetEngine(idx).nozzleRegion().body( asy.body(bi) );
}
    
void JetEngineEditor::displayEngine(int i)
{
  if (i >= int(asy.njet()))
    return;
  
  const JetEngineSpec & js(asy.jetEngine(i));
  cbEngineName->setCurrentIndex(i);
  
  // first intake must be defined 
  string its = js.intakeRegion(0).srfName();
  int idx = cbIntakeRegion->findText( QString::fromStdString(its) );
  idx = max(0, idx);
  cbIntakeRegion->setCurrentIndex(idx);
  
  if (js.nintake() > 1) {
    cbSplitIntake->setChecked(true);
    // cbSecondIntake->setEnabled(true);
    its = js.intakeRegion(1).srfName();
    idx = cbSecondIntake->findText( QString::fromStdString(its) );
    idx = max(0, idx);
    cbSecondIntake->setCurrentIndex(idx);
  } else {
    cbSplitIntake->setChecked(false);
    // cbSecondIntake->setEnabled(false);
  }
  
  string nzs = js.nozzleRegion().srfName();
  idx = cbNozzleRegion->findText( QString::fromStdString(nzs) );
  idx = max(0, idx);
  cbNozzleRegion->setCurrentIndex(idx);
  
  // check which definition to use 
  Real mf = js.massflow();
  if (mf != 0.0) {
    rbUseTFModel->setChecked(true);
    sbMassFlow->setValue(mf);
    const TfSpec & tf( js.turbofan() );
    uint itf = findTFModel( tf.name() );
    if (itf != NotFound) {
      cbSelectTurbofan->setCurrentIndex(itf);
      cbTurbofanName->setCurrentIndex(itf);
    }
  } else {
    rbUseVel->setChecked(true);
    sbIntakeVelocity->setValue(js.intakeVelocity());
    sbNozzleVelocity->setValue(js.nozzleVelocity());
  }
}

void JetEngineEditor::newTurbofan()
{
  TfSpec ntf = TfSpec::createBuiltinTFModel(0);
  ntf.rename("New turbofan model");
  tflib.push_back(ntf);
  updateTFModels();
  displayTurbofan(tflib.size()-1);
}
    
void JetEngineEditor::deleteTurbofan()
{
  uint idx = cbTurbofanName->currentIndex();
  if (idx >= tflib.size() or idx < TfSpec::nBuiltinTFModels())
    return;
  
  tflib.erase(tflib.begin() + idx);
  displayTurbofan(idx-1);
}
    
void JetEngineEditor::displayTurbofan(int i)
{
  if (uint(i) >= tflib.size())
    return;
    
  const TfSpec & tf(tflib[i]);
  cbTurbofanName->setCurrentIndex(i);
  
  sbBpr->setValue(tf.bypassRatio());
  sbTit->setValue(tf.turbineTemperature());
  sbOpr->setValue(tf.totalPressureRatio());
  sbFpr->setValue(tf.fanPressureRatio());
  
  sbPolytropic->setValue(tf.etaPolytropic());
  sbComb->setValue(tf.etaCombustion());
  sbDpComb->setValue(tf.combPressureLoss());
  sbInlet->setValue(tf.etaInlet());
  sbNozzle->setValue(tf.etaNozzle());
  sbSpool->setValue(tf.etaSpool());

  // disable removal of builtin models 
  if (uint(i) < TfSpec::nBuiltinTFModels()) {
    cbTurbofanName->setEditable(false);
    pbDeleteTFModel->setEnabled(false);
    sbBpr->setEnabled(false);
    sbTit->setEnabled(false);
    sbOpr->setEnabled(false);
    sbFpr->setEnabled(false);
    sbPolytropic->setEnabled(false);
    sbComb->setEnabled(false);
    sbDpComb->setEnabled(false);
    sbInlet->setEnabled(false);
    sbNozzle->setEnabled(false);
    sbSpool->setEnabled(false);
  } else {
    cbTurbofanName->setEditable(true);
    pbDeleteTFModel->setEnabled(true);
    sbBpr->setEnabled(true);
    sbTit->setEnabled(true);
    sbOpr->setEnabled(true);
    sbFpr->setEnabled(true);
    sbPolytropic->setEnabled(true);
    sbComb->setEnabled(true);
    sbDpComb->setEnabled(true);
    sbInlet->setEnabled(true);
    sbNozzle->setEnabled(true);
    sbSpool->setEnabled(true);
  }
}
    
void JetEngineEditor::renameTurbofan(const QString & s)
{
  uint idx = cbTurbofanName->currentIndex();
  if (idx >= tflib.size())
    return;
  
  TfSpec & tf(tflib[idx]);
  tf.rename( s.toStdString() );
}
    
void JetEngineEditor::storeTurbofan()
{
  uint idx = cbTurbofanName->currentIndex();
  if (idx < TfSpec::nBuiltinTFModels() or idx >= tflib.size())
    return;
  
  TfSpec & tf(tflib[idx]);
  tf.bypassRatio( sbBpr->value() );
  tf.turbineTemperature( sbTit->value() );
  tf.totalPressureRatio( sbOpr->value() );
  tf.fanPressureRatio( sbFpr->value() );
  
  tf.etaPolytropic( sbPolytropic->value() );
  tf.etaCombustion( sbComb->value() );
  tf.combPressureLoss( sbDpComb->value() );
  tf.etaInlet( sbInlet->value() );
  tf.etaNozzle( sbNozzle->value() );
  tf.etaSpool( sbSpool->value() );
}

void JetEngineEditor::updateTFModels()
{
  int it0 = cbSelectTurbofan->currentIndex();
  int it1 = cbTurbofanName->currentIndex();
  
  if (it0 < 0 or it0 >= int(tflib.size()))
    it0 = 0;
  if (it1 < 0 or it1 >= int(tflib.size()))
    it1 = 0;
  
  cbSelectTurbofan->clear();
  cbTurbofanName->clear();
  uint ntf = tflib.size();
  for (uint i=0; i<ntf; ++i) {
    const TfSpec & tf(tflib[i]);
    QString s =  QString::fromStdString(tf.name());
    cbSelectTurbofan->addItem(s);
    cbTurbofanName->addItem(s);
  }
  
  cbSelectTurbofan->setCurrentIndex(it0);
  cbTurbofanName->setCurrentIndex(it1);
}

void JetEngineEditor::changeTab(int itab)
{  
  if (itab == 0) {
    storeTurbofan();
    defineEngine();
    updateTFModels();
  } else if (itab == 1) {
    updateTFModels();
    int itf = cbSelectTurbofan->currentIndex();
    displayTurbofan(itf);
  }
}

