
#include <genua/mxmesh.h>
#include <genua/timing.h>
#include <genua/configparser.h>
#include <genua/binfilenode.h>

#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{

  try {

    // timing
    Wallclock clk;

    if (argc < 2 or argc > 4) {
      cerr << argv[0] << " basename [expansion] [iterations]" << endl;
      return -2;
    }

    Real xpf = 1.2;
    int niter = 32;
    if (argc > 2)
      xpf = atof(argv[2]);
    if (argc > 3)
      niter = atoi(argv[3]);

    string basename(argv[1]);

    clk.start();
    MxMesh msh;
    DVector<uint> ftags;
    msh.readTetgen(basename, &ftags);
    clk.stop();
    cout << "Reading tetgen mesh: " << clk.elapsed() << endl;

    clk.start();
    msh.fixate();
    clk.stop();
    cout << "Building node connectivity: " << clk.elapsed() << endl;

    ConnectMap map;
    msh.v2vMap(map);

    clk.start();
    size_t nv = msh.nnodes();
    Vector ledg(nv);
    for (size_t i=0; i<nv; ++i) {
      ConnectMap::const_iterator itr, last = map.end(i);
      int nnb = map.size(i);
      if (nnb > 1) {
        for (itr = map.begin(i); itr != last; ++itr)
          ledg[i] += norm(msh.node(*itr) - msh.node(i));
        ledg[i] /= (nnb - 1);
      }
    }
    clk.stop();
    cout << "Mean edge length computation: " << clk.elapsed() << endl;

    clk.start();
    Vector a(ledg), b(nv);
    for (int j=0; j<niter; ++j) {
      for (size_t i=0; i<nv; ++i) {
        b[i] = 0.5*a[i];
        Real ai = a[i];
        ConnectMap::const_iterator itr, last = map.end(i);
        Real sum = 0;
        for (itr = map.begin(i); itr != last; ++itr)
          sum += std::min( ai, xpf*a[*itr] );
        b[i] += 0.5*sum / map.size(i);
      }
      a.swap(b);
    }
    clk.stop();
    cout << "Edge metric smoothing: " << clk.elapsed() << endl;

    // debug
    int nprint = 10;
    for (int i=0; i<nprint; ++i) {
      size_t idx = rand() % nv;
      cout << "Original: " << ledg[idx] << " smoothed: " << a[idx] << endl;
    }

    string mtrfile = append_suffix(basename, ".mtr");
    ofstream os(mtrfile.c_str());
    os << nv << " 1" << endl;
    for (size_t i=0; i<nv; ++i)
      os << a[i] << endl;

    int nbc = msh.nbocos();
    while (nbc > 0) {
      msh.eraseBoco(nbc-1);
      --nbc;
    }

    // create mesh for visualization
    MxMesh viz;
    viz.appendNodes( msh.nodes() );

    Indices itri;
    for (uint i=0; i<msh.nsections(); ++i) {
      const MxMeshSection &sec( msh.section(i) );
      if (sec.elementType() == Mx::Tri3) {
        const Indices &nds( sec.nodes() );
        itri.insert(itri.end(), nds.begin(), nds.end());
      } else {
        viz.appendSection(sec.elementType(), sec.nodes());
      }
    }
    viz.appendSection(Mx::Tri3, itri);

    viz.appendField("MeanEdgeLength", ledg);
    viz.appendField("GradedEdgeLength", a);
    BinFileNodePtr bfp = viz.toXml(true).toGbf(true);
    bfp->write("visu.zml", BinFileNode::CompressedLZ4);


  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
