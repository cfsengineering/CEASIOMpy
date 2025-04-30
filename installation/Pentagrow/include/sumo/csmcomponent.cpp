
/* ------------------------------------------------------------------------
 * file:       csmcomponent.cpp
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Constructs sumo assembly from CEASIOM definition
 * ------------------------------------------------------------------------ */

#include "csmwing.h"
#include "csmbody.h"
#include "csmfairing.h"
#include "csmcomponent.h"

void CsmComponent::attach(const CsmComponentArray &)
{}

CsmComponentPtr CsmComponent::createFromXml(const XmlElement & xe)
{
  CsmComponentPtr cp;
  if ( CsmBody::isValid(xe) ) {
    cp = CsmComponentPtr(new CsmBody);
    cp->fromXml(xe);
  } else if ( CsmWing::isValid(xe) ) {
    cp = CsmComponentPtr(new CsmWing);
    cp->fromXml(xe);
  } else if ( CsmFairing::isValid(xe) ) {
    cp = CsmComponentPtr(new CsmFairing);
    cp->fromXml(xe);
  }
  
  return cp;
}

void CsmComponent::postAttach(Assembly &)
{}



