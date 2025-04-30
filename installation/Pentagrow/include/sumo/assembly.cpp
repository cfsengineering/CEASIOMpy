
/* ------------------------------------------------------------------------
 * file:       assembly.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Collection of all surfaces belonging to a model
 * ------------------------------------------------------------------------ */

#include <QDebug>

#include <algorithm>
#include <genua/mxmesh.h>
#include <genua/sysinfo.h>
#include <genua/transformation.h>
#include <surf/igesfile.h>
#include <surf/igesentity.h>
#include <surf/iges406.h>
#include <surf/iges308.h>
#include <surf/iges314.h>
#include <surf/iges124.h>
#include <surf/iges408.h>
#include "version.h"
#include "pool.h"
#include "assembly.h"

using namespace std;

Assembly::Assembly() : CmpAssembly(), tgRadius(0.0), tgQuality(1.4)
{
  mxm = boost::make_shared<MxMesh>();
  append( BodySkeletonPtr(new BodySkeleton) );
  append( WingSkeletonPtr(new WingSkeleton) );
}

ComponentPtr Assembly::sumoComponent(uint i) const
{
  ComponentPtr cmp;
  cmp = boost::dynamic_pointer_cast<Component>( component(i) );
  assert(cmp);
  return cmp;
}

WingSkeletonPtr Assembly::asWing(uint i) const
{
  return boost::dynamic_pointer_cast<WingSkeleton>( component(i) );
}

BodySkeletonPtr Assembly::asBody(uint i) const
{
  return boost::dynamic_pointer_cast<BodySkeleton>( component(i) );
}

bool Assembly::isWing(uint i) const
{
  return (boost::dynamic_pointer_cast<WingSkeleton>( component(i) ) != 0);
}

uint Assembly::addWing(const WingSkeletonPtr & sp)
{
  AsyComponentPtr acp = boost::dynamic_pointer_cast<AsyComponent>(sp);
  assert(acp);
  return append( acp );
}

uint Assembly::addBody(const BodySkeletonPtr & sp)
{
  AsyComponentPtr acp = boost::dynamic_pointer_cast<AsyComponent>(sp);
  assert(acp);
  return append( acp );
}

BodySkeletonPtr Assembly::body(uint i) const
{
  BodySkeletonPtr bsp;
  uint ibody(0);
  for (uint j=0; j<ncomponents(); ++j) {
    bsp = boost::dynamic_pointer_cast<BodySkeleton>( component(j) );
    if (bsp) {
      if (ibody == i)
        return bsp;
      ++ibody;
    }
  }
  return bsp;
}

WingSkeletonPtr Assembly::wing(uint i) const
{
  WingSkeletonPtr wsp;
  uint iwing(0);
  for (uint j=0; j<ncomponents(); ++j) {
    wsp = boost::dynamic_pointer_cast<WingSkeleton>( component(j) );
    if (wsp) {
      if (iwing == i)
        return wsp;
      ++iwing;
    }
  }
  return wsp;
}

uint Assembly::nwings() const
{
  WingSkeletonPtr wsp;
  uint nwing(0);
  for (uint j=0; j<ncomponents(); ++j) {
    wsp = boost::dynamic_pointer_cast<WingSkeleton>( component(j) );
    if (wsp)
      ++nwing;
  }
  return nwing;
}

uint Assembly::nbodies() const
{
  BodySkeletonPtr bsp;
  uint nbody(0);
  for (uint j=0; j<ncomponents(); ++j) {
    bsp = boost::dynamic_pointer_cast<BodySkeleton>( component(j) );
    if (bsp)
      ++nbody;
  }
  return nbody;
}

SurfacePtr Assembly::surface(uint i) const
{
  return component(i)->surface();
}

void Assembly::clear()
{
  components.clear();
  jes.clear();
  csys.clear();
}

void Assembly::erase(uint k)
{
  if (k >= ncomponents())
    return;
  
  // erase corresponding engines
  string s = component(k)->name();
  if (not jes.empty()) {
    JetEngineSpecArray::iterator itr, last(jes.end());
    for (itr = jes.begin(); itr < last; ++itr) {
      if (itr->onBody(s)) {
        --last;
        swap(*itr, *last);
      }
    }
    jes.erase(last, jes.end());
  }
  
  // erase attached control surface
  for (uint j=0; j<csys.nsurf(); ++j) {
    string csn = csys.surface(j).wing();
    if (csn == s) {
      csys.removeSurface(j);
      --j;
    }
  }
  
  CmpAssembly::erase(k);
}

void Assembly::globalScale(Real f)
{
  for (size_t i=0; i<components.size(); ++i)
    sumoComponent(i)->globalScale(f);
}

void Assembly::globalTranslation(const Vct3 &trn)
{
  for (size_t i=0; i<components.size(); ++i)
    sumoComponent(i)->globalTranslate(trn);
}

void Assembly::loadAndReplace(const std::string & fname)
{
  clear();
  loadAndAppend(fname);
}

void Assembly::loadAndAppend(const std::string & fname, const Vct3 &trn)
{
  XmlElement xe;
  xe.read(fname);
  fromXml(xe);
  globalTranslation(trn);
}

void Assembly::updateJetEngines()
{
  for (uint i=0; i<jes.size(); ++i)
    jes[i].adaptToMesh(mesh());
}

XmlElement Assembly::toXml() const
{
  XmlElement xe("Assembly");
  xe["sumo_version"] = str(SUMO_VERSION);
  if (id != "")
    xe["name"] = id;
  
  xe["ppMaxStretch"] = str(ppMaxStretch);
  xe["ppMaxPhi"] = str(deg(2*ppMaxPhi));
  xe["ppNiter"] = str(ppIter);
  if (tgRadius > 0.0) {
    xe["tgRadius"] = str(tgRadius);
    xe["tgQuality"] = str(tgQuality);
  }
  
  for (uint i=0; i<ncomponents(); ++i)
    xe.append( component(i)->toXml() );
  
  if (csys.nsurf() > 0)
    xe.append(csys.toXml());
  
  for (uint i=0; i<jes.size(); ++i)
    xe.append(jes[i].toModelXml());
  
  return xe;
}

void Assembly::fromXml(const XmlElement & xe)
{
  // TODO: Implement importer for older file formats
  if (xe.name() != "Assembly")
    throw Error("Incompatible XML representation for Assembly: "
                +xe.name());

  if (xe.hasAttribute("name"))
    id = xe.attribute("name");
  else
    id = "";
  
  ppMaxStretch = xe.attr2float("ppMaxStretch", 5.0);
  ppMaxPhi = rad(0.5*xe.attr2float("ppMaxPhi", 30.));
  ppIter = xe.attr2int("ppNiter", 3);
  tgRadius = xe.attr2float("tgRadius", 0.0);
  tgQuality = xe.attr2float("tgQuality", 1.4);
  
  uint prever = _UINT_VERSION(1, 6, 0);
  uint filever = xe.attr2int("sumo_version", prever);
  if (filever > SUMO_VERSION) {
    clog << "Warning: File written by later sumo version." << endl;
    clog << "File writer: " << version_string(filever) << endl;
    clog << "Reader (this): " << _sumo_version << endl;
  }
  
  // need to define surfaces first
  XmlElement::const_iterator ite;
  for (ite = xe.begin(); ite != xe.end(); ++ite) {
    string ename = ite->name();
    if (ename == "BodySkeleton") {
      BodySkeletonPtr bsp(new BodySkeleton);
      bsp->fromXml(*ite);
      append(bsp);
    } else if (ename == "WingSkeleton") {
      WingSkeletonPtr wsp(new WingSkeleton);
      wsp->fromXml(*ite);
      append(wsp);
    }
  }
  
  // construct controls and engines after that
  jes.clear();
  for (ite = xe.begin(); ite != xe.end(); ++ite) {
    string ename = ite->name();
    if (ename == "ControlSystem") {
      if (filever >= _UINT_VERSION(1,0,0))
        csys.fromXml(*ite, *this);
      else
        clog << "Ignored old-style control system definition." << endl;
    } else if (ename == "JetEngineSpec") {
      JetEngineSpec spec;
      spec.fromXml(*this, *ite);
      jes.push_back(spec);
    }
  }
}

XmlElement Assembly::collectionXml() const
{
  //return CmpAssembly::toXml();

  XmlElement xe("SurfaceCollection");
  const int n = ncomponents();
  for (int i=0; i<n; ++i) {
    const Component & cp( *(sumoComponent(i)) );
    xe.append( cp.rawXml(true) );
    //    XmlElement xc(cp.surface()->toXml());
    //    xc.append(cp.criterion()->toXml());
    //    xe.append(xc);
  }
  return xe;
}

void Assembly::exportIges(const std::string & fname) const
{
  IgesFile igfile;
  igfile.nativeSystem("sumo version "+_sumo_version);
  igfile.preprocessorVersion(_sumo_version);

  // top level subfigure object
  IgesSubfigure asyfig;
  asyfig.nestingDepth(1);

  // component subfigures
  std::vector<IgesSubfigure> subfigs(ncomponents());
  for (uint i=0; i<ncomponents(); ++i) {
    
    const ComponentPtr & cmp = sumoComponent(i);
    
    int npre = igfile.nDirEntries();
    cmp->surface()->toIges(igfile);
    cmp->capsToIges(igfile);
    int npost = igfile.nDirEntries();

    // qDebug("Component %d, entries %d to %d", i, npre, npost);

    const Vct4 & rgba(cmp->pgColor());
    IgesColorDefinition cdef;
    cdef.setRGB(rgba[0], rgba[1], rgba[2]);
    int cdi = cdef.append(igfile);
    
    // subfigure for this component
    subfigs[i].rename( cmp->name()+"Part" );
    subfigs[i].nestingDepth(0);

    IgesDirectorySection & dir(igfile.directory());
    for (int j=npre; j<npost; ++j) {
      // dir.content(2*j).fixedNumber(4, 1); // level
      dir.content(2*j+1).fixedNumber(2, -cdi); // color
      subfigs[i].appendEntity(2*j+1);
    }

    qDebug("Created subfigure for %s", cmp->name().c_str());
  }

  // add all section curves separately on level 2
  for (uint i=0; i<ncomponents(); ++i) {

    const ComponentPtr & cmp = sumoComponent(i);
    BodySkeletonPtr bsp;
    bsp = boost::dynamic_pointer_cast<BodySkeleton>(cmp);
    if (bsp) {
      const int nf = bsp->nframes();
      const Vct3 & sRot( bsp->rotation() );
      for (int j=0; j<nf; ++j) {

        // could write curves with transformation instead
        CurvePtr corg = bsp->frame(j)->curve();
        CurvePtr lcpy = CurvePtr(corg->clone());
        lcpy->rotate( sRot[0], sRot[1], sRot[2] );
        lcpy->translate( bsp->origin() );
        lcpy->apply();
        
        // set level to 2
        int npre = igfile.nDirEntries();
        lcpy->toIges(igfile);
        int npost = igfile.nDirEntries();
        for (int k=npre; k<npost; ++k) {
          // dir.content(2*k).fixedNumber(4, 2); // level
          subfigs[i].appendEntity( 2*k+1 );
        }
      }
    } // bsp != 0

    WingSkeletonPtr wsp;
    wsp = boost::dynamic_pointer_cast<WingSkeleton>(cmp);
    if (wsp) {
      const int nf = wsp->nsections();
      const Vct3 & sRot( wsp->rotation() );

      Trafo3d bodyTrafo;
      bodyTrafo.rotate(wsp->rotation());
      bodyTrafo.translate(wsp->origin());

      IgesTrafoMatrix igt;
      igt.fromMatrix( bodyTrafo.matrix() );
      int tfiWsp = igt.append(igfile);

      for (int j=0; j<nf; ++j) {

        // could write curves with transformation instead
        CurvePtr corg = wsp->section(j)->curve();
        CurvePtr lcpy = CurvePtr(corg->clone());
        lcpy->rotate( sRot[0], sRot[1], sRot[2] );
        lcpy->translate( wsp->origin() );
        lcpy->apply();

        // set level to 2
        int npre = igfile.nDirEntries();
        lcpy->toIges(igfile);
        wsp->section(j)->pointsToIges(igfile, j+1, tfiWsp);
        int npost = igfile.nDirEntries();
        for (int k=npre; k<npost; ++k) {
          // dir.content(2*k).fixedNumber(4, 2); // level
          subfigs[i].appendEntity( 2*k+1 );
        }
      }
    } // wsp != 0

    // at this point, the subfigure for this component is complete
    // write its name
    IgesNameProperty nprop(cmp->name());
    int npi = nprop.append(igfile);

    // add an instance for it
    IgesSingularSubfigure cmpins;
    cmpins.subfigure( subfigs[i].append(igfile) );
    cmpins.addPropRef( npi );
    asyfig.appendEntity( cmpins.append( igfile ) );
  }

  // finally, add instance for global object
  IgesSingularSubfigure asyins;
  asyins.subfigure( asyfig.append(igfile) );
  asyins.append( igfile );

  igfile.write( fname );
}

void Assembly::processSurfaceMesh(const MgProgressPtr & mg)
{
  // call surface mesh generator first
  if (SysInfo::nthread() > 1)
    CmpAssembly::generateMesh(mg, &(SumoPool::pool()));
  else
    CmpAssembly::generateMesh(mg, 0);

  // if this failed, never mind the rest
  if (msh.nfaces() == 0)
    return;
  
  // collect current surface element tags which
  // mark the actual rigid wall of the aircraft (sorted)
  Indices twall;
  msh.allTags(twall);
  
  // mark control surface boundaries starting
  // one above the the wall tags
  csys.updateGeometry();
  int cstag = twall.back() + 1;
  const int ncs = csys.nsurf();
  for (int i=0; i<ncs; ++i)
    cstag = csys.surface(i).tagElements(msh, cstag);
  
  // let engines figure out their boundary regions
  updateJetEngines();
  
  // collect engine BC region tags
  Indices etags;
  for (uint i=0; i<jes.size(); ++i)
    jes[i].collectEngineTags(etags);
  
  // merge caps which are not engine BCs
  const int nc = ncomponents();
  const int nf = msh.nfaces();
  for (int i=0; i<nc; ++i) {
    uint mt = component(i)->mainTag();
    msh.tagName(mt, component(i)->name());
    for (int k=0; k<4; ++k) {
      uint ct = component(i)->capTag(k);
      if (ct == NotFound)
        continue;
      else if (binary_search(etags.begin(), etags.end(), ct))
        continue;
      for (int j=0; j<nf; ++j) {
        TriFace & f( msh.face(j) );
        if (uint(f.tag()) == ct)
          f.tag(mt);
      }
    }
  }
}

void Assembly::initMeshBoundaries(Real rfar, int nfar)
{
  if (msh.nfaces() == 0)
    return;
  
  // compute mesh center for farfield
  Vct3 ctr;
  Real a(0), fa;
  const int nf = msh.nfaces();
  for (int i=0; i<nf; ++i) {
    fa = 0.5*norm(msh.face(i).normal());
    ctr += fa*msh.face(i).center();
    a += fa;
  }
  ctr /= a;
  
  // generate farfield mesh
  TriMesh farf;
  farf.sphere(ctr, rfar, nfar);
  farf.reverse();
  const int fartag(1 << 30);
  farf.faceTag(fartag);
  
  // generate generically named boundaries
  tvm.initBoundaries(msh, farf);
  
  // set farfield boundary name
  uint bfar = tvm.groupByTag(fartag);
  assert(bfar != NotFound);
  tvm.boundaryGroup(bfar).rename("Farfield");
  
  // rename wall boundaries properly
  uint ibnd;
  const int nc = ncomponents();
  for (int i=0; i<nc; ++i) {
    
    const AsyComponent & cmp( *component(i) );
    
    // main surface boundary
    ibnd = tvm.groupByTag( cmp.mainTag() );
    if (ibnd != NotFound) {
      TetBoundaryGroup & bg(tvm.boundaryGroup(ibnd));
      bg.rename( cmp.name() );
      bg.boundaryCondition(TetBoundaryGroup::BcWall);
    }
    
    // cap boundaries
    for (int k=0; k<4; ++k) {
      ibnd = tvm.groupByTag( cmp.capTag(k) );
      if (ibnd != NotFound) {
        TetBoundaryGroup & bg(tvm.boundaryGroup(ibnd));
        bg.rename( cmp.name()+"Cap"+str(k+1));
        bg.boundaryCondition(TetBoundaryGroup::BcWall);
      }
    }
  }
  
  // set control surface boundaries
  const int ncs = csys.nsurf();
  for (int i=0; i<ncs; ++i) {
    int tag0, tagn;
    csys.surface(i).tags(tag0, tagn);
    const string & csn = csys.surface(i).name();
    for (int t=0; t<tagn-tag0; ++t) {
      ibnd = tvm.groupByTag(tag0+t);
      if (ibnd != NotFound) {
        TetBoundaryGroup & bg(tvm.boundaryGroup(ibnd));
        bg.rename(csn+"S"+str(t));
        bg.boundaryCondition(TetBoundaryGroup::BcEulerTransp);
      }
    }
  }
  
  // set boundary conditions for jet engines
  for (uint i=0; i<jes.size(); ++i) {
    int nin = jes[i].nintake();
    for (int j=0; j<nin; ++j) {
      
      // for each intake region, identify the index of the
      // main component to which it is assigned
      const JeRegion & r( jes[i].intakeRegion(j) );
      uint cix = find( r.srfName() );
      if (cix == NotFound)
        continue;
      
      // main engine component
      const AsyComponent & cmp(*component(cix));
      
      // figure out which boundary group corresponds to
      // the intake region
      ibnd = NotFound;
      if (r.region() == JeRegion::JerNose)
        ibnd = tvm.groupByTag( cmp.capTag(2) );
      else if (r.region() == JeRegion::JerTail)
        ibnd = tvm.groupByTag( cmp.capTag(3) );
      
      if (ibnd == NotFound)
        continue;
      
      TetBoundaryGroup & bg(tvm.boundaryGroup(ibnd));
      if (nin > 1)
        bg.rename( jes[i].name() + "Intake" + str(j+1) );
      else
        bg.rename( jes[i].name() + "Intake" );

      // FIXME Compute engine boundary conditions
      // bg.nacelleInlet( jes[i].captureAreaRatio() );
      bg.boundaryCondition(TetBoundaryGroup::BcFarfield);
    }
    
    const JeRegion & r( jes[i].nozzleRegion() );
    uint cix = find( r.srfName() );
    if (cix == NotFound)
      continue;

    // main engine component
    const AsyComponent & cmp(*component(cix));

    // figure out which boundary group corresponds to
    // the intake region
    ibnd = NotFound;
    if (r.region() == JeRegion::JerNose)
      ibnd = tvm.groupByTag( cmp.capTag(2) );
    else if (r.region() == JeRegion::JerTail)
      ibnd = tvm.groupByTag( cmp.capTag(3) );

    if (ibnd == NotFound)
      continue;

    TetBoundaryGroup & bg(tvm.boundaryGroup(ibnd));
    bg.rename( jes[i].name() + "Exhaust" );
    
    // FIXME Compute engine boundary conditions
    // bg.nacelleInlet( jes[i].captureAreaRatio() );
    bg.boundaryCondition(TetBoundaryGroup::BcFarfield);
  }
}

bool Assembly::hasVolumeMesh() const
{
  return (mxm) and (mxm->nelements() > 3);
}

XmlElement Assembly::toDwfsMesh()
{
  XmlElement xm("Mesh");
  if (csys.nsurf() > 0) {
    csys.updateGeometry();
    xm.append(csys.meshXml());
  }
  for (uint i=0; i<njet(); ++i)
    xm.append(jetEngine(i).toMeshXml());
  xm.append(mesh().toXml());
  return xm;
}

void Assembly::estimateTgParameters()
{
  if (tgQuality == 0.0)
    tgQuality = 1.4;
  if (tgRadius == 0.0) {
    tgRadius = 0.0;
    const TriMesh & sfm( mesh() );
    if (sfm.nfaces() > 0)
      tgRadius = 8.0*sqrt(sfm.area());
  }
}

