
/* ------------------------------------------------------------------------
 * file:       csmcomponent.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * 
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CSMCOMPONENT_H
#define SUMO_CSMCOMPONENT_H

#include <string>
#include <boost/shared_ptr.hpp>

class XmlElement;
class CsmComponent;
class Assembly;
typedef boost::shared_ptr<CsmComponent> CsmComponentPtr;
typedef std::vector<CsmComponentPtr> CsmComponentArray;

/** Abstract base class for ceasiom components
*/
class CsmComponent
{
  public:
    
    /// undefined component
    CsmComponent() {}

    /// virtual destruction
    virtual ~CsmComponent() {}
    
    /// return tag identification
    const std::string & tag() const {return tagid;}
    
    /// access tag identification
    void tag(const std::string & t) {tagid = t;}
    
    /// read xml content
    virtual void fromXml(const XmlElement & xe) = 0;

    /// connect to remaining components (optional)
    virtual void attach(const CsmComponentArray & csm);
    
    /// create sumo component from representation
    virtual ComponentPtr create() const = 0;

    /// attach additional data which may require the complete model
    virtual void postAttach(Assembly & asy);
    
    /// create ceasiom component from xml
    static CsmComponentPtr createFromXml(const XmlElement & xe);
    
  private:
    
    /// tag used to generate this object
    std::string tagid;
};

#endif
