
/* ------------------------------------------------------------------------
 * file:       ctpattern.h
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Stores data for combined control surface deflections
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CTPATTERN_H
#define SUMO_CTPATTERN_H

#include <genua/defines.h>
#include <genua/dvector.h>
#include <genua/xmlelement.h>

/**
  */
class CtPattern
{
  public:
    
    /// default construction (empty)
    CtPattern() : bVisible(false) {}
    
    /// access name
    const std::string & name() const {return id;}
    
    /// change name
    void rename(const std::string & s) {id = s;}
    
    /// number of participating surfaces
    uint npart() const {return pcf.size();}
    
    /// find index of nonzero pattern 
    uint find(const std::string & s) const;
    
    /// access name and participation factor
    void get(uint i, std::string & s, Real & f) const;
    
    /// change participating control
    void set(uint i, const std::string & s, Real f);
    
    /// append a new participation, return index
    uint append(const std::string & s, Real f);
    
    /// delete all participations
    void clear();
    
    /// delete participation i
    void remove(uint i);
    
    /// delete participation of surface s
    void remove(const std::string & s);
    
    /// rename participating surface old to new
    void rename(const std::string & idold, const std::string & idnew);
    
    /// read from xml definition
    void fromXml(const XmlElement & xe);
    
    /// export to xml definition
    XmlElement toXml() const;
    
  private:
    
    /// name of this control pattern
    std::string id;
    
    /// names of participating controls
    StringArray cnames;
    
    /// participation factors
    std::vector<double> pcf;
    
    /// visibility flag
    bool bVisible;
};

#endif

