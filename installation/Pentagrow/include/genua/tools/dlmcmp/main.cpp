
#include "tritree.h"
#include "lntree.h"
#include <genua/primitives.h>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/dbprint.h>
#include <genua/mxsolutiontree.h>
#include <iostream>
#include <vector>

using namespace std;

// modal masses from reference FEM model
const Real modal_mass[] = { 3.231377E-01, 5.419183E-02, 1.104151E-02,
                            6.331079E-03, 3.182613E-03, 5.984415E-03,
                            3.955968E-03, 3.529855E-02, 3.433663E-03,
                            4.981222E-04 };

// default scaling factor according to AK, unless overwritten on command-line
Real disp_scale = 0.05;

static inline Real scale_factor(const std::string &fieldName)
{
  const char *key = "Mode ";
  const char *pos =  strstr(fieldName.c_str(), key);
  if (pos == 0)
    return 1.0;

  pos += 5;
  char *tail;
  int modeIdx = strtod(pos, &tail);
  if (tail == pos)
    return 1.0;

  --modeIdx;
  if (modeIdx >= 0 and modeIdx < 10)
    return disp_scale*sqrt( modal_mass[modeIdx] );

  return 1.0;
}

struct LineIntersection
{
  Vct2f uv[2];   // (u,v) barycentric triangle coordinates
  uint elix[2];  // global indices of lower and upper triangle
  uint qix;      // original quad4 element index
};

typedef std::vector<LineIntersection> LineIsecArray;

template <uint ND>
static void eval_mean(const MxMesh &mx,
                      const MxMeshField &f,
                      const LineIntersection &lni,
                      SVector<ND> &vpi)
{
  SVector<ND> val[2], xm;
  Real uvw[3];
  for (int k=0; k<2; ++k) {
    uvw[0] = lni.uv[k][0];
    uvw[1] = lni.uv[k][1];
    uvw[2] = 1.0 - uvw[0] - uvw[1];
    val[k] = 0;
    uint nv, isec;
    const uint *v = mx.globalElement(lni.elix[k], nv, isec);
    assert(nv == 3);
    for (int m=0; m<3; ++m) {
      f.value(v[m], xm);
      val[k] += uvw[m] * xm;
    }
  }
  Real cfd_scale = scale_factor( f.name() );
  if (cfd_scale == 1.0)
    cout << "[w] Dubious scale factor for mean field: " << f.name() << endl;
  vpi = cfd_scale*0.5*(val[1] + val[0]);
}

static Real eval_difference(const MxMesh &mx,
                            const MxMeshField &f,
                            const LineIntersection &lni)
{
  Real val[2], xm;
  Real uvw[3];
  for (int k=0; k<2; ++k) {
    uvw[0] = lni.uv[k][0];
    uvw[1] = lni.uv[k][1];
    uvw[2] = 1.0 - uvw[0] - uvw[1];
    val[k] = 0;
    uint nv, isec;
    const uint *v = mx.globalElement(lni.elix[k], nv, isec);
    assert(nv == 3);
    for (int m=0; m<3; ++m) {
      f.scalar(v[m], xm);
      val[k] += uvw[m] * xm;
    }
  }
  Real cfd_scale = scale_factor( f.name() );
  if (cfd_scale == 1.0)
    cout << "[w] Dubious scale factor for difference field: "
         << f.name() << endl;
  return cfd_scale*(val[1] - val[0]);
}

static uint generate_field(const LineIsecArray &lisa,
                           const MxMesh &cfd, uint ifield,
                           MxMesh &dlm, uint idlm)
{
  const MxMeshField & f( cfd.field(ifield) );
  const int nd = f.ndimension();
  const size_t nn = dlm.nnodes();
  const size_t nlp = lisa.size();

  Real refval(0.0);
  Real meandelta(0.0);

  uint icf;
  if (nd == 1) {

    // field of interpolated values cf and differences df
    Vector  cf(nn), df(nn);
    for (size_t i=0; i<nlp; ++i) {
      Real vo, vp;
      uint nv, isec, elix = lisa[i].qix;
      vp = eval_difference(cfd, f, lisa[i]);
      const uint *v = dlm.globalElement(elix, nv, isec);
      for (uint k=0; k<nv; ++k) {
        cf[v[k]] = vp;
        dlm.field(idlm).scalar(v[k], vo);
        df[v[k]] = (vp - vo); // / vo;
        refval += sq(vo);
        meandelta += sq(vp - vo);
      }
    }

    cout << f.name() << " Relative delta: " << meandelta / refval << endl;

    icf = dlm.appendField( f.name() + " CFD", cf );
    dlm.appendField( f.name() + " Delta", df );

  } else if (nd >= 3) {

    PointList<3>  cf(nn), df(nn);
    for (size_t i=0; i<nlp; ++i) {
      SVector<3> vp, vo;
      uint nv, isec, elix = lisa[i].qix;
      eval_mean(cfd, f, lisa[i], vp);
      const uint *v = dlm.globalElement(elix, nv, isec);
      for (uint k=0; k<nv; ++k) {
        cf[v[k]] = vp;
        dlm.field(idlm).value(v[k], vo);
        df[v[k]] = (vp - vo); // / norm(vo);
      }
    }

    icf = dlm.appendField( f.name() + " CFD", cf );
    dlm.field(icf).valueClass( MxMeshField::ValueClass::Eigenmode );
    dlm.appendField( f.name() + " Delta", df );

  } else {
    throw Error("ND-Array not handled in difference mapping.");
  }

  return icf;
}

void cleanup_fields(MxMesh &mx)
{
  const int nf = mx.nfields();
  for (int i=(nf-1); i>=0; --i) {
    const string & fname( mx.field(i).name() );
    if ( (fname.find("Mode 1") == string::npos
         and fname.find("Mode 2") == string::npos)
         or fname.find("Mode 10") != string::npos)
      mx.eraseField(i);
  }
}

int main(int argc, char *argv[])
{
  if (argc < 3) {
    cerr << "Usage: " << argv[0] << " aereldata.zml cfddata.zml [cfd-scale]" << endl;
    return EXIT_FAILURE;
  }

  if (argc > 3)
    disp_scale = atof(argv[3]);
  cout << "Scaling CFD pressure delta by " << disp_scale << endl;

  try {

    MxMesh dlm;
    dlm.loadAny(argv[1]);
    cleanup_fields(dlm);

    MxMesh cfd;
    cfd.loadAny(argv[2]);
    cleanup_fields(cfd);

    // build search tree from all triangles which belong to wall BCs
    TriTree cfdTree;
    Indices cfdElementMap;
    {
      PointList<3,float> tvx( cfd.nodes() );
      Indices triangles;
      for (uint j=0; j<cfd.nbocos(); ++j) {
        if ( cfd.boco(j).bocoType() != Mx::BcWall )
          continue;
        uint isec = cfd.mappedSection(j);
        if (isec == NotFound)
          continue;
        const MxMeshSection &sec( cfd.section(isec) );
        if (sec.elementType() != Mx::Tri3)
          continue;
        cout << "Using mesh section: " << sec.name() << endl;
        uint offset = sec.indexOffset();
        uint ne = sec.nelements();
        triangles.insert(triangles.end(),
                         sec.nodes().begin(), sec.nodes().end());
        for (uint i=0; i<ne; ++i)
          cfdElementMap.push_back( offset+i );
      }

      if (triangles.empty()) {
        for (uint j=0; j<cfd.nsections(); ++j) {
          const MxMeshSection &sec( cfd.section(j) );
          if (sec.elementType() != Mx::Tri3)
            continue;
          cout << "Using mesh section: " << sec.name() << endl;
          uint offset = sec.indexOffset();
          uint ne = sec.nelements();
          triangles.insert(triangles.end(),
                           sec.nodes().begin(), sec.nodes().end());
          for (uint i=0; i<ne; ++i)
            cfdElementMap.push_back( offset+i );
        }
      }

      cout << triangles.size()/3 << " triangles in search tree." << endl;
      cfdTree.init(tvx, triangles);
    }

    // bounding box of the CFD mesh
    float dz = 4*(cfdTree.dop(0).maxCoef(2) - cfdTree.dop(0).minCoef(2));
    cout << "Choosing z-extend: " << dz << endl;

    // generate z-line segments at center point of quad elements of DLM mesh
    LnTree lineTree;
    Indices dlmElementMap;
    {
      PointList<3,float> tvx;
      for (uint j=0; j<dlm.nsections(); ++j) {
        const MxMeshSection &sec( dlm.section(j) );
        if (sec.elementType() != Mx::Quad4)
          throw Error("Unexpected element type, need Quad4 "
                      "elements in DLM mesh.");
        uint ne = sec.nelements();
        uint offset = sec.indexOffset();
        for (uint i=0; i<ne; ++i) {
          const uint *v = sec.element(i);
          Vct3 ctr;
          for (int k=0; k<4; ++k)
            ctr += dlm.node(v[k]);
          ctr *= 0.25;
          Vct3f lp[2];
          lp[0] = Vct3f(ctr[0], ctr[1], ctr[2] - dz);
          lp[1] = Vct3f(ctr[0], ctr[1], ctr[2] + dz);
          tvx.insert(tvx.end(), lp, lp+2);
          dlmElementMap.push_back(offset + i);
        }
      }

      cout << tvx.size()/2 << " line segments in tree." << endl;
      lineTree.init(tvx);
    }

    // determine intersections between z-line segments and CFD wall triangles
    TriTree::IndexPairArray pairs;
    cfdTree.intersect(lineTree, pairs, false);

    // sort intersections by line index
    TriTree::CompareSecond cmp;
    std::sort(pairs.begin(), pairs.end(), cmp);

    // iterate over z-line indices
    size_t ip(0), np = pairs.size();
    cout << np << " triangle-line intersections" << endl;
    LineIsecArray lisa;
    while (ip+1 < np) {
      const TriTree::IndexPair & pa( pairs[ip] );
      const TriTree::IndexPair & pb( pairs[ip+1] );

      // pa and pb must be for the same z-line segment
      if (pa.second != pb.second) {
        cout << "Line indices: " << pa.second << ", " << pb.second << endl;
        ++ip;
        continue;
      }

      // determine which point is on which side
      Vct3f isp[2], ispa, ispb;
      float ta = cfdTree.intersection(lineTree, pa, ispa);
      float tb = cfdTree.intersection(lineTree, pb, ispb);

//      if ( (ta < 0.5f) == (tb < 0.5f) ) {
//        dbprint("Intersection points on the same side of DLM mesh.");
//        ++ip;
//        continue;
//      }

      // assign such that the first element in lni is the one below the
      // DLM mesh, i.e. the one with the lower z value
      LineIntersection lni;
      uint eixa = cfdElementMap[pa.first];  // triangle index
      uint eixb = cfdElementMap[pb.first];
      if (ta < tb) {
        isp[0] = ispa;
        isp[1] = ispb;
        lni.elix[0] = eixa;
        lni.elix[1] = eixb;
      } else {
        isp[0] = ispb;
        isp[1] = ispa;
        lni.elix[0] = eixb;
        lni.elix[1] = eixa;
      }
      assert(isp[0][2] < isp[1][2]);

      // fetch barycentric triangle coordinates for intersection point
      for (int k=0; k<2; ++k) {
        uint nv, isec;
        Vct3f tri[3];
        const uint *v = cfd.globalElement(lni.elix[k], nv, isec);
        for (int m=0; m<3; ++m)
          tri[m] = cfd.node(v[m]);
        qr_project_point(tri, isp[k], lni.uv[k]);
      }

      lni.qix = dlmElementMap[ pa.second ];
      lisa.push_back(lni);

      // next pair
      ip += 2;
    }

    cout << "Identified " << lisa.size() << " point pairs." << endl;
    if (lisa.empty())
      return EXIT_FAILURE;

    // process fields : for each field in the DLM mesh, search for one in the
    // CFD mesh which has the same name and use that to generate the difference
    // field.
    MxSolutionTreePtr psroot = dlm.solutionTree();
    if (psroot != nullptr) {
      for (uint j=0; j<psroot->children(); ++j) {
        MxSolutionTreePtr pssub = psroot->child(j);
        const Indices &fields( pssub->fields() );
        for (uint i=0; i<fields.size(); ++i) {
          const string &fieldname = dlm.field(fields[i]).name();
          uint icfd = cfd.findField(fieldname);
          if (icfd == NotFound) {
            // cout << "Field named '" << fieldname
            //     << "' not found in CFD mesh." << endl;
            continue;
          }
          uint idlm = generate_field(lisa, cfd, icfd, dlm, fields[i]);
          pssub->appendField( idlm );
          pssub->appendField( idlm+1 );
        }
      }
    } else {
      cout << "No solution structure found in DLM mesh: " << argv[1] << endl;
    }

    dlm.writeAs("diff.zml", Mx::NativeFormat, 1);

  } catch (Error &xcp) {
    cerr << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}

