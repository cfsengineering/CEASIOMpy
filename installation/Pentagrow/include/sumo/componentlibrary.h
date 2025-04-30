
/* ------------------------------------------------------------------------
 * file:       componentlibrary.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Provide access to stored components
 * ------------------------------------------------------------------------ */

#ifndef SUMO_COMPONENTLIBRARY_H
#define SUMO_COMPONENTLIBRARY_H

#include <QObject>

#include <genua/xmlelement.h>
#include <genua/binfilenode.h>
#include <surf/airfoillibrary.h>
#include "assembly.h"

class QString;

/** Library of predefined components.

  The global component library object contains an airfoil library object to
  hold a set of predefined airfoil collections which comes with sumo.

  Furthermore, it holds the infastructure to manage predefined assemblies and
  surfaces in the form of their xml representation. 

*/
class ComponentLibrary : public QObject
{
  public:
    
    /// create empty library 
    ComponentLibrary() {}
    
    /// load all components stored in executable 
    void loadPredefined();
    
    /// number of assembly templates 
    uint nassembly() const {return asylib.size();}
    
    /// access name of assembly template i 
    const QString & assemblyName(uint i) const {
      assert(i < asylib.size());
      return asylib[i].id;
    }
    
    /// generate assembly i (expensive) 
    AssemblyPtr assembly(uint i) const;
    
    /// number of component templates 
    uint ncomponents() const {return cmplib.size();}
    
    /// access name of component template i 
    const QString & componentName(uint i) const {
      assert(i < cmplib.size());
      return cmplib[i].id;
    }
    
    /// access component's xml representation
    const XmlElement & componentXml(uint i) const {
      assert(i < cmplib.size());
      return cmplib[i].xe;
    }
    
    /// number of airfoil collections 
    uint nafcollect() const {return aflib.size();}
    
    /// access collection i 
    const AirfoilCollection & collection(uint i) const {
      return aflib.collection(i);
    }
    
    /// access name of collection i
    QString collectionName(uint i) const {
      return QString::fromStdString( aflib.collection(i).name() );
    }
    
    /// find airfoil collection by name 
    uint findCollection(const std::string & s) const {
      return aflib.findCollection(s);
    } 
    
    /// perform global search for airfoil by filename 
    AirfoilPtr airfoilByFileName(const std::string & s) const {
      return aflib.airfoilByFileName( s );
    }
    
  private:
    
    struct XmlTemplate {
      XmlElement xe;
      QString id;
    };
    
    typedef std::vector<XmlTemplate> XmlLibrary;
    
    /// load file into xml element 
    void readXml(const QString & path, XmlElement & xe);
    
    /// fetch binary file node from path 
    BinFileNodePtr readGbf(const QString & path);
    
  private:
    
    /// collection of airfoils
    AirfoilLibrary aflib;
    
    /// complete assemblies 
    XmlLibrary asylib;
    
    /// components
    XmlLibrary cmplib;
};

extern ComponentLibrary SumoComponentLib;

#endif
