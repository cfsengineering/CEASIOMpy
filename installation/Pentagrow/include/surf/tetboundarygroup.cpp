
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
 
#include <sstream>
#include <genua/trimesh.h>
#include "tetmesh.h"
#include "tetboundarygroup.h"

//#ifdef HAVE_CGNS
#include <genua/cgnszone.h>
#include <genua/cgnsboco.h>
//#endif

using namespace std;

TetBoundaryGroup::TetBoundaryGroup(const TriMesh & m, int tag) : itag(tag), bc(BcWall)
{
  const int nf = m.nfaces();
  for (int i=0; i<nf; ++i) {
    if (m.face(i).tag() == itag)
      ifaces.push_back(i);
  }
  
  // set default name
  stringstream ss;
  ss << "Boundary " << itag;
  bname = ss.str();
}

void TetBoundaryGroup::capture(const TetFaceArray & tfa)
{
  ifaces = IndexVector();
  const int nf = tfa.size();
  for (int i=0; i<nf; ++i) {
    if (tfa[i].tag() == itag)
      ifaces.push_back(i);
  }
}

void TetBoundaryGroup::enforce(TetFaceArray & tfa) const
{
  const int ni = ifaces.size();
  for (int i=0; i<ni; ++i)
    tfa[ifaces[i]].tag(itag);
}

void TetBoundaryGroup::facelist(const IndexVector & v, int offset)
{
  ifaces = v;
  ifaces -= offset;
}

void TetBoundaryGroup::nacelleInlet(Real eps)
{
  bc = BcNacelleInlet;
  epsfan = eps;
}

void TetBoundaryGroup::nacelleOutlet(Real pr, Real tr)
{
  bc = BcNacelleOutlet;
  pratio = pr;
  tratio = tr;
}

void TetBoundaryGroup::mdotInflow(Real tmf, Real tt, const Vct3 & direction)
{
  bc = BcMassFlowInlet;
  mdot = tmf;
  ttotal = tt;
  fdir = direction;
}
    
void TetBoundaryGroup::mdotOutflow(Real tmf)
{
  bc = BcMassFlowOutlet;
  mdot = tmf;
}

void TetBoundaryGroup::collectVertices(const TetFaceArray & faces, 
                                       IndexMatrix & vertices,
                                       bool sensible_ordering) const
{
  int nf(ifaces.size());
  if (sensible_ordering) {
    vertices.resize(3,nf);
    for (int i=0; i<nf; ++i) {
      const uint *vi = faces[ifaces[i]].vertices();
      for (int k=0; k<3; ++k) 
        vertices(k,i) = (int) (vi[k] + 1);
    }
  } else {
    vertices.resize(nf,3);
    for (int i=0; i<nf; ++i) {
      const uint *vi = faces[ifaces[i]].vertices();
      for (int k=0; k<3; ++k) 
        vertices(i,k) = (int) (vi[k] + 1);
    }
  }
}



void TetBoundaryGroup::ffamsh(const TetFaceArray & faces, FFANode & node) const
{
  // collect faces
  IndexMatrix ielm;
  collectVertices(faces, ielm, false);
  
  FFANode *boundary = new FFANode("boundary");
  FFANode *boundary_name = new FFANode("boundary_name");
//   if (bc == BcWall) {
//     if (bname.substr(bname.size()-2, bname.size()) == ":p")
//       boundary_name->copy(bname);
//     else
//       boundary_name->copy(bname + ":p");
//   } else {
//     boundary_name->copy(bname);
//   }
  
  switch (bc) {
    case BcWall:
    case BcEulerTransp:
      boundary_name->copy(bname);
      break;
    case BcFarfield:
    case BcNacelleInlet:
    case BcNacelleOutlet:
    case BcMassFlowInlet:
    case BcMassFlowOutlet:
    default:
      boundary_name->copy(bname);
  }
  
  boundary->append(boundary_name);
  FFANode *belem_group = new FFANode("belem_group");
  FFANode *bound_elem_type = new FFANode("bound_elem_type");
  bound_elem_type->copy("tria3");
  belem_group->append(bound_elem_type);
  FFANode *bound_elem_nodes = new FFANode("bound_elem_nodes");
  bound_elem_nodes->copy(ielm.nrows(), ielm.ncols(), &ielm[0]);
  belem_group->append(bound_elem_nodes);
  boundary->append(belem_group);
  node.append(boundary);
}

void TetBoundaryGroup::ffaboc(FFANode & node) const
{
  FFANode *boundary = new FFANode("boundary");
  node.append(boundary);
  FFANode *b_name = new FFANode("b_name");
  boundary->append(b_name);
  FFANode *b_class = new FFANode("b_class");
  boundary->append(b_class);
  FFANode *b_type = new FFANode("b_type");
  boundary->append(b_type);
  
  FFANode *eps_fan, *pres_ratio, *temp_ratio;
  FFANode *massflow, *total_temp, *flow_direction;
  switch (bc) {
    case BcWall:
      b_class->copy("wall");
      b_type->copy("weak euler");
      b_name->copy(bname);
      break;
    case BcFarfield:
      b_class->copy("external");
      b_type->copy("weak characteristic");
      b_name->copy(bname);
      break;
    case BcNacelleInlet:
      b_class->copy("external");
      b_type->copy("nacelle inlet");
      eps_fan = new FFANode("eps_fan");
      eps_fan->copy(epsfan);
      boundary->append(eps_fan);
      b_name->copy(bname);
      break;
    case BcNacelleOutlet:
      b_class->copy("external");
      b_type->copy("nacelle exhaust");
      pres_ratio = new FFANode("pres_ratio");
      pres_ratio->copy(pratio);
      boundary->append(pres_ratio);
      temp_ratio = new FFANode("temp_ratio");
      temp_ratio->copy(tratio);
      boundary->append(temp_ratio);
      b_name->copy(bname);
      break;
    case BcMassFlowInlet:
      b_class->copy("external");
      b_type->copy("mass flow inlet");
      massflow = new FFANode("Total_mass_flow");
      massflow->copy(mdot);
      boundary->append(massflow);
      total_temp = new FFANode("total_temperatur");
      total_temp->copy(ttotal);
      boundary->append(total_temp);
      flow_direction = new FFANode("flow_direction");
      flow_direction->copy(3, 1, fdir.pointer());
      boundary->append(flow_direction);
      b_name->copy(bname);
      break;
    case BcMassFlowOutlet:
      b_class->copy("external");
      b_type->copy("mass flow outlet");
      massflow = new FFANode("Total_mass_flow");
      massflow->copy(mdot);
      boundary->append(massflow);
      b_name->copy(bname);
      break;
    case BcEulerTransp:
      b_class->copy("wall");
      b_type->copy("weak euler transp");
      b_name->copy(bname);
      break;
    default:
      throw Error("TetBoundaryGroup: BC type not supported for FFA files.");
  }
}

//#ifdef HAVE_CGNS

void TetBoundaryGroup::cgnsBoundaryCondition(cgns::BCType_t b)
{
  switch (b) {
    case cgns::BCWall:
      bc = BcWall;
      break;
    case cgns::BCFarfield:
      bc = BcFarfield;
      break;
    case cgns::BCInflow:
      bc = BcMassFlowInlet;
      break;
    case cgns::BCOutflow:
      bc = BcMassFlowOutlet;
      break;
    default:
      bc = BcUser;
  }
}

void TetBoundaryGroup::writeCgnsBoco(CgnsZone & z, int offset)
{
  if (ifaces.empty())
    return;

  CgnsBoco cb(z.findex(), z.bindex(), z.index(), 1);
  cb.pointSet( cgns::ElementList );
  cb.rename(bname);
  switch (bc) {
    case BcWall:
      cb.bcType( cgns::BCWall );
      break;
    case BcFarfield:
      cb.bcType( cgns::BCFarfield );
      break;
    case BcNacelleInlet:
    case BcMassFlowOutlet:
      cb.bcType( cgns::BCOutflow );
      break;
    case BcNacelleOutlet:
    case BcMassFlowInlet:
      cb.bcType( cgns::BCInflow );
      break;
    case BcEulerTransp:
    case BcUser:
    default:
      cb.bcType( cgns::BCTypeUserDefined );
      break;
  }

  // apply offset
  const int ni = ifaces.size();
  CgnsIntVector idx(ni);
  for (int i=0; i<ni; ++i)
    idx[i] = ifaces[i] + offset + 1;
  cb.writePoints( idx );
}

//#endif
