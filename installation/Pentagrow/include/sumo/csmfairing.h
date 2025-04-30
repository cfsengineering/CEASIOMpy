
/* ------------------------------------------------------------------------
 * file:       csmfairing.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * CEASIOM fairing definition of the SimSAC project
 * ------------------------------------------------------------------------ */

#ifndef SUMO_CSMFAIRING_H
#define SUMO_CSMFAIRING_H

#include <string>
#include <genua/defines.h>
#include "bodyskeleton.h"
#include "csmcomponent.h"

class XmlElement;
class CsmBody;
class CsmWing;

/**
*/
class CsmFairing : public CsmComponent
{
  public:
    
    /// undefined fairing
    CsmFairing() : width(0.0) {}

    /// read parameters from xml file
    void fromXml(const XmlElement & xe);
    
    /// derive remaining size parameters by attaching to wing/body
    void attach(const CsmComponentArray & csm);
    
    /// generate an actual body
    ComponentPtr create() const;
    
    /// determine if xml element contains a fairing
    static bool isValid(const XmlElement & xe);
    
  private:
    
    /// fairing size parameters from file
    Real fwd_fraction, aft_fraction, width2height;
  
    /// dimensions induced from body/wing
    Real fwd_length, ctr_length, aft_length, width, height;

    /// location of the first section
    Vct3 org;
};

#endif
