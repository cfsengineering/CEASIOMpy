
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
 
#ifndef SURF_SURFINTERPOLATOR_H
#define SURF_SURFINTERPOLATOR_H

#include "dispinterpolator.h"
#include <genua/forward.h>
#include <genua/mxelementtree.h>

/** Map displacements from structural to aerodynamic surfaces.
 *
 * This object makes use of radial basis functions (RBF) to interpolate
 * structural displacements of any kind of structural mesh (even simple
 * beam models) to a wetted-surface aerodynamic mesh.
 *
 * \ingroup mapping
 * \sa RbfInterpolator
 */
class SurfInterpolator : public DispInterpolator
{
public:

  /// empty construction
  SurfInterpolator() : DispInterpolator(), m_catchRadius(1e18f),
                       m_maxNrmDev(rad(20.)), m_maxDistance(1e18),
                       m_concavityLimit(2.0),
                       m_smoothedRadius(0.0), m_smOmega(0.5f),
                       m_smoothSelective(0), m_smoothGlobal(0),
                       m_smoothedRing(1) {}

  /// virtual destructor
  virtual ~SurfInterpolator();

  /// set parameters for identification of discontinuous projections
  void jumpCriteria(Real nrmDev, Real absDst=-1);

  /// set threshold value for concavity criterion (set negative to disable)
  void concavityThreshold(Real t) {m_concavityLimit = t;}

  /// set parameters for postprocessing by selective Laplacian smoothing
  void selectiveSmoothing(int niterations, int neighborhoodRing=1,
                          float neighborhoodRadius=0.0f, float omega=0.5f) {
    m_smoothSelective = niterations;
    m_smoothedRadius = neighborhoodRadius;
    m_smoothedRing = neighborhoodRing;
    m_smOmega = omega;
  }

  /// use Galerkin method for smoothing
  void useGalerkin(bool flag) {m_useGalerkin = flag;}

  /// set parameters for postprocessing by global Laplacian smoothing
  void globalSmoothing(int niterations) {
    m_smoothGlobal = niterations;
  }

  /// build mapping tree from given list of sections, or all shell elements
  void buildTreeFromSections(const Indices &sections = Indices());

  /** Build tree from shell elements with PID.
   *  Assemble search tree from structural shell elements which conform to
   *  a certain pattern. If \a pidwet is not empty, then all shell elements which
   *  have a PID in that set are used. If, on the other hand, \a pidintern is
   *  not empty, then all shell elements which have one of the listed PIDs are
   *  not used, but all other shell elements are.
   *
   *  This procedure will fail if the structural mesh does not have a PID field.
   **/
  void buildTreeByPid(const Indices &pidwet, const Indices &pidintern);

  /// perform mapping and store displacement fields in aerodynamic mesh
  uint map();

  /// determine mapping matrix
  void hmap(MapMatrix &H);

  /// apply mapping matrix obtained by different means
  uint map(const MapMatrix &H, DMatrix<float> &m);

  /// pack mapping matrix H into FFA format
  FFANodePtr mapToFFA(const MapMatrix &H) const;

  /// retreive mapping matrix H from FFA format file
  virtual bool mapFromFFA(const FFANodePtr &root, MapMatrix &H);

  /// useful for debugging : dump projection surface to mesh file for viewing
  void writeProjection(const std::string &fname) const;

  /// debugging: write field of projection distances
  void addDebugFields();

private:

  /// evaluate position of foot point
  Vct3f footPoint(const uint v[], const float wuv[]) const {
    Vct3f fp;
    for (int k=0; k<3; ++k)
      fp += Vct3f( m_pstr->node(v[k]) ) * wuv[k];
    return fp;
  }

  /// compute distance from projection foot
  float sqDistance(uint iwn, const uint v[], const float wuv[]) const {
    return sq( Vct3f(m_paer->node(iwn)) - footPoint(v, wuv) );
  }

  /// evaluate displacement of aerodynamic node mapped to specified triangle
  Vct3f evalDisplacement(uint anode, uint ifield,
                        const uint v[], const float wuv[]) const;

  /// evaluate displacement when local H matrices are available
  Vct3f evalDisplacement(uint ifield, const uint v[], const Mtx33f h[]) const;

  /// evaluate displacements for all modes in one pass
  void evalDisplacements(uint anode, const uint v[], const float wuv[],
                         float *column) const;

  /// compute local mapping matrices for one node, return foot point
  Vct3f evalMap(uint anode, const uint v[],
                const float wuv[], Mtx33f h[]) const;

  /// determine projection foot points
  void footPoints(const Indices &nodeSet, PointList<3> &feet) const;

  /// gather mapped nodes with concavity ratio exceeding threshold
  void collectConcaveNodes(const ConnectMap &v2v, const PointList<3> &feet,
                           Indices &cnodes) const;

  /// identify aerodynamic elements which likely straddle a discontinuity
  void jumpNodes(Indices &rnodes) const;

  /// identify aerodynamic nodes where displacement jumps are expected
  void riskyNodes(const ConnectMap &v2v, Indices &rn,
                  Real maxphi=rad(20.0)) const;

  /// collect direct neighbors of a node set
  void topoNeighbors(const ConnectMap &v2v, Indices &rn) const;

  /// plain Laplacian smoothing displacements for a node subset
  void smoothDisplacements(const Indices &rn, const ConnectMap &v2v,
                           DMatrix<float> &m, int niter=1,
                           float omega=0.5f) const;

  /// solve diffusion problem for nodes in the internal discontinuity regions
  void diffuseDisplacements(const ConnectMap &v2v,
                            const Indices &rnodes, DMatrix<float> &m);

  /// stencils for jump node set
  void diffusionStencil(const ConnectMap &v2v, const Indices &rnodes,
                        ConnectMap &spty) const;

  /// generate diffusion matrix for internal smoothed region
  void smoothingOperator(const Indices &rnodes, const Indices &rim,
                         CsrMatrixD &Dff,
                         CsrMatrixD &Dfc) const;

  /// generate surface diffusion operator for single triangle
  static void diffusionMatrix(const Vct3 tri[], Mtx33 &De);

  /// generate mass matrix for single triangle
  static void massMatrix(const Vct3 tri[], Mtx33 &De);

  /// another smoothing operator
  void averagingOperator(const Indices &rnodes, const Indices &rim,
                         CsrMatrixD &Dff, CsrMatrixD &Dfc) const;

  /// construct a single row for linear-approximation smoothing operator
  void linearSmoothingRow(size_t row,
                          const Indices &fnodes, const Indices &cnodes,
                          CsrMatrixD &Dff, CsrMatrixD &Dfc) const;

//  /// determine least-squares error vector
//  void evalLeastSquares(const Indices &itri, const Indices &inodes,
//                        const MapMatrix &H,
//                        CsrMatrixD &A,
//                        Vector &b) const;

  /// debugging: generate lines connecting a-nodes to footpoints
  void drawFootLines();

private:

  /// element search tree
  MxTriTree m_tree;

  /// accepted distance between surfaces
  float m_catchRadius;

  /// parameter for identification of discontinuities
  Real m_maxNrmDev;

  /// parameter for identification of discontinuities
  Real m_maxDistance;

  /// threshold value for the classification as concave
  Real m_concavityLimit;

  /// radius around discontinuities which is included in smoothing
  Real m_smoothedRadius;

  /// relaxation parameter for smoothing iterations
  float m_smOmega;

  /// optional selective smoothing iterations
  int m_smoothSelective;

  /// optional global smoothing iterations
  int m_smoothGlobal;

  /// extend of region to smooth
  int m_smoothedRing;

  /// surface diffusion or Galerkin averaging?
  bool m_useGalerkin = false;

  /// assemble symmetric operator matrix?
  bool m_buildSymmetric = false;
};

#endif // SURFINTERPOLATOR_H
