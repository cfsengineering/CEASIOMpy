
#include <genua/mxmesh.h>
#include <genua/mxmeshtypes.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{
  try {

    if (argc < 2) {
      cout << "Usage: " << argv[0] << " file.zml" << endl;
      return -1;
    }

    string infile( argv[1] );
    string outfile( append_suffix(infile, ".zml") );
    if (argc > 2)
      outfile = string(argv[2]);

    MxMesh mx;
    mx.loadAny(infile);

    // gather fields
    Indices mfields;
    for (size_t i=0; i<mx.nfields(); ++i) {
      const MxMeshField &f( mx.field(i) );
      if (f.nodal() and (f.ndimension() == 3 or f.ndimension() == 6))
        mfields.push_back(i);
    }

    // process sections, ignore anything which is not Tri3
    Indices idx;
    idx.reserve(4096);
    Vector ndarea(mx.nnodes());
    Matrix ntu(mx.nnodes(), mfields.size());
    for (size_t j=0; j<mfields.size(); ++j) {
      Vector mp(mx.nnodes());
      const MxMeshField &f(mx.field(mfields[j]));
      for (size_t i=0; i<mx.nsections(); ++i) {
        const MxMeshSection &sec( mx.section(i) );
        if (sec.elementType() != Mx::Tri3)
          continue;
        const size_t ne = sec.nelements();
        for (size_t ej=0; ej<ne; ++ej) {
          const uint *v = sec.element(ej);
          idx.insert(idx.end(), v, v+3);
          Vct3 fn = cross( mx.node(v[1])-mx.node(v[0]),
              mx.node(v[2])-mx.node(v[0]) );
          Real ar2 = normalize(fn);

          Vct3 u[3];
          for (int k=0; k<3; ++k)
            f.value(v[k], u[k]);
          Real ndu = dot(fn, (u[0]+u[1]+u[2])) * ar2 / 6.0;
          for (int k=0; k<3; ++k) {
            mp[v[k]] += ndu;
            ndarea[v[k]] += ar2 / 6.0;
          }
        }
      }
      std::copy(mp.begin(), mp.end(), ntu.colpointer(j));
      mx.appendField("ModeProjection"+str(j+1), mp);
    }
    sort_unique(idx);

    // write projections as text file for matlab
    ofstream os("mprojection.txt");
    for (size_t i=0; i<idx.size(); ++i) {
      os << idx[i];
      for (size_t j=0; j<ntu.ncols(); ++j)
        os << ' ' << ntu(idx[i], j);
      os << endl;
    }

    // check whether computed nodal sensitivities are available
    ifstream in("cps.txt");
    if (in) {
      Vector nds(mx.nnodes()), cps(mx.nnodes());
      string line;
      char *tail;
      while (getline(in, line)) {
        const char *p = line.c_str();
        uint idx = genua_strtoul(p, &tail, 10);
        if (tail == p)
          continue;
        if (idx >= mx.nnodes())
          throw Error("Node index in 'cps.txt' is out of bounds.");
        p = tail;
        nds[idx] = genua_strtod(p, &tail);
        cps[idx] = nds[idx] / ndarea[idx];
        if (tail == p)
          throw Error("Error reading file 'cps.txt' for node: "+str(idx));
      }

      mx.appendField("NodalSensitivity", nds);
      mx.appendField("CpSensitivity", cps);
    }

    mx.writeAs("results", Mx::NativeFormat, 1);

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
