
#include <genua/implicittree.h>
#include <genua/point.h>
#include <genua/timing.h>
#include <genua/boxsearchtree.h>
#include <genua/ndpointtree.h>
#include <iostream>
#include <cstdlib>

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

// Simple point tree for testing

class PointTree
{
private:

  class Comparison {
  public:

    Comparison(const PointList<3> & pts) : vtx(pts), iax(0) {}

    // setup division criterion
    template <class Iterator>
    bool divide(uint , Iterator begin, Iterator end) {
      if (begin >= end)
        return false;
      Vct3 pmin, pmax;
      pmin = huge;
      pmax = -huge;
      for (Iterator itr = begin; itr != end; ++itr) {
        const Vct3 & p( vtx[*itr] );
        for (int k=0; k<3; ++k) {
          pmin[k] = std::min(pmin[k], p[k]);
          pmax[k] = std::max(pmax[k], p[k]);
        }
      }
      Vct3 ds = pmax - pmin;
      iax = std::distance(ds.begin(), std::max_element(ds.begin(), ds.end()));

      // cout << "Node size: " << std::distance(begin, end)
      //      << " ds " << ds << " iax " << iax << endl;

      return true;
    }

    // setup division criterion
    template <class Iterator>
    bool pdivide(uint , Iterator begin, Iterator end) {

      Vct3 pgmax, pgmin;
#pragma omp parallel
      {
        Vct3 pmin, pmax;
        pmin = huge;
        pmax = -huge;
        const int n = std::distance(begin, end);


#pragma omp for
        for (int i = 0; i<n; ++i) {
          Iterator itr = begin + i;
          const Vct3 & p( vtx[*itr] );
          for (int k=0; k<3; ++k) {
            pmin[k] = std::min(pmin[k], p[k]);
            pmax[k] = std::max(pmax[k], p[k]);
          }

        }

#pragma omp critical
        {
          for (int k=0; k<3; ++k) {
            pgmax[k] = std::max(pgmax[k], pmax[k]);
            pgmin[k] = std::min(pgmin[k], pmin[k]);
          }
        }
      }
      Vct3 ds = pgmax - pgmin;
      iax = std::distance(ds.begin(), std::max_element(ds.begin(), ds.end()));

      return true;
    }

    // true if a is to the left of b
    bool operator() (uint a, uint b) const {
      if (a == NotFound)
        return false;
      else if (b == NotFound)
        return true;
      else
        return vtx[a][iax] < vtx[b][iax];
    }

  public:

    const PointList<3> & vtx;
    int iax;
  };

public:

  PointTree(uint n) : vtx(n), itree(n,8) {
    random_pointlist(vtx);
  }

  // sort tree
  void sort() {
    Comparison cmp(vtx);
    itree.sort(cmp);
  }

public:
  PointList<3> vtx;
  ImplicitTree itree;
};


int main(int argc, char *argv[])
{
  cout << "hardware_concurrency = " << std::thread::hardware_concurrency() << endl;

  Wallclock clk;

#ifdef NDEBUG
  const uint np = 5000000;
#else
  const uint np = 100000;
#endif

  {
    PointList<3> vf(np);
    random_pointlist(vf);
    clk.start("Sorting BSearchTree... ");
    BSearchTree btree(vf);
    clk.stop("done.");
    cout << "BSearchTree: " << btree.nTreeNodes() << " nodes." << endl;

    // time nearest()
    clk.start("Locating nearest points... ");
    for (uint i=0; i<np/4; ++i) {
      uint idx = rand() % np;
      uint inear = btree.nearest( vf[idx] );
      if (idx != inear)
        cout << "Mismatch: " << idx << " != " << inear << endl;
    }
    clk.stop("done. ");
    cout << (np/4) / clk.elapsed() << " points/s" << endl;
  }

  // test single-precision version
  PointList3f vf(np);
  random_pointlist(vf);

  NDPointTree<3,float> ndt;
  clk.start("Allocating NDPointTree... ");
  uint nn = ndt.allocate( vf, true, 8 );
  clk.stop("done. ");
  cout << "NDPointTree: " << nn << " nodes." << endl;
  clk.start("Sorting NDPointTree... ");
  ndt.sort();
  clk.stop("done.");

  // test nearest()
  uint idx = np/3;
  uint inear = ndt.nearest( vf[idx] );
  cout << "Searched " << idx << ", found " << inear << endl;

  // time nearest()
  clk.start("Locating nearest points... ");
  for (uint i=0; i<np/4; ++i) {
    uint idx = rand() % np;
    uint inear = ndt.nearest( vf[idx] );
    if (idx != inear)
      cout << "Mismatch: " << idx << " != " << inear << endl;
  }
  clk.stop("done. ");
  cout << (np/4) / clk.elapsed() << " points/s" << endl;

  // test find()
  Indices fref, found;
  const Vct3f & px( vf[rand()%np] );
  double radius = 0.02;

  clk.start();
  ndt.find(px, radius, found);
  clk.stop();
  cout << "Neighborhood search: " << clk.elapsed() << endl;

  // do a linear search for comparison
  for (uint i=0; i<np; ++i) {
    if ( sq(vf[i] - px) < sq(radius) )
      fref.push_back( i );
  }
  std::sort(found.begin(), found.end());

  if (fref.size() != found.size()) {
    cout << "Number of points found does not match: "
         << found.size() << ", " << fref.size() << endl;
  } else {
    uint nmm(0);
    for (uint i=0; i<fref.size(); ++i) {
      if (fref[i] != found[i])
        ++nmm;
    }
    if (nmm > 0)
      cout << nmm << " mismatches. " << endl;
    else
      cout << "find() results correct: " << found.size() << endl;
  }

  return 0;
}
