
#include <iostream>
#include <fstream>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <genua/mxmesh.h>
#include <genua/pattern.h>
#include <genua/dbprint.h>
#include <surf/delaunaycore.h>
#include <surf/dcplanegeometry.h>
#include <surf/uvmapping.h>
#include <surf/airfoil.h>
#include <surf/linearsurf.h>
#include <surf/uvmapdelaunay.h>
#include <surf/dcmeshcrit.h>

using namespace std;

// FIXME
// Insertion of edge midpoint is not optimal: Midpoint can be outside the
// initial mesh (when s,t-domain initialized with bounding quads) so that
// location query fails.
//
// -> insertion outside handled in DelaunayCore (buggy?)
// Problem with this approach : Newly inserted vertex outside the region does
// not lie on edge in (s,t) domain; hence, edge is not split and criterion is
// not fulfilled. On the next pass, edge will be "split" again and the already
// existing vertex inserted again -> convergence towards mesh which does not
// fullfill criteria.
// OPTION: split boundary edge, insert otherwise

class MappedDelaunay
{
public:

  /// setup empty object
  MappedDelaunay(SurfacePtr p) : psf(p), geo(0.0,1.0), core(geo) {}

  /// initialize mapping
  void initMapping(const Vector &up, const Vector &vp)
  {
    Real tmin, tmax;
    uvm.init(*psf, up, vp);
    uvm.boundaries(tmin, tmax);
    tmin = std::min(0.0, tmin) - 0.125;
    tmax = std::max(1.0, tmax) + 0.125;
    geo.quantRange(tmin, tmax);
    geo.pointTolerance( 1e-6 );
  }

  /// initialize (0,1)x(0,1) with two triangles
  void initQuad() {
    core.clear();
    uint c1 = append( vct(0.0, 0.0) );
    uint c2 = append( vct(1.0, 0.0) );
    uint c3 = append( vct(1.0, 1.0) );
    uint c4 = append( vct(0.0, 1.0) );
    core.addFace(c1, c2, c3);
    core.addFace(c1, c3, c4);
    core.fixate();
    // core.legalizeEdge(c1, c3, c2);
    // core.legalizeEdge(c1, c3, c4);
  }

  /// insert vertex, return flag
  int insertVertex(const Vct2 & uv) {
    uint c = append(uv);
    return core.insertVertex(c);
  }

  /// just append vertex, do not insert into triangulation
  uint append(const Vct2 & uv) {
    Vct3 S, Su, Sv;
    psf->plane(uv[0], uv[1], S, Su, Sv);
    pxy.push_back( S );
    pnm.push_back( cross(Su,Sv) );
    puv.push_back(uv);
    Vct2 st = vct( uv[0], uvm.eval(uv[0], uv[1]) );
    return geo.stInsertVertex(st);
  }

  /// split boundary edges which violate criteria
  uint refineBoundaries(Real sqlmax, Real sqlmin, Real mincphi) {
    int nsplit = 0;
    const int nface = core.nAllFaces();
    for (int i=0; i<nface; ++i) {
      if (not core.face(i).valid())
        continue;

      const uint *vi = core.face(i).vertices();
      bool didSplit = false;
      for (int k=0; k<3; ++k) {
        uint s = vi[k];
        uint t = vi[ (k+1)%3 ];
        Real eln = sq( pxy[s] - pxy[t] );
        Real cphi = cosarg(pnm[s], pnm[t]);
        if (eln > sqlmax or cphi < mincphi) {
          DcEdge *pe = core.findEdge(s,t);
          if (pe->degree() < 2) {
            uint c = append(0.5*(puv[s] + puv[t]));
            core.splitEdge(pe, c);
            didSplit = true;
            ++nsplit;
          }
        }
        if (didSplit)
          break;
      }
    }

    return nsplit;
  }

  /// single refinement pass
  uint refineInternal(Real sqlmax, Real sqlmin, Real mincphi) {
    int nsplit = 0;
    const int nface = core.nAllFaces();
    for (int i=0; i<nface; ++i) {
      if (not core.face(i).valid())
        continue;

      const uint *vi = core.face(i).vertices();
      Real eln[3], elmax(0);
      int esplit = -1;
      for (int k=0; k<3; ++k) {
        uint s = vi[k];
        uint t = vi[ (k+1)%3 ];
        eln[k] = sq( pxy[s] - pxy[t] );
        if (eln[k] > elmax) {
          esplit = k;
          elmax = eln[k];
        }
      }

      if (elmax > sqlmax) {
        // dbprint("Splitting edge with length", sqrt(elmax), "limit", sqrt(sqlmax));
        splitInternalEdge( vi[esplit], vi[(esplit+1)%3] );
        ++nsplit;
        continue;
      }

      // compare nodal surface normals
      for (int k=0; k<3; ++k) {
//        if (eln[k] < sqlmin)
//          continue;
        uint s = vi[k];
        uint t = vi[ (k+1)%3 ];
        Real cphi = cosarg(pnm[s], pnm[t]);
        if (cphi < mincphi) {
          // dbprint("Splitting edge with phi = ", deg(acos(cphi)));
          splitInternalEdge(s, t);
          ++nsplit;
          break;
        }
      }
    }

    return nsplit;
  }

  /// write 3D mesh to file
  void dump(const std::string & fname) const {
    MxMesh mx;
    mx.appendNodes( pxy );
    Indices tri;
    core.triangles(tri);
    mx.appendSection(Mx::Tri3, tri);
    mx.toXml(true).zwrite(fname + "_xy.zml");

    const PointList<2> & pst(geo.stVertices());
    PointList<3> psm(pst.size());
    for (uint i=0; i<psm.size(); ++i)
      psm[i] = vct(  pst[i][0], pst[i][1], 0.0 );
    mx.nodes() = psm;
    mx.toXml(true).zwrite(fname + "_st.zml");
  }

private:

//  /// split triangle
//  void splitFace(DcFace *pf) {
//    Real elen[3];
//    const uint *vi = pf->vertices();
//    for (int k=0; k<3; ++k) {
//      uint s = vi[k];
//      uint t = vi[ (k+1)%3 ];
//      elen[k] = sq( pxy[s] - pxy[t] );
//    }
//    if (elen[0] > elen[1] and elen[0] > elen[2])
//      splitEdge(vi[0], vi[1]);
//    else if (elen[1] > elen[0] and elen[1] > elen[2])
//      splitEdge(vi[1], vi[2]);
//    else
//      splitEdge(vi[0], vi[2]);
//  }

  /// split edge
  void splitInternalEdge(uint s, uint t) {
    Vct2 uvmid = 0.5*( puv[s] + puv[t] );
    uint c = append(uvmid);
    DcEdge *pe = core.findEdge(s, t);

    // test : split only boundaries
    if (pe == 0 or pe->degree() < 2)
      return;

    int stat = core.insertVertex(c);
    if (stat == DelaunayCore::ExtendedOutward)
      dbprint("Inserted vertex beyond mesh: ", puv[c]);

//    if (pe != 0 and pe->degree() < 2) {
//      dbprint("Edge split at ", uvmid);
//      core.splitEdge(pe, c);
//    } else {
//      int stat = core.insertVertex(c);
//      dbprint("Vertex inserted at ", uvmid, pe->degree(), stat);
//      if (stat >= DcGeometry::OnVertex1 and stat <= DcGeometry::OnVertex3) {
//        const PointList<2> & pst( geo.vertices() );
//        dbprint("pre uv", uvmid, "st", pst[c]);
//        Vct2 dst( 0.5*(pst[s] + pst[t]) - pst[c] );
//        dbprint("stmid", 0.5*(pst[s] + pst[t]), "duv", uvm.uvStep(uvmid, dst));
//        uvmid += uvm.uvStep(uvmid, dst);
//        c = append(uvmid);
//        dbprint("post uv", uvmid, "st", pst[c]);
//        //core.splitEdge(pe, c);
//      }
//    }
  }

private:

  /// underlying surface
  SurfacePtr psf;

  /// vertices in (u,v) space, (s,t) space stored in geo
  PointList<2> puv;

  /// vertices in physical space
  PointList<3> pxy;

  /// normal directions in physical space
  PointList<3> pnm;

  /// plane Delaunay geometry object operating in the (s,t) plane
  DcPlaneGeometry geo;

  /// Delaunay core data structures
  DelaunayCore core;

  /// mapping from (u,v) to (s,t)
  UvMapping uvm;
};

int main(int argc, char *argv[])
{
  try {

    // construct a tapered swept wing
    const Real lambda = 0.2;
    const Real sweep = rad(70.);

    CurvePtrArray cpa(2);
    {
      Airfoil *af = new Airfoil("TipAirfoil");
      af->naca4(0.0, 0.3, 0.12);
      af->scale(lambda);
      af->translate( tan(sweep), 1.0, 0.0 );
      af->apply();
      cpa[0] = CurvePtr(af);
    }

    {
      Airfoil *af = new Airfoil("RootAirfoil");
      af->naca4(0.0, 0.3, 0.12);
      af->scale(1.0);
      af->translate( 0.0, 0.0, 0.0 );
      af->apply();
      cpa[1] = CurvePtr(af);
    }

    LinearSurf *lsf = new LinearSurf("SweptWing");
    lsf->init(cpa);
    SurfacePtr psf(lsf);

    // generate patterns including surface boundaries, will not work
    // for degenerate surfaces which end in a point (derivatives vanish)
    Vector up, vp;
    airfoil_pattern(80, 0.5, 1.1, 1.1, up);
    vp = equi_pattern(8, 0.0, 1.0);

    cout << "up : " << up << endl;

    UvMapping uvm;
    uvm.init(*psf, up, vp);

    // visualization of the mapping [u,v] -> [s,t]
    // map the (u,v) grid [0,1]^2 to the [s,t] domain and write out as
    // a quad mesh to observe stretch and skew factors

    const int nu = up.size(); // 64;
    const int nv = 24;
    PointList<3> pts(nu*nv);
    for (int j=0; j<nv; ++j) {
      Real v = Real(j) / (nv-1);
      for (int i=0; i<nu; ++i) {
        Real u = up[i]; // Real(i) / (nu-1);
        Real t = uvm.eval(u,v);
        // cout << "u,v: " << u << ',' << v << " t: " << t << endl;
        pts[j*nu+i] = vct(u, t, 0.0);  // s == u

        // debug
        if (j == 0 or j == nv-1) {
          Vct3 S, Su, Sv;
          lsf->plane(u, v, S, Su, Sv);
          Vct2 buv = uvm.mappingCriteria<3>(Su, Sv);
          Vct2 fuv = uvm.gradient(u, v);
          cout << "u " << u << " v " << v << " t " << t
               << " fu " << buv[0] << ", " << fuv[0]
               << " fv " << buv[1] << ", " << fuv[1] << endl;
        }

      }
    }

    MxMesh mx;
    mx.appendNodes(pts);

    const uint nq = (nu-1)*(nv-1);
    Indices quads(4*nq);
    for (int j=0; j<nv-1; ++j) {
      for (int i=0; i<nu-1; ++i) {

        uint off = 4*( j*(nu-1) + i );
        quads[off + 0] = j*nu + i;
        quads[off + 1] = j*nu + i+1;
        quads[off + 2] = (j+1)*nu + i+1;
        quads[off + 3] = (j+1)*nu + i;
      }
    }

    mx.appendSection(Mx::Quad4, quads);
    mx.toXml(true).zwrite("mapped.zml");

    // return 0;

//    MappedDelaunay mpd(psf);
//    mpd.initMapping(up, vp);
//    mpd.initQuad();

    const Real lmax = 0.1;
    const Real lmin = 0.001;
    const Real phimax = 20.0;
    const int npass = 16 ;
//    for (int i=0; i<npass; ++i) {
//      uint nref = mpd.refineBoundaries(sq(lmax), sq(lmin), cos(rad(phimax)));
//      if (i > 3 and nref < 3)
//        break;
//      // uint nref = mpd.refinePass(sq(lmax), sq(lmin), cos(rad(phimax)));
//      cout << "********BPass " << i << " split " << nref << " edges." << endl;
//    }

//    for (int i=0; i<npass; ++i) {
//      uint nref = mpd.refineInternal(sq(lmax), sq(lmin), cos(rad(phimax)));

//      // uint nref = mpd.refinePass(sq(lmax), sq(lmin), cos(rad(phimax)));
//      cout << "********RPass " << i << " split " << nref << " edges." << endl;
//      if (i > 3 and nref < 3)
//        break;
//    }

//    mpd.dump("refined");

    // test library implementation
    UvMapDelaunay umd(psf, up, vp);
    umd.twoQuads();

    Wallclock clk;
    clk.start();

    DcMeshCrit mc;
    mc.xyzLength(lmax, lmin);
    mc.uvLength(0.02, 0.05);
    mc.maxNormalAngle(rad(phimax));


//    clk.stop();
//    cout << "UvMapDelaunay setup: " << clk.elapsed() << endl;
//    clk.start();

//    mc.npass(npass);
//    umd.refineBoundaries(mc);

//    mc.npass(4);
//    for (int i=0; i<8; ++i) {
//      umd.refineInternal(mc);
//      umd.smooth(1, 0.5);
//    }

//    clk.stop();
//    cout << "UvMapDelaunay refinement: "
//         << umd.stVertices().size() / clk.elapsed() << " vertices/s" << endl;



    mc.npass(npass);
    umd.refineBoundaries(mc);
    umd.refineInternal(mc);

    clk.stop();
    cout << "UvMapDelaunay refinement: "
         << umd.stVertices().size() / clk.elapsed() << " vertices/s" << endl;

    clk.start();
    umd.smooth(1, 0.5);
    clk.stop();
    cout << "UvMapDelaunay smoothing: "
         << umd.stVertices().size() / clk.elapsed() << " vertices/s" << endl;


    MxMesh umx;
    umx.appendNodes( umd.xyzVertices() );
    Indices tri;
    umd.triangles(tri);
    umx.appendSection( Mx::Tri3, tri );
    umx.toXml(true).zwrite("uvmaprefined.zml");

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}
