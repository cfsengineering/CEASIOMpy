
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

#ifndef SURF_PENTAGROW_H
#define SURF_PENTAGROW_H

#include <genua/trimesh.h>
#include <genua/mxmesh.h>
#include <genua/ndpointtree.h>
#include <genua/logger.h>
#include <boost/atomic.hpp>

/** Hybrid prismatic mesh generation.

  PentaGrow generates a layer of pentahedral elements between a triangular
  surface mesh and an automatically constructed envelope surface placed at a
  suitable distance. It is meant to be used to quickly create meshes appropriate
  for the solution of the Reynolds-Averaged Navier-Stokes equations around
  aircraft configurations or similar geometries.

  The algorithms are described in:

  D. Eller, M. Tomac:
  "Implementation and evaluation of automated tetrahedral–prismatic mesh
  generation software."
  Computer-Aided Design, July 2015.
  <a href="http://www.sciencedirect.com/science/article/pii/S0010448515000901">
  doi:10.1016/j.cad.2015.06.010 </a>

  \ingroup meshgen
  \sa MxMesh, TriMesh
*/
class PentaGrow : public MxMesh, public Logger
{
public:
  /// empty object
  PentaGrow() {}

  /// initialize from wall mesh
  PentaGrow(const TriMesh &m);

  /// set configuration options
  void configure(const ConfigParser &cfg);

  /// maximum permitted section tag value
  static int maximumTagValue()
  {
    return std::numeric_limits<int>::max();
  }

  /// maximum permitted number of boundary triangles
  static uint maximumTriangleCount()
  {
    return std::numeric_limits<int>::max();
  }

  /// generate the outermost layer
  void generateShell(int hiter, int niter, int ncrititer,
                     int laplaceiter, bool symmetry = false, Real y0 = 0);

  /// number of wall nodes
  size_t nWallNodes() const { return mwall.nvertices(); }

  /// extrude between wall and envelope, return prism layer mesh section index
  uint extrude(bool curvedGrowth, bool symmetry = false, Real y0 = 0);

  /// adapt wall from refined outer shell (from tetgen)
  void adaptWall(const DVector<uint> &faceTags);

  /// read tetgen result and collect face tags
  void readTets(const std::string &basename);

  /// export boundaries to tetgen smesh file
  void writeTetgen(const std::string &fname, const TriMesh &farf,
                   const PointList<3> &holes, const TriMesh &refr = TriMesh(),
                   Real nearBoxEdge = 0.0, bool symmetry = false, Real y0 = 0);

  /// reduce memory footprint by erasing all working data (only raw mesh left)
  void shrink();

  /// check volume elements in final mesh for positive volume
  size_t countNegativeVolumes(std::ostream &msg);

  /// compute bounding box of wall mesh
  void envelopeBounds(Vct3 &plo, Vct3 &phi) const;

  /// check whether axis-aligned ellipsoid encloses all envelope vertices
  bool ellipsoidEncloses(const Vct3 &ctr, const Vct3 &hax) const;

  /// used to suggest near-field refinement factor: envelope edge lengths
  void envelopeEdgeStats(Real &lmean, Real &lmax) const;

  /// compute prism quality histogram and write to file
  Vector prismQualitySumCos(const std::string &fname,
                            uint isection, uint nbin = NotFound) const;

  PointList<3> getouterlayer()
  {
    return vout;
  }

  PointList<3> getouterlayeryplane_ordered(Real y0 = 0);

#ifdef HAVE_NLOPT

  /// setup local coordinate system and bound constraints for NLOPT
  void initializeBounds(double *x, double *lbound, double *ubound);

  /// NLOPT constraint for pentahedron inversion
  double inversionConstraint(const double *x, double *grad) const;

  /// NLOPT constraint for pentahedron self-intersection
  double intersectionConstraint(const double *x, double *grad) const;

  /// NLOPT objective for pentahedron quality
  double qualityObjective(const double *x, double *grad) const;

  /// call NLOPT to generate optimal envelope geometry
  void optimizeEnvelope();

#endif // HAVE_NLOPT

  // write outermost layer to file (debugging)
  void writeShell(const std::string &fname);

  // test connectivity
  void debugConnect();

private:
  enum VertexCategory
  {
    Undefined = 0,
    Concave = 1,
    Convex = 2,
    Conical = 4,
    Corner = 8,
    Ridge = 16,
    StrongCurvature = 32,
    Sharp = 64,
    Saddle = (Concave | Convex),                          // == 3
    ConcaveCorner = (Corner | Concave),                   // == 9
    ConvexCorner = (Corner | Convex),                     // == 10
    SaddleCorner = (Corner | Saddle),                     // == 11
    ConeDipp = (Concave | Corner | Conical),              // == 13
    ConeTip = (Convex | Corner | Conical),                // == 14
    BluntCorner = (Corner | Saddle | Conical),            // == 15
    Trench = (Ridge | Concave),                           // == 17
    ConvexEdge = (Ridge | Convex),                        // == 18
    Wedge = (Ridge | Convex | Concave),                   // == 19
    RidgeConeTip = (Convex | Conical | Ridge),            // == 22
    LeadingEdgeIntersection = (Trench | StrongCurvature), // == 49
    TrailingEdgeIntersection = (SaddleCorner | Sharp),    // == 83
    CriticalCorner = 512,
    Flat = 1024,
    Anything = -1
  };

  /// extract wall from global mesh
  void extractWall(const MxMesh &gm);

  /// classify and rank vertices
  void classify(bool symmetry = false, Real y0 = 0);
  // void classify();

  /// determine initial wall normals
  void adjustRidgeNormals(bool symmetry = false, Real y0 = 0);

  /// test whether a vertex is exactly of a certain category
  bool isClass(size_t i, int cat) const
  {
    return (i < vtype.size()) and (vtype[i] == cat);
  }

  /// test whether a vertex has at least a certain category
  bool hasClass(size_t i, int cat) const
  {
    return (i < vtype.size()) and ((vtype[i] & cat) == cat);
  }

  /// test for convexity, returns positive values for convex features
  Real convexity(const Vct3 &p1, const Vct3 &n1,
                 const Vct3 &p2, const Vct3 &n2)
  {
    return arg(p2 - p1, n1) + arg(p1 - p2, n2) - PI;
  }

  /// test for convexity, returns positive values for convex features
  Real convexity(uint i1, uint i2)
  {
    return convexity(mwall.vertex(i1), wfn[i1],
                     mwall.vertex(i2), wfn[i2]);
  }

  /// smooth thickness of prismatic layers
  void smoothThickness(Vector &lyt, int niter) const;

  /// compute wall mesh edge length statistics around node k
  void edgeLengthStats(uint k, Real &lmean, Real &lmax, Real &lmin) const;

  /// determine suitable normalized pattern for prism heights
  void prismPattern(Real rhfirst, Real rhlast, Vector &xpp) const;

  /// determine wall point for outer mesh point pout
  Vct3 projectToWall(const TriMesh &mout,
                     const Vct3 &pout, uint inear) const;

  /// determine corresponding wall mesh vertex
  Vct3 findWallVertex(const TriMesh &oldShell,
                      const TriMesh &newShell, uint niShell) const;

  /// rebuild search tree using current set of outer-layer vertices
  void rebuildTree();

  /// find all outer-layer nodes closer than r to p
  void findNeighbors(const Vct3 &p, Real r, Indices &neighbors) const
  {
    assert(nodeTree.npoints() == vout.size());
    neighbors.clear();
    nodeTree.find(Vct3f(p), r, neighbors);
  }

  /// find collision candidates using normal criterion
  bool collisions(Indices &colliding, uint iwall, Real safety,
                  Real nrmdev = cos(rad(60.)), Real fnrmdev = cos(rad(120.))) const;

  /// just test for collisions using normal criterion, do not collect neighbors
  int collisions(uint iwall, Real safety = 1.2, Real nrmdev = cos(rad(60.)),
                 Real fnrmdev = cos(rad(120.))) const;

  /// extract section tag from tetgen tag
  uint32_t extractSectionTag(uint32_t tag) const
  {
    return id2section[tag];
  }

  /// extract element tag from tetgen tag
  uint32_t extractElementTag(uint32_t tag) const
  {
    return id2index[tag];
  }

  /// build vertex-to-vertex connectivity for the surface
  void edgeMap(ConnectMap &map) const;

  /// generalized nodal smoothing.
  template <class Container>
  void smooth(const ConnectMap &map, Container &c) const
  {
    typedef typename Container::value_type ItemType;
    Container b(c);
    const size_t n = map.size();
    ConnectMap::const_iterator itr, last;

    // #pragma omp parallel for
    for (size_t i = 0; i < n; ++i)
    {
      ItemType sum;
      sum = 0.0;
      int nsum = 0;
      last = map.end(i);
      for (itr = map.begin(i); itr != last; ++itr)
      {
        sum += c[*itr];
        ++nsum;
      }
      if (nsum > 0)
        b[i] = 0.5 * c[i] + (0.5 / nsum) * sum;
    }

    c.swap(b);
  }

  /// generalized nodal smoothing.
  template <class Container, class WritePred, class ReadPred>
  void smooth(const ConnectMap &map, Container &c,
              const WritePred &writeNode,
              const ReadPred &readNode) const
  {
    typedef typename Container::value_type ItemType;
    Container b(c);
    const size_t n = map.size();
    ConnectMap::const_iterator itr, last;

    // #pragma omp parallel for
    for (size_t i = 0; i < n; ++i)
    {
      if (not writeNode(i))
        continue;
      ItemType sum;
      sum = 0.0;
      int nsum = 0;
      last = map.end(i);
      for (itr = map.begin(i); itr != last; ++itr)
      {
        if (readNode(*itr))
        {
          sum += c[*itr];
          ++nsum;
        }
      }
      if (nsum > 0)
        b[i] = 0.5 * c[i] + (0.5 / nsum) * sum;
    }

    c.swap(b);
  }

  /// Laplace smoothing of outer shell node coordinates
  void smoothShellNodes(const Vector &lyt, int niter, Real omega = 0.5);

  /// compute barycenter of local neighborhood of node k
  Vct3 nbBarycenter(const PointList<3> &pts, size_t k) const;

  /// reduce edge twist
  int untangle(Vector &lyt, int niter, Real permitted_etwist);

  /// reduce penta warp
  void unwarp(int niter, Real permitted_angle, bool symmetry = false, Real y0 = 0);

  /// resolve indirect collisions
  void uncollide(int niter, Real safety, Real retraction, Real limitphi,
                 Real limitphif, bool symmetry = false, Real y0 = 0);

  /// uncollide a single vertex (nucleus function for parallelization)
  uint uncollideVertex(uint i, Vector &lyt, Real safety,
                       Real retraction, Real cphi, Real cphif);

  /// ring-2 smoothing of affected vertices in untangle/unwarp/uncollide
  void retractNeighbors(const Indices &afv, Vector &lyt, int ring = 3);

  /// extrude a single vertex (nucleaus for parallelization)
  void extrudeVertex(int ivx, int nl, Real hi,
                     bool curvedGrowth, PointGrid<3> &grid) const;

  /// optionally initialize, then distribute wall normal transition parameters
  void smoothWallTransition(int niter);

  /// augment a set of vertices with its direct neighbors
  void mergeNeighbors(Indices &idx) const;

  /// attempt to untangle remaining tangled pentahedra
  size_t untangleGrid(PointGrid<3> &grid);

  /// add pentahedral elements to mesh, return mesh section index
  uint appendPrismLayer(const PointGrid<3> &grid);

  /// determine vertex normals for envelope
  void updateShellNormals(bool symmetry = false, Real y0 = 0);

  /// move grid vertices to the barycenter of their neighborhood
  void centerGridNodes(uint niter, PointGrid<3> &grid) const;

  /// move grid vertices to the barycenter of their neighborhood, single pass
  void centerGridNodesPass(const PointGrid<3> &cgrid, PointGrid<3> &grid) const;

  /// find nodes which are part of prismatic and tetrahedral region
  void findEnvelopeNeighbors(Indices &interfaceNodes,
                             Indices &nearTetNodes) const;

private:
  /// Task for parallel resolution of indirect collisions
  class UncollideTask
  {
  public:
    UncollideTask(PentaGrow &pg, Vector &lyt,
                  Real safety, Real retract, Real cphi, Real cphif)
        : m_pg(pg), m_lyt(lyt), m_safety(safety), m_retract(retract),
          m_cphi(cphi), m_cphif(cphif) { m_ncol.store(0); }
    void operator()(uint a, uint b)
    {
      int sum = 0;
      for (uint i = a; i < b; ++i)
      {
        uint n = m_pg.uncollideVertex(i, m_lyt, m_safety, m_retract, m_cphi,
                                      m_cphif);
        sum += n;
        if (n > 0)
          m_afv.push_back(i);
      }
      m_ncol += sum; // atomic
    }
    const Indices &affected() const { return m_afv; }
    uint ncollisions() const { return m_ncol.load(); }

  private:
    PentaGrow &m_pg;
    Vector &m_lyt;
    Real m_safety, m_retract, m_cphi, m_cphif;
    boost::atomic<int> m_ncol;
    Indices m_afv;
  };

  /// Task for parallel extrusion of prismatic mesh grid
  class ExtrusionTask
  {
  public:
    ExtrusionTask(const PentaGrow &pg, PointGrid<3> &grid,
                  uint nl, Real hi, bool curved)
        : m_pg(pg), m_grid(grid), m_hi(hi), m_nl(nl), m_curved(curved) {}
    void operator()(uint a, uint b)
    {
      for (uint i = a; i < b; ++i)
        m_pg.extrudeVertex(i, m_nl, m_hi, m_curved, m_grid);
    }

  private:
    const PentaGrow &m_pg;
    PointGrid<3> &m_grid;
    Real m_hi;
    uint m_nl;
    bool m_curved;
  };

private:
  /// wall mesh (must be watertight)
  TriMesh mwall;

  /// smoothed wall normals
  PointList<3> wfn;

  /// outermost layer
  PointList<3> vout;

  /// vertex normals for outer layer
  PointList<3> envNormals;

  /// local wall coordinate system for optimization
  PointList<3> fudir, fvdir;

  /// target height values for NLOPT
  Vector targetHeight;

  /// exponent factor for curved growth direction (0.0 -> straight)
  Vector invGrowthExponent;

  /// integer flag indicating vertex category
  DVector<int> vtype;

  /// integer flag indicating mesh edge category
  DVector<int> etype;

  /// maps triangle id passed to tetgen to original triangle index
  DVector<uint> id2index;

  /// maps triangle id passed to tetgen to section index
  DVector<uint> id2section;

  /// mesh tags which contain wall boundary
  Indices wallTags, farTags;

  /// search tree for nodes in the outer layer
  NDPointTree<3, float> nodeTree;

  /// tags surface nodes which resulted in tangled grid nodes
  std::vector<bool> gridBaseTangled;

  /// Feature angle for geometrical identification
  Real cosFeatureAngle;

  /// Angle for concave/convex identification
  Real cosconcave;

  /// cosine of angle limit for classification as sharp (default 150deg)
  Real cosSharpAngle;

  /// farfield section generated by adaptWall
  MxMeshSection farfieldSection;

  /// configuration parameters
  Real firstCellHeight, maxRelHeight, maxAbsHeight, maxExpansionFactor;

  /// maximum time to be used by numerical optimization (default 30 seconds)
  Real maxOptimizationTime;

  /// growth exponent factor : make this larger for improved wall-normality
  Real defaultInvGrowthExp;

  /// configuration parameters
  int numPrismLayers;

  /// whether to log function values during optimization
  bool chattyOptimization;

  /// whether to attamept grid untangling or not (default - yes)
  bool attemptGridUntangling;
};

#endif // PENTAGROW_H
