
#include <surf/nstmesh.h>
#include <surf/nstelements.h>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/ndpointtree.h>
#include <genua/configparser.h>
#include <genua/basicedge.h>
#include <fstream>
#include <iostream>
#include <sstream>

using namespace std;

void make_test_case()
{
  NstMesh msh;

  int nbp = 10;
  PointList3d pts(nbp);
  for (int i=0; i<nbp; ++i)
    pts[i] = Vct3(Real(i)/(nbp-1), 0.0, 0.0);
  msh.addBeams(pts, 2);

  int nu = 20, nv = 45;
  PointGrid<3> grid(nu,nv);
  for (int i=0; i<nu; ++i)
    for (int j=0; j<nv; ++j) {
      Real phi = j*2*PI/(nv-1);
      grid(i,j) = Vct3(Real(i)/(nu-1), sin(phi), cos(phi));
    }
  msh.addQuads(grid);

  ofstream os("testmesh.blk");
  msh.nstwrite(os);
}

inline uint nearest_beam(const PointList3d &vtx, const Indices &beams,
                         uint inode)
{
  const Vct3 &pt = vtx[inode];
  const size_t nb = beams.size() / 2;
  Real mindst = std::numeric_limits<Real>::max();
  uint ibest = NotFound;
  for (size_t i=0; i<nb; ++i) {
    const Vct3 &pa = vtx[beams[2*i+0]];
    const Vct3 &pb = vtx[beams[2*i+1]];
    Vct3 dab = pb - pa;
    Real t = clamp(dot(pt - pa, dab) / dot(dab, dab), 0.0, 1.0);
    Real dst = norm( pt - ((1-t)*pa + t*pb) );
    if (dst < mindst) {
      ibest = i;
      mindst = dst;
    }
  }
  return ibest;
}

int main(int argc, char *argv[])
{
  try {

    make_test_case();

    if (argc < 2) {
      cerr << "Usage: " << argv[0] << " config.txt [meshfile]" << endl;
      return EXIT_FAILURE;
    }

    ConfigParser cfg(argv[1]);
    string fname, outfile;
    if (argc > 2)
      fname = argv[2];
    else
      fname = cfg["MeshFile"];

    outfile = cfg.value("OutFile", "rconnect.blk");

    NstMesh msh;
    msh.nstread(fname);
    const Indices &gid( msh.gridids() );

    Indices beamPID, shellPID;
    {
      stringstream ss;
      ss << cfg["BeamPID"];
      uint pid;
      while (ss >> pid)
        beamPID.push_back(pid);
    }
    sort_unique(beamPID);
    {
      stringstream ss;
      ss << cfg["ShellPID"];
      uint pid;
      while (ss >> pid)
        shellPID.push_back(pid);
    }
    sort_unique(shellPID);

    // find beam elements and shell nodes
    const size_t ne = msh.nelements();
    Indices bsegs, shellNodes;
    NstBeam *pbeam;
    NstElementBase *pbase;
    for (size_t i=0; i<ne; ++i) {
      if ( msh.as(i, &pbeam) ) {
        if (binary_search(beamPID.begin(), beamPID.end(), pbeam->pid())) {
          bsegs.insert(bsegs.end(), pbeam->begin(), pbeam->end());
        }
      } else if ( msh.as(i, &pbase) ) {
        if (binary_search(shellPID.begin(), shellPID.end(), pbase->pid())) {
          const Element &e( msh.element(i) );
          shellNodes.insert(shellNodes.end(), e.begin(), e.end());
        }
      }
    }
    Indices beamNodes(bsegs);
    sort_unique(beamNodes);
    sort_unique(shellNodes);

    // keep some nodes for connections
    uint shellskip = cfg.getInt("SkipShellNodes", 1);
    if (shellskip != 1) {
      Indices tmp;
      tmp.reserve(shellNodes.size()/shellskip + 3);
      uint n = shellNodes.size();
      for (uint i=0; i<n; i += shellskip)
        tmp.push_back(shellNodes[i]);
      tmp.swap(shellNodes);
    }
    clog << "[i] " << shellNodes.size() << " nodes to connect." << endl;

    // extract method tag
    string smethod = toLower( cfg.value("Method", "beams") );
    uint eidOffset = cfg.getInt("OffsetEID", 1);

    NDPointTree<3,Real> ptree;
    PointList3d bnodes(msh.vertices(), beamNodes);
    ptree.allocate(bnodes, true);
    ptree.sort();

    // connect all shell nodes using node-to-node CBEAMS
    if (smethod == "beams") {

      const size_t nsn = shellNodes.size();
      Indices bcon(2*nsn);
#pragma omp parallel for
      for (size_t i=0; i<nsn; ++i) {
        bcon[2*i+0] = shellNodes[i];
        uint inp = ptree.nearest( msh.vertex( shellNodes[i] ) );
        bcon[2*i+1] = beamNodes[inp];
      }

      ofstream os(outfile);
      uint cpid = cfg.getInt("ConnectionBeamPID", 999);
      Vct3 bdir = cfg.getVct3("ConnectionBeamDirection", Vct3(0,0,1));
      for (size_t i=0; i<nsn; ++i) {
        uint a = gid[bcon[2*i+0]];
        uint b = gid[bcon[2*i+1]];
        os << "CBEAM, " << i+eidOffset << ", " << cpid << ", "
           << a << ", " << b << ", "
           << bdir[0] << ", " << bdir[1] << ", " << bdir[2] << endl;
      }
    } else if (smethod == "rbe3") {

      uint rbecomp = cfg.getInt("RBE3Components", 123456);

      // connect using RBE3
      typedef std::pair<uint,uint> idxpair;
      vector<idxpair> pairs;

      const size_t nsn = shellNodes.size();
      //#pragma omp parallel for
      for (size_t i=0; i<nsn; ++i) {
        uint inp = ptree.nearest( msh.vertex( shellNodes[i] ) );
        //#pragma omp critical
        pairs.emplace_back(beamNodes[inp], shellNodes[i]);
      }

      // sort such that beam node comes first
      auto cmp = [&](const idxpair &a, const idxpair &b){
        if (a.first < b.first)
          return true;
        else if (a.first > b.first)
          return false;
        else
          return (a.second < b.second);
      };
      sort(pairs.begin(), pairs.end(), cmp);

      ofstream os(outfile);
      uint bn = NotFound;
      uint ndep = 0;
      uint rbeid = eidOffset;
      const size_t np = pairs.size();
      for (size_t j=0; j<np; ++j) {
        uint bgid = pairs[j].first;
        if (bgid == bn) {
          ndep++;
          os << gid[pairs[j].second] << ", ";
          if (ndep == 2 or (ndep > 2 and (ndep-2)%8 == 0))
            os << endl << "   , ";
        } else {
          // TODO DoF identifiers
          ndep = 1;
          bn = bgid;
          os << "RBE3, " << rbeid++ << ",, "
             << gid[pairs[j].first] << ", " << rbecomp << ", 1.0, 123, "
             << gid[pairs[j].second] << ", ";
        }
      }

    } else {
      throw Error("Method not recognized.");
    }

  } catch (std::exception &x) {
    cerr << x.what() << endl;
    return EXIT_FAILURE;
  }
  return EXIT_SUCCESS;
}
