
#include <genua/csrmatrix.h>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <iostream>
#include <fstream>

using namespace std;

void rcpermute(const ConnectMap &map, const Indices &perm,
               ConnectMap &pmap)
{
  const size_t nr = map.size();
  pmap.beginCount(nr);
  for (size_t i=0; i<nr; ++i)
    pmap.incCount(perm[i], map.size(i));
  pmap.endCount();
  for (size_t i=0; i<nr; ++i) {
    uint pi = perm[i];
    const uint nc = map.size(i);
    const uint *pcol = map.first(i);
    for (uint j=0; j<nc; ++j)
      pmap.append(pi, perm[pcol[j]]);
  }
  pmap.sort();
  pmap.close();
}

void printrow(const ConnectMap &map, const Indices &perm, uint r)
{
  const uint nc = map.size(r);
  const uint *pcol = map.first(r);
  cout << "Row " << r << ", size: " << map.size(r) << " : " << endl;
  for (uint j=0; j<nc; ++j)
    cout << j << " -> " << pcol[j] << " (" << perm[pcol[j]] << ")" << endl;
  cout << endl;
}

int main(int argc, char *argv[])
{
  try {

    Wallclock clk;

    string fname("jacobian.b");
    if (argc > 1)
      fname = argv[1];

    ifstream in(fname);
    if (not in)
      throw Error("Cannot open file: "+fname);

    CsrMatrix<double> A;
    A.readBin(in);

    Indices perm, iperm;
    const ConnectMap &spty(A.sparsity());
    cout << "Calling METIS..." << endl;
    clk.start();
    bool stat = A.permuteByMetis(perm, iperm);
    clk.stop();
    cout << "METIS run time: " << clk.elapsed() << endl;

    if (not stat)
      throw Error("Call to METIS failed.");

//    ConnectMap pmap;
//    // pmap.rowpermute(perm);
//    // pmap.colpermute(perm);
//    rcpermute(spty, perm, pmap);

//    printrow(spty, perm, perm[0]);
//    printrow(pmap, perm, perm[0]);

//    uint joo = spty.index(0,0);
//    cout << "ColIndex (0,0) = " << joo << endl;
//    uint lix = pmap.lindex( perm[0], perm[joo] );
//    if (lix == NotFound)
//      cout << "Not found in pmap." << endl;
//    else
//      cout << "Found at " << lix << endl;

    ofstream out("permuted.b");
    A.writeBin(out);

    ofstream osp("permutation.txt");
    std::copy(perm.begin(), perm.end(), ostream_iterator<uint>(osp, " "));

  } catch (Error & xcp) {
    cerr << xcp.what();
    return -1;
  }

  return 0;
}
