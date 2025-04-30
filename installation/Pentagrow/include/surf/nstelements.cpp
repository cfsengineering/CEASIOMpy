
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

#include "nstelements.h"
#include "nstmesh.h"
#include <genua/meshfields.h>
#include <genua/strutils.h>

using namespace std;

int NstElementBase::s_vixoffset = 0;
int NstElementBase::s_eixoffset = 0;

void NstElementBase::index2gid(const Element &e, uint vg[]) const
{
  assert(msh != 0);
  const uint *v(e.vertices());
  const uint n(e.nvertices());
  for (uint i = 0; i < n; ++i)
    vg[i] = msh->index2gid(v[i]);
}

void NstElementBase::indexOffsets(int gidoffset, int eidoffset)
{
  s_vixoffset = gidoffset;
  s_eixoffset = eidoffset;
}

// ----------------- CMASS2 : Scalar mass element -------------------------

void NstScalarMass::nstwrite(std::ostream &os) const
{
  uint vg[2];
  index2gid(*this, vg);
  os << "CMASS2, " << id() + 1 + s_eixoffset << ", " << nstr(mss) << ", "
     << vg[0] + s_vixoffset << ", " << vdof[0] << ", " << vg[1] + s_vixoffset
     << ", " << vdof[1] << endl;
}

// ----------------- CONM2 : Concentrated mass element -----------------------

void NstConMass::nstwrite(std::ostream &os) const
{
  uint vg;
  index2gid(*this, &vg);
  os << "CONM2, " << id() + 1 + s_eixoffset << ", " << vg + s_vixoffset
     << ", 0, " << nstr(mss) << ", " << nstr(poff[0]) << ", " << nstr(poff[1])
     << ", " << nstr(poff[2]) << endl
     << "     , " << nstr(mj(0, 0)) << ", " << nstr(mj(1, 0)) << ", "
     << nstr(mj(1, 1)) << ", " << nstr(mj(2, 0)) << ", " << nstr(mj(2, 1))
     << ", " << nstr(mj(2, 2)) << endl;
}

// ----------------- CELAS2 : Scalar spring element -------------------------

void NstSpring::nstwrite(std::ostream &os) const
{
  uint vg[2];
  index2gid(*this, vg);
  os << "CELAS2, " << id() + 1 + s_eixoffset << ", " << nstr(mk) << ", "
     << vg[0] + s_vixoffset << ", " << vdof[0] << ", " << vg[1] + s_vixoffset
     << ", " << vdof[1] << endl;
}

// ----------------- RBAR : Rigid bar element -------------------------

void NstRigidBar::nstwrite(std::ostream &os) const
{
  uint vg[2];
  index2gid(*this, vg);
  os << "RBAR, " << id() + 1 + s_eixoffset << ", " << vg[0] + s_vixoffset
     << ", " << vg[1] + s_vixoffset << ", ";
  if (cna > 0)
    os << cna;
  os << ", ";
  if (cnb > 0)
    os << cnb;
  os << ", ";
  if (cma > 0)
    os << cma;
  os << ", ";
  if (cmb > 0)
    os << cmb;
  os << endl;
}

// ----------------- SimpleMpc two-point constraint -------------------------

void NstSimpleMpc::nstwrite(std::ostream &os) const
{
  if (adof[0] == NotFound)
    return;

  uint vg[2];
  index2gid(*this, vg);
  os << "MPC, " << sid << ", " << vg[0] + s_vixoffset << ", " << adof[0] << ", "
     << nstr(acf[0]) << ", " << vg[1] + s_vixoffset << ", " << bdof[0] << ", "
     << nstr(bcf[0]) << ", " << endl;

  for (int k = 1; k < 6; ++k) {
    if (adof[k] != NotFound and bdof[k] != NotFound) {
      os << "   ,  , ";
      os << vg[0] + s_vixoffset << ", " << adof[k] << ", " << nstr(acf[k])
         << ", ";
      os << vg[1] + s_vixoffset << ", " << bdof[k] << ", " << nstr(bcf[k])
         << ", ";
      os << endl;
    }
  }
}

// ----------------- CBEAM : Beam element -------------------------------------

void NstBeam::nstwrite(std::ostream &os) const
{
  uint vg[2];
  index2gid(*this, vg);
  os << "CBEAM, " << id() + 1 + s_eixoffset << ", " << pid() << ", "
     << vg[0] + s_vixoffset << ", " << vg[1] + s_vixoffset << ", "
     << nstr(orn[0]) << ", " << nstr(orn[1]) << ", " << nstr(orn[2]) << endl;
}

// ----------------- CTRIA3 : Triangular shell element -----------------------

void NstTria3::nstwrite(std::ostream &os) const
{
  uint vg[3];
  index2gid(*this, vg);
  os << "CTRIA3, " << id() + 1 + s_eixoffset << ", " << pid() << ", "
     << vg[0] + s_vixoffset << ", " << vg[1] + s_vixoffset << ", "
     << vg[2] + s_vixoffset;
  os << ", " << mcid() << endl;
}

// ----------------- CTRIAR : Triangular shell element -----------------------

void NstTriaR::nstwrite(std::ostream &os) const
{
  uint vg[3];
  index2gid(*this, vg);
  os << "CTRIAR, " << id() + 1 + s_eixoffset << ", " << pid() << ", "
     << vg[0] + s_vixoffset << ", " << vg[1] + s_vixoffset << ", "
     << vg[2] + s_vixoffset;
  os << ", " << mcid() << endl;
}

// ----------------- CTRIA6 : Triangular shell element -----------------------

void NstTria6::nstwrite(std::ostream &os) const
{
  uint vg[6];
  index2gid(*this, vg);
  os << "CTRIA6, " << id() + 1 + s_eixoffset << ", " << pid();
  for (uint i = 0; i < 6; ++i)
    os << ", " << vg[i] + s_vixoffset;
  os << endl;
  os << "      , " << mcid() << endl;
}

// ----------------- CQUAD4 : Quadrilateral shell element
// -----------------------

void NstQuad4::nstwrite(std::ostream &os) const
{
  uint vg[4];
  index2gid(*this, vg);
  os << "CQUAD4, " << id() + 1 + s_eixoffset << ", " << pid() << ", "
     << vg[0] + s_vixoffset << ", " << vg[1] + s_vixoffset << ", "
     << vg[2] + s_vixoffset << ", " << vg[3];
  os << ", " << mcid() << endl;
}

// ----------------- CQUADR : Quadrilateral shell element
// -----------------------

void NstQuadR::nstwrite(std::ostream &os) const
{
  uint vg[4];
  index2gid(*this, vg);
  os << "CQUADR, " << id() + 1 + s_eixoffset << ", " << pid() << ", "
     << vg[0] + s_vixoffset << ", " << vg[1] + s_vixoffset << ", "
     << vg[2] + s_vixoffset << ", " << vg[3] + s_vixoffset;
  os << ", " << mcid() << endl;
}

// ----------------- CQUAD8 : Quadrilateral shell element
// -----------------------

void NstQuad8::nstwrite(std::ostream &os) const
{
  uint vg[8];
  index2gid(*this, vg);
  os << "CQUAD8, " << id() + 1 + s_eixoffset << ", " << pid();
  for (uint i = 0; i < 6; ++i)
    os << ", " << vg[i] + s_vixoffset;
  os << endl
     << "      , " << vg[6] + s_vixoffset << ", " << vg[7] + s_vixoffset;
  os << ", , , , , " << mcid() << endl;
}

// ----------------- CHEXA : Hexahedral solid element -----------------------

void NstHexa::nstwrite(std::ostream &os) const
{
  if (nvertices() == 20) {
    uint vg[20];
    index2gid(*this, vg);
    os << "CHEXA, " << id() + 1 + s_eixoffset << ", " << pid();
    for (uint i = 0; i < 6; ++i)
      os << ", " << vg[i] + s_vixoffset;
    os << endl;
    for (uint i = 6; i < 14; ++i)
      os << ", " << vg[i] + s_vixoffset;
    os << endl;
    for (uint i = 14; i < 20; ++i)
      os << ", " << vg[i] + s_vixoffset;
    os << endl;
  } else {
    uint vg[8];
    index2gid(*this, vg);
    os << "CHEXA, " << id() + 1 + s_eixoffset << ", " << pid();
    for (uint i = 0; i < 6; ++i)
      os << ", " << vg[i] + s_vixoffset;
    os << endl;
    for (uint i = 6; i < 8; ++i)
      os << ", " << vg[i] + s_vixoffset;
    os << endl;
  }
}

// ----------------- CTETRA : Tetrahedral solid element -----------------------

void NstTetra::nstwrite(std::ostream &os) const
{
  if (nvertices() == 10) {
    uint vg[10];
    index2gid(*this, vg);
    os << "CTETRA, " << id() + 1 + s_eixoffset << ", " << pid();
    for (uint i = 0; i < 6; ++i)
      os << ", " << vg[i] + s_vixoffset;
    os << endl;
    for (uint i = 6; i < 10; ++i)
      os << ", " << vg[i] + s_vixoffset;
    os << endl;
  } else {
    uint vg[4];
    index2gid(*this, vg);
    os << "CTETRA, " << id() + 1 + s_eixoffset << ", " << pid();
    for (uint i = 0; i < 4; ++i)
      os << ", " << vg[i] + s_vixoffset;
    os << endl;
  }
}

// ----------------- RBE2 : Rigid-body element -----------------------

void NstRigidBody2::nstwrite(std::ostream &os) const
{
  Indices vg(nvertices());
  index2gid(*this, &vg[0]);
  const int niv(vg.size() - 1);
  os << "RBE2, " << id() + 1 + s_eixoffset << ", " << vg[0] + s_vixoffset
     << ", " << cm;

  // first line of dependent nodes
  int n1 = min(niv, 5);
  for (int i = 0; i < n1; ++i)
    os << ", " << vg[1 + i] + s_vixoffset;
  os << endl;

  // second line, if necessary
  if (niv > n1) {
    int n2 = min(niv - 5, 8);
    os << "        ";
    for (int i = 0; i < n2; ++i)
      os << ", " << vg[6 + i] + s_vixoffset;
    os << endl;
  }
}

uint NstRigidBody2::add2viz(MeshFields &m) const
{
  const uint n(nvertices());
  const uint niv(n - 1);
  const uint *v(vertices());

  uint elid(0);
  for (uint i = 0; i < niv; ++i)
    elid = m.addLine2(v[0], v[1 + i]);
  return elid;
}
