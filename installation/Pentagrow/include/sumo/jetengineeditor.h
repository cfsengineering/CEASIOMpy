
/* ------------------------------------------------------------------------
 * file:       jetengine.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Assign jet engine boundary conditions to mesh triangles
 * ------------------------------------------------------------------------ */

#ifndef SUMO_JETENGINEEDITOR_H
#define SUMO_JETENGINEEDITOR_H

#include "ui_dlgeditjetengine.h"
#ifndef Q_MOC_RUN
#include "jetenginespec.h"
#include "assembly.h"
#endif

class QDoubleValidator;

/** Define jet engine properties.

  
*/
class JetEngineEditor : public QDialog, private Ui::DlgEditJetEngine
{
  Q_OBJECT
  
  public:
    
    /// setup editor dialog window
    JetEngineEditor(QWidget *parent, Assembly & a);
    
    /// destruction 
    virtual ~JetEngineEditor() {}

  private slots:
    
    /// create new engine spec
    void newEngine();
    
    /// delete existing engine spec
    void deleteEngine();
    
    /// change engine definition type 
    void defineEngine();
    
    /// show data for engine i 
    void displayEngine(int i);
    
    /// change engine name
    void renameEngine(const QString & s);
    
    /// change inlet region 
    void changeIntakeRegion(int bi);
    
    /// change split intake
    void changeSplitIntake(int bi);
    
    /// switch split intake on/off 
    void splitIntake(bool toggle);
    
    /// change nozzle region 
    void changeNozzleRegion(int bi);
    
    /// create new turbofan model
    void newTurbofan();
    
    /// delete existing turbofan model 
    void deleteTurbofan();
    
    /// show data for turbofan i 
    void displayTurbofan(int i);
    
    /// change turbofan model name 
    void renameTurbofan(const QString & s);
    
    /// set all values for current turbofan 
    void storeTurbofan();
    
    /// update TF model list 
    void updateTFModels();
    
    /// called whenever tab is changed 
    void changeTab(int itab);
    
  private:
    
    /// fill data for existing engines
    void init();
    
    /// fill engine model library 
    void initEngineLib();
    
    /// look for engine model in library
    uint findTFModel(const std::string & id) const;
    
  private:
    
    /// assembly to assign engine spec to 
    Assembly & asy; 
    
    /// validator for volume flow fields 
    QDoubleValidator *vfval;

    /// library of engine models found in file
    TfSpecLib tflib; 
};

#endif
