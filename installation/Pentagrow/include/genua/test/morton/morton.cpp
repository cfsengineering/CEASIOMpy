
#include <genua/morton.h>
#include <genua/timing.h>
#include <genua/point.h>
#include <genua/trimesh.h>
#include <genua/mxmesh.h>

#include <iostream>

using namespace std;

template <uint ND, class FloatType>
void random_pointlist(PointList<ND,FloatType> & vtx)
{
  uint n = vtx.size();
  // random points
  for (uint i=0; i<n; ++i) {
    vtx[i][0] = FloatType( rand() ) / RAND_MAX;
    vtx[i][1] = FloatType( rand() ) / RAND_MAX;
    vtx[i][2] = FloatType( rand() ) / RAND_MAX;
  }
}

void random_elements(uint nv, Indices & elix)
{
  const int n = elix.size();
  for (int i=0; i<n; ++i)
    elix[i] = rand() % nv;
}

// this exists here just to look at asm codegen
bool triangle_compare(const Indices & qvi, const Indices & elix,
                      uint a, uint b)
{
  ElementMortonLess<uint,3,3> eless(&qvi[0], &elix[0]);
  return eless(a, b);
}

// test
template <class UIntType, int ND, int NV>
void icenter(const UIntType *qiv, const UIntType *eli, uint a, uint b,
             UIntType actr[], UIntType bctr[])
{
  for (int i=0; i<ND; ++i)
    actr[i] = bctr[i] = 0;

  const UIntType *avi = &eli[a*NV];
  const UIntType *bvi = &eli[b*NV];
  for (int i=0; i<NV; ++i) {
    const UIntType *pa = &qiv[ND*avi[i]];
    const UIntType *pb = &qiv[ND*bvi[i]];
    for (int k=0; k<ND; ++k) {
      actr[k] += pa[k];
      bctr[k] += pb[k];
    }
  }
}

class FloatCtrLess
{
public:

  FloatCtrLess(const PointList<2,float> & pts, const Indices & vi)
    : vtx(pts), tri(vi) {}

  bool operator()(uint a, uint b) const {
    const uint *va = &tri[3*a];
    const uint *vb = &tri[3*b];
    Vct2f ca, cb;
    for (int k=0; k<3; ++k) {
      ca += vtx[va[k]];
      cb += vtx[vb[k]];
    }

    FloatMortonLess<float,2> fless;
    return fless(ca.pointer(), cb.pointer());
  }

private:
  const PointList<2,float> & vtx;
  const Indices & tri;
};

int main(int argc, char *argv[])
{
  typedef SVector<2,uint> IPoint;

  // very simple test problem
  {
    const int n = 4;
    std::vector<IPoint> vtx(n*n);
    for (int i=0; i<n; ++i) {
      for (int j=0; j<n; ++j) {
        vtx[i*n+j][0] = i;
        vtx[i*n+j][1] = j;
      }
    }

    MortonLess<uint,2> iless;
    std::sort(vtx.begin(), vtx.end(), iless);
    cout << "Ordering for " << n << 'x' << n << " points" << endl;
    for (uint i=0; i<vtx.size(); ++i) {
      cout << i << " : " << vtx[i] << endl;
    }
  }

  const int ns = 1800;
  const int np = ns*ns;
  PointGrid<3> pg(ns,ns);
  for (int j=0; j<ns; ++j) {
    Real y = Real(j) / (ns-1);
    for (int i=0; i<ns; ++i) {
      Real x = Real(i) / (ns-1);
      pg(i,j) = vct(x, y, 0.0);
    }
  }

  TriMesh msh;
  msh.triangulate(pg);
  const int nf = msh.nfaces();
  Indices elix;
  elix.reserve(3*nf);
  for (int i=0; i<nf; ++i) {
    const uint *vi = msh.face(i).vertices();
    elix.insert(elix.end(), vi, vi+3);
  }

  // quantize vertices
  SVector<2,Real> plo, phi;
  plo = std::numeric_limits<Real>::max();
  phi = -plo;
  for (int i=0; i<np; ++i) {
    for (int k=0; k<2; ++k) {
      plo[k] = std::min(plo[k], pg[i][k]);
      phi[k] = std::max(phi[k], pg[i][k]);
    }
  }

  SVector<2> iscal;
  for (int k=0; k<2; ++k)
    iscal[k] = Real( (1 << 30) ) / (phi[k] - plo[k]);
  cout << "inv scale: " << iscal << endl;

  Wallclock clk;
  clk.start();
  std::vector<IPoint> qvi(np);
  for (int i=0; i<np; ++i) {
    for (int k=0; k<2; ++k)
      qvi[i][k] = (int) ((pg[i][k] - plo[k]) * iscal[k]);
  }
  clk.stop();

  cout << "Quanitization: " << qvi.size() / clk.elapsed()
       << " points/s" << endl;

  // test
  uint a = 17 % nf;
  uint b = 133 % nf;
  IPoint actr, bctr;
  icenter<uint,2,3>(qvi[0].pointer(), &elix[0], a, b,
                    actr.pointer(), bctr.pointer());
  cout << "Triangle " << a << " fctr: " << 3.0*msh.face(a).center()
       << " ictr: " << actr << endl;
  cout << "Triangle " << b << " fctr: " << 3.0*msh.face(b).center()
       << " ictr: " << bctr << endl;

  // element indices to sort
  const int ne = elix.size() / 3;
  Indices idx(ne);
  for (int i=0; i<ne; ++i)
    idx[i] = i;

  clk.start();
  ElementMortonLess<uint,2,3> triCompare(qvi[0].pointer(), &elix[0]);
  std::sort(idx.begin(), idx.end(), triCompare);
  clk.stop();
  cout << "Sorting/int: " << ne/clk.elapsed() << " triangles/s" << endl;

  for (int i=0; i<ne; ++i)
    idx[i] = i;

  PointList<2,float> pt2(np);
  for (int i=0; i<np; ++i) {
    pt2[i] = Vct2f(vct(pg[i][0], pg[i][1]));
  }

  clk.start();
  FloatCtrLess cless(pt2, elix);
  std::sort(idx.begin(), idx.end(), cless);
  clk.stop();

  cout << "Sorting/float: " << ne/clk.elapsed() << " triangles/s" << endl;

  // visualize
  if (np < 100000) {

    MxMesh mx;
    mx.appendSection(msh);

    Indices vline;
    for (int i=1; i<ne; ++i) {
      const uint a = mx.appendNode( msh.face(idx[i-1]).center() );
      const uint b = mx.appendNode( msh.face(idx[i]).center() );
      vline.push_back(a);
      vline.push_back(b);
    }
    mx.appendSection(Mx::Line2, vline);

    mx.toXml(true).zwrite("zsorted.zml");
  }

  return 0;
}
