
/* ------------------------------------------------------------------------
 * file:       component.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Interface for surfaces which can be meshed
 * ------------------------------------------------------------------------ */
 
#include <QColor> 
 
#include <cstdlib>
#include <iostream>
#include <genua/xmlelement.h>
#include <surf/curve.h>

#include "../scope/glew.h"
#include "component.h"

using namespace std;

int Component::lasthue(117);

Component::Component() : AsyComponent(), bUseMgDefaults(true), 
                       bVisible(true), bGridUp2date(false)
{
  cPolygon = vct(0.5, 0.5, 0.5, 1.0);
  cLine = vct(1.0, 0.0, 0.0, 1.0);

  // experiment: set random color 
  // int hue = lrand48() % 360;
  int hue = lasthue;
  lasthue = (lasthue + 53) % 360;
  int sat = 140;
  int val = 170;
  Real *red = &cPolygon[0];
  Real *green = &cPolygon[1];
  Real *blue = &cPolygon[2];
  QColor::fromHsv(hue, sat, val).getRgbF(red, green, blue);
}

const std::string & Component::name() const
{
  return surface()->name();
}

void Component::rename(const std::string & s)
{
  surface()->rename(s);
}

void Component::globalScale(Real f)
{
  sTrn *= f;
  bbplo *= f;
  bbphi *= f;
  for (size_t i=0; i<vzpts.size(); ++i)
    vzpts[i] *= f;
  criterion()->globalScale(f);
}

void Component::globalTranslate(const Vct3 &trn)
{
  sTrn += trn;
  bbplo += trn;
  bbphi += trn;
  for (size_t i=0; i<vzpts.size(); ++i)
    vzpts[i] += trn;
}

void Component::updateVizGrid() const
{
  if (not bGridUp2date) {
    PointGrid<2> qts;
    vizGrid(qts);
    evalGrid(qts);
  }
}

void Component::evalGrid(const PointGrid<2> & qts) const
{
  // reset bounding box parameters 
  bbplo =  huge;
  bbphi = -huge;  
  
  // evaluate surface points 
  Vct3 Su, Sv, Sn;
  const uint pnu(qts.nrows());
  const uint pnv(qts.ncols());
  vzpts.resize(pnu,pnv);
  vznrm.resize(pnu,pnv);

  const Surface & srf(*surface());
  for (uint j=0; j<pnv; ++j) {
    for (uint i=0; i<pnu; ++i) {
      const Vct2 & q( qts(i,j) );
      srf.plane(q[0], q[1], vzpts(i,j), Su, Sv);
      Sn = cross(Su, Sv);
      normalize(Sn);
      vznrm(i,j) = Sn;

      // update bounding box values 
      for (uint k=0; k<3; ++k) {
        Real w = vzpts(i,j)[k];
        bbplo[k] = min(bbplo[k], w);
        bbphi[k] = max(bbphi[k], w);
      }
    }
  }
  
  bGridUp2date = true;
}

void Component::glDrawGrid() const
{
  // draw quads -- this should be ported to vertex arrays
  const uint nr(vzpts.nrows());
  const uint nc(vzpts.ncols());
  glBegin(GL_QUADS);
  glColor4dv(cPolygon.pointer());
  for (uint j=0; j<nc-1; ++j) {
    for (uint i=0; i<nr-1; ++i) {
      glNormal3dv( vznrm(i,j).pointer() );
      glVertex3dv( vzpts(i,j).pointer() );
      glNormal3dv( vznrm(i+1,j).pointer() );
      glVertex3dv( vzpts(i+1,j).pointer() );
      glNormal3dv( vznrm(i+1,j+1).pointer() );
      glVertex3dv( vzpts(i+1,j+1).pointer() );
      glNormal3dv( vznrm(i,j+1).pointer() );
      glVertex3dv( vzpts(i,j+1).pointer() );
    }
  }
  glEnd();
}

void Component::glDrawGrid(const PointGrid<2> & qts) const
{
  // reset bounding box parameters 
  bbplo = huge;
  bbphi = -huge;  
  
  // evaluate surface points 
  Vct3 Su, Sv, Sn;
  const uint pnu(qts.nrows());
  const uint pnv(qts.ncols());
  PointGrid<3> pg(pnu,pnv), nrm(pnu,pnv);
  const Surface & srf(*surface());
  for (uint j=0; j<pnv; ++j) {
    for (uint i=0; i<pnu; ++i) {
      const Vct2 & q( qts(i,j) );
      srf.plane(q[0], q[1], pg(i,j), Su, Sv);
      Sn = cross(Su, Sv);
      normalize(Sn);
      nrm(i,j) = Sn;
      
      // update bounding box values 
      for (uint k=0; k<3; ++k) {
        Real w = pg(i,j)[k];
        bbplo[k] = min(bbplo[k], w);
        bbphi[k] = max(bbphi[k], w);
      }
    }
  }
  
  // draw quads
  const uint nc(pg.ncols());
  glBegin(GL_QUADS);
  glColor4dv(cPolygon.pointer());
  for (uint j=0; j<nc-1; ++j) {
    for (uint i=0; i<pnu-1; ++i) {
      glNormal3dv( nrm(i,j).pointer() );
      glVertex3dv( pg(i,j).pointer() );
      glNormal3dv( nrm(i+1,j).pointer() );
      glVertex3dv( pg(i+1,j).pointer() );
      glNormal3dv( nrm(i+1,j+1).pointer() );
      glVertex3dv( pg(i+1,j+1).pointer() );
      glNormal3dv( nrm(i,j+1).pointer() );
      glVertex3dv( pg(i,j+1).pointer() );
    }
  }
  glEnd();
}

void Component::glDrawCurve(const Curve & c, const Vector & t) const
{
  // construct transformation for curve  
  Transformer tf;
  tf.rotate(sRot[0], sRot[1], sRot[2]);
  tf.translate(sTrn);
  
  // evaluate curve points
  const uint nu(t.size());
  PointList<3> pts(nu);
  for (uint i=0; i<nu; ++i)
    pts[i] = tf.forward( c.eval(t[i]) );
  
  glBegin(GL_LINE_STRIP);
  glLineWidth(2.0);
  glColor4dv(cLine.pointer());
  for (uint i=0; i<nu; ++i)
    glVertex3dv( pts[i].pointer() );
  glVertex3dv( pts[0].pointer() );
  glEnd();
}

void Component::extendBoundingBox(float plo[3], float phi[3]) const
{
  for (uint k=0; k<3; ++k) {
    plo[k] = min(plo[k], (float) bbplo[k]);
    phi[k] = max(phi[k], (float) bbphi[k]);
  }
}

XmlElement Component::rawXml(bool share) const
{
  XmlElement xs = surface()->toXml(share);
  xs.append( mgToXml() );
  for (int k=0; k<4; ++k)
    if (ecaps[k].isPresent())
      xs.append( ecaps[k].toXml() );
  return xs;
}

XmlElement Component::mgToXml() const
{
  assert(criterion());
  XmlElement xmg(criterion()->toXml());
  
  if (bUseMgDefaults)
    xmg["defaults"] = "true";
  else
    xmg["defaults"] = "false"; 
  
  if (main->stretchedMesh())
    xmg["xcoarse"] = "true";
  else
    xmg["xcoarse"] = "false"; 
  
  return xmg;
}
    
void Component::mgFromXml(const XmlElement & xe)
{
  DnRefineCriterionPtr rc = DnRefineCriterion::createFromXml(xe);
  assert(rc);
  criterion(rc);
  if (xe.hasAttribute("defaults") 
      and xe.attribute("defaults") == "true")
    bUseMgDefaults = true;
  else
    bUseMgDefaults = false;
  
  if (xe.hasAttribute("xcoarse") and 
      xe.attribute("xcoarse") == "true")
    main->stretchedMesh(true);
  else
    main->stretchedMesh(false);
}

void Component::capsToIges(IgesFile &) const
{}
