
#include <genua/dyntritree.h>
#include <genua/timing.h>
#include <genua/point.h>

#include <iostream>

using namespace std;

Real rnd()
{
  return Real( rand() ) / RAND_MAX;
}

template <uint ND, class FloatType>
void random_pointlist(PointList<ND,FloatType> & vtx)
{
  const uint n = vtx.size();

  // random points
  for (uint i=0; i<n; ++i) {
    for (uint k=0; k<ND; ++k)
      vtx[i][k] = FloatType( rand() ) / RAND_MAX;
  }
}

void random_elements(uint nv, Indices & elix)
{
  const int n = elix.size();
  for (int i=0; i<n; ++i)
    elix[i] = rand() % nv;
}

void random_triangles(uint nt, PointList<2> & vtx, Indices & tri)
{
  vtx.resize( 3*nt );
  tri.resize( 3*nt );

  const Real ds = sqrt(1.0 / nt);
  for (uint i=0; i<nt; ++i) {
    Vct2 ctr( vct(rnd(), rnd()) );
    for (int k=0; k<3; ++k) {
      vtx[3*i+k] = ctr + ds*vct(rnd(), rnd());
      tri[3*i+k] = 3*i+k;
    }
  }
}

int main(int argc, char *argv[])
{
  int ntri = 6;
  if (argc > 1)
    ntri = strtol(argv[1], 0, 10);

//  const int nv = 2*ntri;
//  PointList<2> pts(nv);
//  random_pointlist(pts);

//  Indices idx(3*ntri);
//  random_elements(nv, idx);

  PointList<2> pts;
  Indices idx;
  random_triangles(ntri, pts, idx);

  DynTriTree tree;
  tree.assign(&pts, &idx);
  tree.build();
  tree.dbPrintTree();
  cout << "Quality: " << tree.leafSqArea() << endl;

  cout << "-----------------------------------------------------------" << endl;

  DynTriTree dtr;
  dtr.assign(&pts, &idx);
  for (int i=0; i<ntri; ++i)
    dtr.insert(i);
  dtr.dbPrintTree();
  cout << "Quality: " << dtr.leafSqArea() << endl;

  return 0;
}
