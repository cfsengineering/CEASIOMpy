
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
 
#include <genua/algo.h>
#include <genua/trimesh.h>
#include <genua/xcept.h>
#include "tritetwriter.h"

using namespace std;

// -------------------- file-scope helper functions ----------------------------

static void ttWriteString40(ostream & os, const string & s)
{
  char block[40];
  std::fill(block, block+40, ' ');
  std::copy(s.begin(), min(s.end(), s.begin()+40), block);
  int nb = host2network(int32_t(40));
  os.write((const char *) &nb, 4);
  os.write(block, 40);
  os.write((const char *) &nb, 4);
}

static void ttWriteString72(ostream & os, int tag, const string & s)
{
  char block[72];
  std::fill(block, block+72, ' ');
  std::copy(s.begin(), min(s.end(), s.begin()+72), block);
  int nb = host2network(int32_t(76));
  int ntag = host2network(int32_t(tag));
  os.write((const char *) &nb, 4);
  os.write((const char *) &ntag, 4);
  os.write(block, 72);
  os.write((const char *) &nb, 4);
}

static void ttWriteArray(ostream & os, int n, int *a)
{
  int nb = host2network(int32_t(4*n));
  host2network<4>(4*n, (char *) a);
  os.write((const char*) &nb, 4);
  os.write((const char*) a, 4*n);
  os.write((const char*) &nb, 4);
}

static void ttWriteArray(ostream & os, const Vct3 & p)
{
  float pf[3];
  pf[0] = (float) p[0];
  pf[1] = (float) p[1];
  pf[2] = (float) p[2];
  int nb = host2network( (int32_t) sizeof(pf) );
  host2network<4>(12, (char *) pf);
  os.write((const char*) &nb, 4);
  os.write((const char*) pf, sizeof(pf));
  os.write((const char*) &nb, 4);
}

static void ttWriteFace(ostream & os, int tag, const TriFace & f)
{
  uint v[4];
  const uint *vi = f.vertices();
  v[0] = tag+1;
  for (int k=0; k<3; ++k)
    v[k+1] = vi[k] + 1;
  int nb = host2network( (int32_t) sizeof(v) );
  host2network<4>(16, (char *) v);
  os.write((const char*) &nb, 4);
  os.write((const char*) v, sizeof(v));
  os.write((const char*) &nb, 4);
}

// -----------------------------------------------------------------------------

TritetWriter::TritetWriter(const TriMesh & m, const std::string & name) : msh(m)
{
  ibnd.resize(msh.nfaces());
  fill(ibnd.begin(), ibnd.end(), 0);
  bnames.push_back(name);
}

void TritetWriter::setBoundary(const std::string & bname, const Indices & idx)
{
  uint ib = bnames.size();
  bnames.push_back(bname);
  const int ni(idx.size());
  assert(uint(ni) <= msh.nfaces());
  for (int i=0; i<ni; ++i) {
    assert(idx[i] < ibnd.size());
    ibnd[idx[i]] = ib;
  }
}

void TritetWriter::setBoundary(const std::string & bname, int n1, int n2)
{
  uint ib = bnames.size();
  bnames.push_back(bname);
  assert(uint(n1) <= msh.nfaces());
  assert(uint(n2) <= msh.nfaces());
  for (int i=n1; i<n2; ++i) 
    ibnd[i] = ib;
}
    
void TritetWriter::write(std::ostream & os) const
{
  if (msh.nfaces() != ibnd.size())
    throw Error("TritetWriter: Incompatible array of boundary flags.");
  
  int tmp[2];
  tmp[0] = tmp[1] = 3;
  ttWriteString40(os, casename);
  ttWriteArray(os, 1, tmp);
  
  const int nb(bnames.size());
  tmp[0] = 15;
  tmp[1] = nb;
  ttWriteArray(os, 2, tmp);
  for (int i=0; i<nb; ++i) 
    ttWriteString72(os, i+1, bnames[i]);
  
  const int np(msh.nvertices());
  tmp[0] = 1;
  tmp[1] = np;
  ttWriteArray(os, 2, tmp);
  for (int i=0; i<np; ++i)
    ttWriteArray(os, msh.vertex(i));
  
  const int nf(msh.nfaces());
  tmp[0] = 4;
  tmp[1] = nf;
  ttWriteArray(os, 2, tmp);
  for (int i=0; i<nf; ++i) 
    ttWriteFace(os, ibnd[i], msh.face(i));
}

void TritetWriter::sphericalFarfield(Real radius, int nref)
{
  // determine mesh center 
  Vct3 fn;
  const int nf(msh.nfaces());
  Real a, asum(0);
  for (int i=0; i<nf; ++i) {
    const TriFace & f(msh.face(i));
    a = f.normal(fn);
    asum += a;
    mctr += a*f.center();
  }
  mctr /= asum;
  
  TriMesh ffm;
  ffm.sphere(mctr, radius, nref);
  msh.merge(ffm);
  msh.fixate();
  
  // tag farfield as such 
  Indices nbnd(msh.nfaces());
  std::copy(ibnd.begin(), ibnd.end(), nbnd.begin());
  nbnd.swap(ibnd);
  
  setBoundary("Farfield", nf, msh.nfaces());
}

void TritetWriter::writeTetgen(std::ostream & os) const
{
  // write nodes without markers
  os << "# " << casename << endl;
  os << "# boundary mesh for tetgen" << endl; 
  os << endl;
  
  const int nv(msh.nvertices());
  const int nf(msh.nfaces());
  os.precision(16);
  os << scientific;
  
  os << "# node list" << endl;
  os << nv << " 3 0 0" << endl;
  for (int i=0; i<nv; ++i)
    os << i+1 << " " << msh.vertex(i) << endl;
  os << endl;
    
  os << "# facet list" << endl;
  os << nf << " 1" << endl;
  for (int i=0; i<nf; ++i) {
    const uint *vi = msh.face(i).vertices();
    os << "3 " << vi[0]+1 << " " << vi[1]+1 
       << " " << vi[2]+1 << " " << ibnd[i]+1 << endl;
  }
  os << endl;
  
  os << "# hole list" << endl;
  os << "1" << endl;
  os << "1 " << mctr << endl;
  os << endl;
  
  os << "# region attribute list" << endl;
  os << "0" << endl;
  os << endl;
}
