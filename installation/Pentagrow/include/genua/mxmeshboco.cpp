
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#include "ffanode.h"
#include "mxmesh.h"
#include "mxmeshboco.h"
#include "dbprint.h"

// #ifdef HAVE_CGNS
#include "cgnsboco.h"
// #endif

using namespace std;

size_t MxMeshBoco::elements(Indices & idx) const
{
  if (empty())
    return 0;
  
  if (not bRange) {
    idx = bcelm;
  } else {
    uint ifirst = bcelm[0];
    uint ilast = bcelm[1];
    idx.resize(ilast-ifirst);
    for (uint i=ifirst; i<ilast; ++i)
      idx[i-ifirst] = i;
  }

  return idx.size();
}

uint MxMeshBoco::nelements() const
{
  if (empty())
    return 0;
  
  if (bRange) {
    return bcelm[1] - bcelm[0];
  } else {
    return bcelm.size();
  }
}

void MxMeshBoco::clearElements()
{
  bRange = false;
  bcelm.clear();
}

void MxMeshBoco::shiftElementIndices(int shift, uint threshold)
{
  const int ne = bcelm.size();
  for (int i=0; i<ne; ++i)
    if (bcelm[i] >= threshold)
      bcelm[i] += shift;
}

MxMeshBoco::MxMeshBoco(Mx::BocoType t, uint a, uint b)
  : MxAnnotated(), bcelm(2), bRange(true), bctype(t),
    dispColor(0.5f,0.5f,0.5f), itag(0)
{
  bcelm[0] = std::min(a,b);
  bcelm[1] = std::max(a,b);
}

void MxMeshBoco::eraseElements(uint a, uint b)
{
  assert(a <= b);

  // nothing to do if a is beyond boco range
  if (a > bcelm.back())
    return;

  // element indices beyond b reduce by this amount
  const int elix_downshift = b - a;

  if (isRange()) {

    // boco maps exactly the erased section
    if (a == bcelm[0] and b == bcelm[1]) {
      bcelm[0] = bcelm[1] = 0;
      return;
    }

    // erased index range is below this boco
    if (b <= bcelm[0]) {
      bcelm[0] -= elix_downshift;
      bcelm[1] -= elix_downshift;
      return;
    }

    // erased region overlaps
    if (a > bcelm[0] and b >= bcelm[1]) {
      bcelm[1] = a;
      return;
    } else if (a < bcelm[0] and b < bcelm[1]) {
      bcelm[0]  = b - elix_downshift; // == a
      bcelm[1] -= elix_downshift;
      return;
    }

    // erased region is in the middle of element range
    bcelm[1] = (bcelm[1] - bcelm[0]) - (b-a);
    return;

  } else {

    Indices elx;
    elx.reserve(bcelm.size());
    for (size_t i=0; i<bcelm.size(); ++i) {
      uint k = bcelm[i];
      if (k < a)
        elx.push_back(k);
      else if (k >= b)
        elx.push_back(k - elix_downshift);
    }
    bcelm.swap(elx);

  }
}

void MxMeshBoco::edgeMassflowInlet(Real mdot, Real Ttot, const Vct3 & dir)
{
  bctype = Mx::BcMassflowIn;
  
  XmlElement xe("EdgeBCData");
  xe["b_class"] = "external";
  xe["b_type"] = "mass flow inlet";
  xe["Total_mass_flow"] = str(mdot);
  xe["total_temperatur"] = str(Ttot);
  xe["flow_direction"] = str(dir);
  annotate(xe);
}

void MxMeshBoco::edgeMassflowOutlet(Real mdot)
{
  bctype = Mx::BcMassflowOut;
  
  XmlElement xe("EdgeBCData");
  xe["b_class"] = "external";
  xe["b_type"] = "mass flow outlet";
  xe["Total_mass_flow"] = str(mdot);
  annotate(xe);
}

void MxMeshBoco::toFFA(FFANode & node) const
{
  FFANode *boundary = new FFANode("boundary");
  node.append(boundary);
  FFANode *b_name = new FFANode("b_name");
  boundary->append(b_name);
  FFANode *b_class = new FFANode("b_class");
  boundary->append(b_class);
  FFANode *b_type = new FFANode("b_type");
  boundary->append(b_type);
  
  // look for edge BC data
  XmlElement::const_iterator itr;
  itr = xnote.findChild("EdgeBCData");
  bool haveEdgeData = itr != xnote.end();
  
  Vct3 fdir;
  FFANode *massflow(0), *total_temp(0), *flow_direction(0);
  switch (bctype) {
  case Mx::BcWall:
    b_class->copy("wall");
    b_type->copy("weak euler");
    b_name->copy(bcid);
    break;
  case Mx::BcFarfield:
    b_class->copy("external");
    b_type->copy("weak characteristic");
    b_name->copy(bcid);
    break;
  case Mx::BcMassflowIn:

    if (not haveEdgeData)
      throw Error("BC data for massflow inlet not defined.");

    b_class->copy("external");
    b_type->copy("mass flow inlet");
    massflow = new FFANode("Total_mass_flow");
    massflow->copy( itr->attr2float("Total_mass_flow", 0.0) );
    boundary->append(massflow);
    total_temp = new FFANode("total_temperatur");
    total_temp->copy( itr->attr2float("total_temperatur", 0.0) );
    boundary->append(total_temp);
    flow_direction = new FFANode("flow_direction");
    fromString(itr->attribute("flow_direction"), fdir);
    flow_direction->copy(3, 1, fdir.pointer());
    boundary->append(flow_direction);
    b_name->copy(bcid);
    break;

  case Mx::BcMassflowOut:

    if (not haveEdgeData)
      throw Error("BC data for massflow outlet not defined.");

    b_class->copy("external");
    b_type->copy("mass flow outlet");
    massflow = new FFANode("Total_mass_flow");
    massflow->copy(itr->attr2float("Total_mass_flow", 0.0));
    boundary->append(massflow);
    b_name->copy(bcid);
    break;
    //     case BcEulerTransp:
    //       b_class->copy("wall");
    //       b_type->copy("weak euler transp");
    //       if (bcid.substr(bcid.size()-2, bcid.size()) == ":p")
    //         b_name->copy(bcid);
    //       else
    //         b_name->copy(bcid + ":p");
    //       break;

  case Mx::BcAdiabaticWall:
    b_class->copy("wall");
    b_type->copy("weak adiabatic");
    b_name->copy(bcid);
    break;

  case Mx::BcSlipWall:
    b_class->copy("wall");
    b_type->copy("weak euler");
    b_name->copy(bcid);
    break;

  default:
    dbprint("MxMeshBoco: BC type not supported for FFA files.");
  }
}

BinFileNodePtr MxMeshBoco::gbfNode(bool share) const
{
  BinFileNodePtr np(new BinFileNode("MxMeshBoco"));
  np->attribute("boco_type", str(int(bctype)) );
  np->attribute("name", bcid);
  np->attribute("use_range", bRange ? "true" : "false");
  np->attribute("displayColor", dispColor.str());
  np->assign( bcelm.size(), &bcelm[0], share );

  if (not xnote.name().empty())
    np->append( xnote.toGbf(share) );

  return np;
}

void MxMeshBoco::fromGbf(const BinFileNodePtr & np, bool digestNode)
{
  int ftyp = Int( np->attribute("boco_type") );
  if (ftyp >= 0 and ftyp < int(Mx::BcNTypes)) {
    bctype = Mx::BocoType(ftyp);
  } else {
    throw Error("Unknown boundary condition type in binary file.");
  }
  bRange = np->attribute("use_range")  == "true";
  bcid = np->attribute("name");
  if ( np->blockTypeWidth() != sizeof(uint) )
    throw Error("Incompatible integer type in binary file.");
  bcelm.resize(np->blockElements());
  memcpy(&bcelm[0], np->blockPointer(), np->blockBytes());
  np->digest(digestNode);
}

XmlElement MxMeshBoco::toXml(bool share) const
{
  XmlElement xe("MxMeshBoco");
  xe["boco_type"] = str(bctype);
  xe["name"] = bcid;
  xe["use_range"] = bRange ? "true" : "false";
  xe["count"] = str(bcelm.size());
  xe["displayColor"] = dispColor.str();
  xe.asBinary( bcelm.size(), &bcelm[0], share);
  
  if (not xnote.name().empty())
    xe.append(xnote);
  
  return xe;
}

void MxMeshBoco::fromXml(const XmlElement & xe)
{
  bctype = Mx::decodeBocoType( xe.attribute("boco_type") );
  bRange = xe.attribute("use_range")  == "true";
  bcid = xe.attribute("name");
  if (xe.hasAttribute("displayColor"))
    dispColor.str( xe.attribute("displayColor") );
  else
    displayColor( Color(0.5f,0.5f,0.5f) );

  size_t n = Int(xe.attribute("count"));
  bcelm.resize(n);
  xe.fetch(n, &bcelm[0]);

  XmlElement::const_iterator itr, last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr) {
    const string & s = itr->name();
    if (s == "MxNote")
      xnote = *itr;
  }
}

//#ifdef HAVE_CGNS

void MxMeshBoco::readCgns(CgnsBoco & cb)
{
  cgns::BCType_t ctype = cb.bcType();
  bctype = cgns2MxBocoType(ctype);
  if (bctype == Mx::BcUndefined)
    bctype = Mx::BcUserDefined;

  CgnsIntVector pnts;
  cgns::PointSetType_t ps = cb.pointSet();
  cb.readPoints( pnts );
  if (ps == cgns::ElementList) {
    bRange = false;
    const int n = pnts.size();
    bcelm.resize( n );
    for (int i=0; i<n; ++i)
      bcelm[i] = pnts[i] - 1;
  } else if (ps == cgns::ElementRange) {
    bRange = true;
    bcelm.resize(2);
    bcelm[0] = pnts[0] - 1;
    bcelm[1] = pnts[1];
  }

  rename( cb.name() );
}

void MxMeshBoco::writeCgns(CgnsBoco & cb) const
{
  CgnsIntVector ev;
  if (bRange) {
    ev.resize(2);
    ev[0] = bcelm[0] + 1;
    ev[1] = bcelm[1];
    cb.pointSet( cgns::ElementRange );
  } else {
    const int n = bcelm.size();
    ev.resize(n);
    for (int i=0; i<n; ++i)
      ev[i] = bcelm[i] + 1;
    cb.pointSet( cgns::ElementList );
  }

  cb.bcType( MxBocoType2Cgns(bctype) );
  cb.rename( name() );
  cb.writePoints( ev );
}

void MxMeshBoco::writeAbaqus(const Indices &gid, const Indices &eid,
                             ostream &os) const
{
  // translate index set
  const int n = bcelm.size();
  Indices tix(n);
  if (bocoType() == Mx::BcElementSet) {
    os << "*Elset, name=" << name() << endl;
    if (eid.empty())
      for (int i=0; i<n; ++i)
        tix[i] = bcelm[i]+1;
    else
      for (int i=0; i<n; ++i)
        tix[i] = eid[bcelm[i]];
  } else if (bocoType() == Mx::BcNodeSet) {
    os << "*Nset, name=" << name() << endl;
    if (gid.empty())
      for (int i=0; i<n; ++i)
        tix[i] = bcelm[i]+1;
    else
      for (int i=0; i<n; ++i)
        tix[i] = gid[bcelm[i]];
  } else {
    return;
  }
  std::sort(tix.begin(), tix.end());

  // write indices
  const int blk(8);
  const int nb = n / blk;
  for (int i=0; i<nb; ++i) {
    for (int j=0; j<blk-1; ++j)
      os << tix[i*blk+j] << ", ";
    os << tix[i*blk+blk-1] << endl;
  }
  if (blk*nb < n) {
    for (int i=(blk*nb); i<n-1; ++i)
      os << tix[i] << ", ";
    os << tix[n-1];
  }
  os << endl;
}

