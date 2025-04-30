
/* ------------------------------------------------------------------------
 * file:       ctsurface.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Control surface geometry data
 * ------------------------------------------------------------------------ */

#include <sstream>
#include <genua/xcept.h>
#include "assembly.h"
#include "ctsurface.h"

#include "../scope/glew.h"

using namespace std;

// ----------------- CtSurfaceBox ------------------------------------------

CtSurfaceBox::CtSurfaceBox(uint iseg, const PointList<3> & pfwd, 
                                      const PointList<3> & paft)
{
  const Vct3 & pfl( pfwd[iseg] );
  const Vct3 & pfr( pfwd[iseg+1] );
  const Vct3 & pal( paft[iseg] );
  const Vct3 & par( paft[iseg+1] );
  
  Real clr = norm(par-pfr);
  Real cll = norm(pal-pfl);
  Real clen = 0.5*(clr + cll);
  Real zlen = 0.5*clen;
  
  Vct3 pmid = 0.25*(pfl+pfr+pal+par);
  Vct3 nplane = cross(pal-pfl, par-pfl).normalized()
              + cross(pfl-pfr, par-pfr).normalized();
  normalize(nplane);
  
  // bottom and top plane
  pn[0] = nplane;
  pd[0] = dot(pn[0], pmid - zlen*nplane);
  pn[1] = -nplane;
  pd[1] = dot(pn[1], pmid + zlen*nplane);
  
  // front and rear plane
  pn[2] = cross(nplane, pfl-pfr).normalized();
  pd[2] = dot(pn[2],pfl);
  pn[3] = cross(nplane, par-pal).normalized();
  pd[3] = dot(pn[3],pal);
  
  // left and right plane
  pn[4] = cross(nplane, pal-pfl).normalized();
  pd[4] = dot(pn[4], pal);
  pn[5] = cross(nplane, pfr-par).normalized();
  pd[5] = dot(pn[5],pfr);
  
  // swap normal directions if necessary
  for (int k=0; k<6; ++k) {
    if (dot(pn[k],pmid)-pd[k] < 0.0)
      pn[k] *= -1.;
  }
}

// ----------------- CtSurface ----------------------------------------------

CtSurface::CtSurface(const WingSkeletonPtr & w) : wsp(w), firstTag(0) 
{
  assert(wsp);
  id = "LeftFlap";
  cstype = CsTef;
  
  // default dimensions   
  chordpos.resize(2);
  spanpos.resize(2);
  spanpos[0] = 0.2;
  spanpos[1] = 0.4;
  chordpos[0] = 0.75;
  chordpos[1] = 0.75; 
  updateGeometry();
}

CtSurface CtSurface::mirrorCopy() const
{
  CtSurface mc(wsp);
  
  // try to guess a good name
  const char Left[] = "Left";
  const char Right[] = "Right";
  string sname(id);
  string::size_type lpos, rpos;
  lpos = sname.find(Left);
  rpos = sname.find(Right);
  if (lpos != string::npos) {
    sname.replace(lpos, strlen(Left), Right); 
  } else if (rpos != string::npos) {
    sname.replace(rpos, strlen(Right), Left); 
  } else {
    sname += "MirrorCopy";
  }
  mc.rename(sname);
  
  mc.type( type() );
  mc.clearHinges();
  const int nbp(spanpos.size());
  for (int i=0; i<nbp; ++i) {
    int k = nbp-i-1;
    mc.addHingepoint(1.0-spanpos[k], chordpos[k]);
  }
  mc.updateGeometry();
  
  return mc;
}

void CtSurface::segments(StringArray & sgnames) const
{
  const uint ns(nsegments());
  if (ns < 2) {
    sgnames.push_back(id);
    return;
  } 
  
  for (uint i=0; i<ns; ++i) {
    string sn(id);
    sn += "Segment" + str(i);
    sgnames.push_back(sn);
  }
}

uint CtSurface::addHingepoint(Real spos, Real cpos)
{
  Vector::iterator pos;
  pos = lower_bound(spanpos.begin(), spanpos.end(), spos);
  uint ipos = std::distance(spanpos.begin(), pos);
  spanpos.insert(spanpos.begin()+ipos, spos);
  chordpos.insert(chordpos.begin()+ipos, cpos);
  updateGeometry();
  return ipos;
}

uint CtSurface::changeHingepoint(uint i, Real spos, Real cpos)
{
  assert(i < spanpos.size());
  spanpos.erase(spanpos.begin()+i);
  chordpos.erase(chordpos.begin()+i);
  uint ipos = addHingepoint(spos, cpos);
  updateGeometry();
  return ipos;
}

void CtSurface::updateGeometry()
{
  const int nhp(spanpos.size());
  if ((not wsp) or (nhp < 2))
    return;
  
  Real c;
  hp.resize(nhp);
  ep.resize(nhp);
  for (int j=0; j<nhp; ++j) {
    int i = nhp-j-1;
    c = wsp->hingePos(spanpos[i], chordpos[i], hp[j]);
    ep[j] = hp[j];
    if (cstype == CsLef) {
      ep[j][0] -= 2*c*chordpos[i];
    } else if (cstype == CsTef) {
      ep[j][0] += 2*c*(1.0 - chordpos[i]);
    }
  }
  
  // extend extreme hinges beyond wingtips if needed 
  const int n(nhp-1);
  if (spanpos[0] < 0.0) {
    Vct3 dv = spanpos[0]*(hp[n] - hp[n-1])/(spanpos[1] - spanpos[0]);
    hp[n] -= dv;
    ep[n] -= dv;
  }
  if (spanpos[n] > 1.0) {
    Vct3 dv = (spanpos[n] - 1.0)*(hp[1] - hp[0])/(spanpos[n] - spanpos[n-1]);
    hp[0] -= dv;
    ep[0] -= dv;
  }
}
    
void CtSurface::draw() const
{
  const uint ns(nsegments());
  if (ns == 0)
    return;
  
  // construct hinge directions
  PointList<3> hline(ns);
  for (uint i=0; i<ns; ++i) {
    hline[i] = hp[i+1] - hp[i];
    normalize(hline[i]);
  }
  
  // construct points for drawing
  Vct3 mhl;
  PointList<3> vup(ns+1), pup(ns+1), plo(ns+1);
  for (uint i=0; i<ns+1; ++i) {
    if (i == 0)
      mhl = hline.front();
    else if (i == ns)
      mhl = hline.back();
    else 
      mhl = 0.5*(hline[i-1] +  hline[i]);
    Real chord = norm(ep[i] - hp[i]);
    vup[i]  = cross(ep[i]-hp[i], mhl);
    vup[i] *= 0.25*chord/norm(vup[i]);
    pup[i] = ep[i] + vup[i];
    plo[i] = ep[i] - vup[i];
  }
  
  // disable lighting temporarily
  glDisable(GL_LIGHTING);

  // draw each segment using three quads   
  Vct3 t1, t2, t3, t4;
  glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
  glEnable(GL_LINE_SMOOTH);
  glBegin(GL_QUADS);  
  for (uint i=0; i<ns; ++i) {
    
    // surface mean plane, defleced upward
    glColor3f(1.0f, 0.0f, 0.0f);
    glVertex3dv(hp[i].pointer());
    glVertex3dv(pup[i].pointer());
    glVertex3dv(pup[i+1].pointer());
    glVertex3dv(hp[i+1].pointer());
    
    // surface mean plane, deflected downward
    glColor3f(0.0f, 0.0f, 1.0f);
    glVertex3dv(hp[i].pointer());
    glVertex3dv(hp[i+1].pointer());
    glVertex3dv(plo[i+1].pointer());
    glVertex3dv(plo[i].pointer());
    
    // compute points for hinge plane
    t1 = hp[i] + vup[i];
    t2 = hp[i+1] + vup[i+1];
    t3 = hp[i+1] - vup[i+1];
    t4 = hp[i] - vup[i];
    
    // indicate hinge plane
    glVertex3dv(t1.pointer());
    glVertex3dv(t2.pointer());
    glVertex3dv(t3.pointer());
    glVertex3dv(t4.pointer());
  }
  glEnd();
  
  // indicate breakpoints using triangles
  glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
  glBegin(GL_TRIANGLES);
  glColor3f(0.0f, 0.0f, 1.0f);
  for (uint i=0; i<ns+1; ++i) {
    glVertex3dv(hp[i].pointer());
    glVertex3dv(pup[i].pointer());
    glVertex3dv(plo[i].pointer());
  }
  glEnd();  

  // disable lighting temporarily
  glEnable(GL_LIGHTING);
}
    
void CtSurface::fromXml(const XmlElement & xe, const Assembly & asy)
{
  // read parameters only 
  if (xe.name() != "ControlSrf")
    throw Error("Incompatible XML representation for CtSurface.");
  
  // identify wing surface 
  string wname = xe.attribute("wing");
  uint iw = asy.find(wname);
  if (iw == NotFound)
    throw Error("Cannot attach hinge to wing "+wname);
  
  wsp = asy.asWing(iw);
  assert(wsp);
  
  id = xe.attribute("name");
  string s = xe.attribute("type");
  if (s == "LEF")
    cstype = CsLef;
  else if (s == "TEF")
    cstype = CsTef;
  else if (s == "AM")
    cstype = CsAm;
  
  spanpos = Vector();
  chordpos = Vector();
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    if (itr->name() == "Hingepoint") {
      spanpos.push_back( Float(itr->attribute("spanpos")) );
      chordpos.push_back( Float(itr->attribute("chordpos")) );
    }
  }  
  
  updateGeometry();
}
    
XmlElement CtSurface::toXml() const
{
  XmlElement xe("ControlSrf");
  xe["name"] = id;
  xe["wing"] = wsp->name();
  if (cstype == CsLef)
    xe["type"] = "LEF";
  else if (cstype == CsTef)
    xe["type"] = "TEF";
  else if (cstype == CsAm)
    xe["type"] = "AM";
  
  const int nbp(spanpos.size());
  for (int i=0; i<nbp; ++i) {
    XmlElement xb("Hingepoint");
    xb["spanpos"] = str(spanpos[i]);
    xb["chordpos"] = str(chordpos[i]);
    xe.append(xb);
  }
  
  return xe;
}
    
XmlElement CtSurface::meshXml() const
{
  XmlElement xe("ControlSrf");
  xe["name"] = id;
  const uint nbp(hp.size());
  xe["nbreak"] = str(nbp);
  
  stringstream ss;
  for (uint i=0; i<nbp; ++i) 
    ss << hp[i] << ep[i] << endl;
  xe.text(ss.str());
  
  return xe;
}

int CtSurface::tagElements(TriMesh & msh, int t)
{
  firstTag = t;
  
  PointList<3> fwd, aft;
  if (type() == CsTef) {
    fwd = hp;
    aft = ep;
  } else if (type() == CsLef){
    fwd = ep;
    aft = hp;
  } else if (type() == CsAm) {
    fwd.resize(hp.size());
    aft.resize(hp.size());
    for (uint i=0; i<hp.size(); ++i) {
      fwd[i] = hp[i] - ep[i];
      aft[i] = hp[i] + ep[i];
    }
  }
  
  // mark vertices
  const int nv = msh.nvertices();
  Indices vseg(nv);
  fill(vseg.begin(), vseg.end(), NotFound);
  const int nseg = hp.size()-1;
  for (int iseg=0; iseg<nseg; ++iseg) {
    CtSurfaceBox box(iseg, fwd, aft);
    uint nvtag(0);
    for (int i=0; i<nv; ++i) {
      if (box.isInside(msh.vertex(i))) {
        vseg[i] = iseg;
        ++nvtag;
      }
    }
  }
  
  // mark faces
  uint vt[3], fcount(0);
  const int nf = msh.nfaces();
  for (int i=0; i<nf; ++i) {
    const uint *vi = msh.face(i).vertices();
    for (int k=0; k<3; ++k)
      vt[k] = vseg[vi[k]];
    
    // common case : at least two vertices outside any box
    if ( (vt[0] == NotFound and vt[1] == NotFound) or 
         (vt[0] == NotFound and vt[2] == NotFound) or
         (vt[2] == NotFound and vt[1] == NotFound) ) 
      continue;
    
    // two vertices have equal tag
    if ( vt[0] == vt[1] ) {
      msh.face(i).tag(t + vt[0]);
      ++fcount;
    } else if ( vt[0] == vt[2] ) {
      msh.face(i).tag(t + vt[0]);
      ++fcount;
    } else if ( vt[1] == vt[2] ) {
      msh.face(i).tag(t + vt[1]);
      ++fcount;
    }
  }
  return t + nseg;
}

