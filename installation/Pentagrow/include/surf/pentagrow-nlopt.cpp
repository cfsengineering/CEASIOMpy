
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
 
#include "pentagrow.h"
#include <genua/timing.h>
#include <genua/atomicop.h>
#include <predicates/predicates.h>
#include <nlopt.hpp>

// extra verbosity used in debugging MMA call
// extern unsigned int mma_verbose;

using namespace std;

// ------------------- interface for optimization using NLOPT -----------------

// debug
float time_eval = 0.0f;

// wrapper functions for use with NLOPT

static double eval_inversion_constraint(unsigned n, const double *x,
                                        double *grad, void *aux)
{
  const PentaGrow *pg = (const PentaGrow *) aux;
  if (grad != nullptr)
    memset(grad, 0, n*sizeof(double));
  return pg->inversionConstraint(x, grad);
}

static double eval_intersection_constraint(unsigned n, const double *x,
                                           double *grad, void *aux)
{
  const PentaGrow *pg = (const PentaGrow *) aux;
  if (grad != nullptr)
    memset(grad, 0, n*sizeof(double));
  return pg->intersectionConstraint(x, grad);
}

static double eval_quality_objective(unsigned n, const double *x,
                                     double *grad, void *aux)
{
  const PentaGrow *pg = (const PentaGrow *) aux;
  if (grad != nullptr)
    memset(grad, 0, n*sizeof(double));
  return pg->qualityObjective(x, grad);
}

static double eval_combined_constraint(unsigned n, const double *x,
                                       double *grad, void *aux)
{
  const PentaGrow *pg = (const PentaGrow *) aux;
  if (grad != nullptr)
    memset(grad, 0, n*sizeof(double));

  double c1 = pg->inversionConstraint(x, grad);
  double c2 = pg->intersectionConstraint(x, grad);
  return c1 + c2;
}

void PentaGrow::initializeBounds(double *x, double *lbound, double *ubound)
{
  // generate local coordinate systems: pick first triangle edge encountered
  // as the approximate u-direction, remove component of the vertex normal
  const int nw = mwall.nvertices();
  fudir.resize(nw);
  fvdir.resize(nw);

  std::vector<bool> tag(nw, false);
  const int nf = mwall.nfaces();
  for (int i=0; i<nf; ++i) {
    const uint *v = mwall.face(i).vertices();
    for (int k=0; k<3; ++k) {
      uint vs = v[k];
      uint vt = v[(k+1)%3];
      if (not tag[vs]) {
        fudir[vs] = mwall.vertex(vt) - mwall.vertex(vs);
        tag[vs] = true;
      }
    }
  }

  // initialize height bounds from current values
  targetHeight.resize(nw);
  for (int i=0; i<nw; ++i) {
    Vct3 vni = mwall.normal(i).normalized();
    fudir[i] -= dot(fudir[i], vni)*vni;
    normalize(fudir[i]);
    fvdir[i] = cross(vni, fudir[i]);

    // present value of local envelope height; this is set as a
    // upper bound for h
    Vct3 ni = vout[i] - mwall.vertex(i);
    Real hi = dot( vni, ni );

    double *xi = &x[3*i];
    xi[0] = dot(fudir[i], ni);
    xi[1] = dot(fvdir[i], ni);
    xi[2] = hi;

    double *lb = &lbound[3*i];
    double *ub = &ubound[3*i];
    ub[0] = xi[0] + 16*hi;
    ub[1] = xi[1] + 16*hi;
    ub[2] = hi;

    lb[0] = xi[0] - 16*hi;
    lb[1] = xi[1] - 16*hi;
    lb[2] = -hi; // std::min(firstCellHeight, hi);

    // initialize target height with upper bound
    targetHeight[i] = ub[2];
  }

  // shorthands
  const int nl = numPrismLayers;
  const Real hfirst = firstCellHeight;

  // determine target heights
  for (int i=0; i<nw; ++i) {
    Real lbt = 0.0;
    TriMesh::nb_edge_iterator ite, elast = mwall.v2eEnd(i);
    for (ite = mwall.v2eBegin(i); ite != elast; ++ite)
      lbt += norm(mwall.vertex(ite->opposed(i)) - mwall.vertex(i));
    lbt /= mwall.vdegree(i);
    Real r0 = clamp( std::pow(lbt/hfirst, 1.0/(nl-1.0)),
                     1.0000001, maxExpansionFactor);
    Real htot = hfirst*(1.0 - std::pow(r0, Real(nl))) / (1.0 - r0);
    Real elf = clamp(htot/lbt, 0.1, maxRelHeight);

    // do not make target height larger than upper bound; that would
    // just add a large constant to the objective
    targetHeight[i] = std::min(targetHeight[i],
                               std::min(lbt*elf, maxAbsHeight));
  }
}

// for NLOPT, constraints must be in the form f(x) <= 0

const double nndotmin(0.001);

inline static
double penta_inv_constraint(const Vct3 u[], const Vct3 v[])
{
  const Vct3 &uf( u[0] );
  const Vct3 &ur( u[1] );
  const Vct3 &vf( v[0] );
  const Vct3 &vr( v[1] );

  Vct3 nf = cross(uf, vf);
  Vct3 nr = cross(ur, vr);

  return -(dot(nf,nr)/sq(nf) - nndotmin);
}

inline static
double penta_inv_gradient(const Vct3 u[], const Vct3 v[],
                          Vct3 &fu, Vct3 &fv)
{
  // verified.

  const Vct3 &uf( u[0] );
  const Vct3 &ur( u[1] );
  const Vct3 &vf( v[0] );
  const Vct3 &vr( v[1] );

  Vct3 nf = cross(uf, vf);
  Vct3 nr = cross(ur, vr);

  // constraint value
  double s = - 1.0 / sq(nf);
  double f = s*dot(nf,nr);

  // gradient fu = df/dur
  fu[0] = s*( -nf[1]*vr[2] + nf[2]*vr[1] );
  fu[1] = s*( +nf[0]*vr[2] - nf[2]*vr[0] );
  fu[2] = s*( -nf[0]*vr[1] + nf[1]*vr[0] );

  // gradient fv = df/dvr
  fv[0] = s*( +nf[1]*ur[2] - nf[2]*ur[1] );
  fv[1] = s*( -nf[0]*ur[2] + nf[2]*ur[0] );
  fv[2] = s*( +nf[0]*ur[1] - nf[1]*ur[0] );

  return f + nndotmin;
}

double PentaGrow::inversionConstraint(const double *x, double *grad) const
{
  Wallclock clk;
  clk.start();
  const int nf = mwall.nfaces();
  // const int nw = mwall.nvertices();

  double f(0.0);

#pragma omp parallel for schedule(static, 512)
  for (int i=0; i<nf; ++i) {

    Vct3 pf[3], pr[3], nrm[3];
    const uint *vx = mwall.face(i).vertices();
    for (int k=0; k<3; ++k) {
      const uint vk = vx[k];
      const Vct3 &ud( fudir[vk] );
      const Vct3 &vd( fvdir[vk] );
      pf[k] = mwall.vertex(vk);
      Vct3 uvh( &x[3*vk] );
      nrm[k] = uvh[0]*ud + uvh[1]*vd + uvh[2]*cross(ud,vd);
      pr[k] = pf[k] + nrm[k];
    }

    Vct3 u[2], v[2];
    u[0] = pf[1] - pf[0];
    v[0] = pf[2] - pf[0];
    u[1] = pr[1] - pr[0];
    v[1] = pr[2] - pr[0];

    if (grad != nullptr) {

      Vct3 fg[3];
      double fp = penta_inv_gradient(u, v, fg[1], fg[2]);

      // add only positive terms (constraint violations)
      if (fp > 0) {

        fg[0] = - fg[1] - fg[2];
        atomic_add(f, fp);

        // TODO: verify!
        // assemble gradient of the constraint
        for (int j=0; j<3; ++j) {
          double *gj = &grad[3*vx[j]];
          const Vct3 &bu( fudir[vx[j]] );
          const Vct3 &bv( fvdir[vx[j]] );
          atomic_add( gj[0], dot(fg[j], bu) );           // x[3*vx[j]+0]
          atomic_add( gj[1], dot(fg[j], bv) );           // x[3*vx[j]+1]
          atomic_add( gj[2], dot(fg[j], cross(bu,bv)) ); // x[3*vx[j]+2]
        }
      } // fp > 0

    } else {
      // add only constraint violations
      double fp = penta_inv_constraint(u, v);
      if (fp > 0)
        atomic_add(f, fp);
    }
  }

  if (chattyOptimization) {
    static int ncall(0);
    static int ngrad(0);
    ++ncall;
    ngrad += (grad != nullptr);
    log("[i] Penta inversion constraint: ", f, ", calls: ", ncall, ngrad);
  }

  time_eval += clk.stop();

  return f;
}

inline static
double penta_isec_constraint(const Vct3 &nf, const Vct3 ds[], int &imin)
{
  double h[3];
  for (int k=0; k<3; ++k)
    h[k] = dot(nf, ds[k]);

  imin = std::distance(h, std::min_element(h, h+3));
  return h[imin];
}

double PentaGrow::intersectionConstraint(const double *x, double *grad) const
{
  Wallclock clk;
  clk.start();

  const int nf = mwall.nfaces();
  // const int nw = mwall.nvertices();

  // minimum permitted height
  const double hminroof = 0.0; // 2*firstCellHeight;

  double f(0.0);


#pragma omp parallel for schedule(static, 512)
  for (int i=0; i<nf; ++i) {

    Vct3 pf[3], ds[3];
    const uint *vx = mwall.face(i).vertices();
    for (int k=0; k<3; ++k) {
      const uint vk = vx[k];
      const Vct3 &ud( fudir[vk] );
      const Vct3 &vd( fvdir[vk] );
      pf[k] = mwall.vertex(vk);
      Vct3 uvh( &x[3*vk] );
      ds[k] = uvh[0]*ud + uvh[1]*vd + uvh[2]*cross(ud,vd);
    }

    int imin;
    Vct3 nf = cross(pf[1]-pf[0], pf[2]-pf[0]).normalized();
    double fp = penta_isec_constraint(nf, ds, imin) - hminroof;

    // ignored when constraint fulfilled
    if (fp > 0)
      continue;

    atomic_add(f, -fp);

    // only a contribution from node vx[imin]
    if (grad != nullptr) {
      const uint vk = vx[imin];
      double *fg = &grad[3*vk];
      const Vct3 &ud( fudir[vk] );
      const Vct3 &vd( fvdir[vk] );
      atomic_add(fg[0], -dot(nf, ud));
      atomic_add(fg[1], -dot(nf, vd));
      atomic_add(fg[2], -dot(nf, cross(ud,vd)));
    }
  }

  if (chattyOptimization) {
    static int ncall(0);
    static int ngrad(0);
    ++ncall;
    ngrad += (grad != nullptr);
    log("[i] Penta intersection constraint: ", f, ", calls: ", ncall, ngrad);
  }

  time_eval += clk.stop();

  return f;
}

inline static
double penta_quality_objective(const Vct3 &a, const Vct3 ds[])
{
  double f(0.0);
  for (int k=0; k<3; ++k)
    f += 1.0 - dot(a, ds[k]) / norm(ds[k]);
  return f;
}

inline static
double penta_quality_objective(const Vct3 &a, const Vct3 ds[], Vct3 fg[])
{
  // Sum of 1 - cos(arg(nf, ds_k)) for all k
  //
  // verified.
  double f(0.0);

  for (int k=0; k<3; ++k) {
    f += 1.0 - dot(a, ds[k]) / norm(ds[k]);

    const Vct3 &x(ds[k]);
    double s1 = sq(x[0]) + sq(x[1]) + sq(x[2]);
    double s2 = -1.0 / (s1*sqrt(s1));

    Vct3 &g( fg[k] );
    g[0] = s2 * (a[0]*(sq(x[1]) + sq(x[2])) - x[0]*(a[1]*x[1] + a[2]*x[2]));
    g[1] = s2 * (a[1]*(sq(x[0]) + sq(x[2])) - x[1]*(a[0]*x[0] + a[2]*x[2]));
    g[2] = s2 * (a[2]*(sq(x[1]) + sq(x[0])) - x[2]*(a[1]*x[1] + a[0]*x[0]));
  }

  return f;
}

double PentaGrow::qualityObjective(const double *x, double *grad) const
{
  Wallclock clk;
  clk.start();

  const int nf = mwall.nfaces();
  const int nw = mwall.nvertices();

  double f(0.0);

  // scaling factor for height deviation
  const double f1s = 1.0 / nw;

  // scaling factor for angle criterion
  const double f2s = 1.0 / nw; // 1.0 / (3*(1.0 - cos(M_PI/12.)) * nf);

  // merge both loops for parallelization
#pragma omp parallel for schedule(static, 512)
  for (int i=0; i<nf; ++i) {

    Vct3 pf[3], ds[3];
    const uint *vx = mwall.face(i).vertices();
    for (int k=0; k<3; ++k) {
      const uint vk = vx[k];
      const Vct3 &ud( fudir[vk] );
      const Vct3 &vd( fvdir[vk] );
      pf[k] = mwall.vertex(vk);
      Vct3 uvh( &x[3*vk] );
      ds[k] = uvh[0]*ud + uvh[1]*vd + uvh[2]*cross(ud,vd);
    }

    Vct3 a = cross(pf[1]-pf[0], pf[2]-pf[0]).normalized();

    // target height objective
    double fp(0.0);
    if (grad != nullptr) {

      // quality objective
      Vct3 fg[3];
      fp = f2s*penta_quality_objective(a, ds, fg);

      // decompose gradient df/dds into df/dx
      for (int k=0; k<3; ++k) {

        const uint vk = vx[k];
        const Vct3 &ud( fudir[vk] );
        const Vct3 &vd( fvdir[vk] );
        double *gk = &grad[3*vx[k]];
        atomic_add(gk[0], f2s*dot(fg[k], ud)); // u-component
        atomic_add(gk[1], f2s*dot(fg[k], vd)); // v-component
        atomic_add(gk[2], f2s*dot(fg[k], cross(ud,vd))); // h-component
      }

      // height objective
      for (int k=0; k<3; ++k) {
        const uint vk = vx[k];
        const Vct3 &ud( fudir[vk] );
        const Vct3 &vd( fvdir[vk] );
        double *gk = &grad[3*vk];
        double dh = dot(a, ds[k]) - targetHeight[vk];
        fp += f1s*sq(dh);
        Vct3 dfs = 2*f1s*dh * a;

        atomic_add(gk[0], dot(dfs, ud)); // u-component
        atomic_add(gk[1], dot(dfs, vd)); // v-component
        atomic_add(gk[2], dot(dfs, cross(ud,vd))); // h-component
      }

    } else {

      // quality objective
      fp = f2s*penta_quality_objective(a, ds);

      // height objective
      for (int k=0; k<3; ++k)
        fp += f1s*sq( dot(a, ds[k]) - targetHeight[vx[k]] );
    }

    atomic_add(f, fp);
  }

  if (chattyOptimization) {
    static int ncall(0);
    static int ngrad(0);
    ++ncall;
    ngrad += (grad != nullptr);
    log("[i] Quality objectve: ", f, ", calls: ", ncall, ngrad);
  }

  time_eval += clk.stop();

  return f;
}

static inline bool penta6_posvol(const Vct3 pw[], const Vct3 pe[])
{
  bool pv = true;
  pv &= jrsOrient3d( pw[0], pw[1], pw[2], pe[0] ) < 0.0;
  pv &= jrsOrient3d( pw[0], pw[1], pw[2], pe[1] ) < 0.0;
  pv &= jrsOrient3d( pw[0], pw[1], pw[2], pe[2] ) < 0.0;
  return pv;
}

void PentaGrow::optimizeEnvelope()
{
  // do nothing if no time assigned
  if (maxOptimizationTime <= 0.0)
    return;

  // debug call to MMA internally
  // mma_verbose = 1;

  Wallclock clk;

  const size_t nw = nWallNodes();
  const size_t nv = 3*nw;
  std::vector<double> x(nv, 0.0), lb(nv), ub(nv);
  initializeBounds(&x[0], &lb[0], &ub[0]);

  double minf;
  log("[i] Envelope optimization using MMA...");
  clk.start();

  nlopt::result result = nlopt::FAILURE;

  // first stage : find a feasible point
  // if the (difficult) constraints are violated at the initial point,
  // start with running an unconstrained optimization with the constraints as
  // objective for a certain amount of time
  try {
    nlopt::opt opt(nlopt::LD_LBFGS, nv);
    opt.set_lower_bounds(lb);
    opt.set_upper_bounds(ub);
    opt.set_min_objective(eval_combined_constraint, (void *) this);
    opt.set_xtol_rel(1e-6);
    opt.set_stopval(0.0);
    opt.set_maxtime( 0.5*maxOptimizationTime );
    result = opt.optimize(x, minf);

    if ( int(result) > 0)
      log("[i] NLOPT phase 1 terminated successfully, code: ", int(result));
    else
      log("[w] NLOPT phase 1 failed, code: ", int(result));

  } catch (std::exception &ex) {
    log("[w] NLOPT failed in first stage, error: ", ex.what());
  }

  // at this point, we might have run into a local minimum where the constraints
  // are not actually fulfilled. the second stage cannot possible fix this, so
  // it's probably better to reject the optimization results outright
  if (inversionConstraint(&x[0], nullptr) > 0) {
    log("[i] Phase 1: Inversion constraint violated, rejected results.");
    return;
  }

  if (intersectionConstraint(&x[0], nullptr) > 0) {
    log("[i] Phase 1: Intersection constraint violated, rejected results.");
    return;
  }

  result = nlopt::FAILURE;
  try {

    nlopt::opt opt(nlopt::LD_MMA, nv);
    opt.set_lower_bounds(lb);
    opt.set_upper_bounds(ub);
    opt.add_inequality_constraint(eval_inversion_constraint, (void *) this);
    opt.add_inequality_constraint(eval_intersection_constraint, (void *) this);
    opt.set_min_objective(eval_quality_objective, (void *) this);
    opt.set_xtol_rel(1e-12);
    opt.set_ftol_rel(1e-6);
    opt.set_maxtime( 0.5*maxOptimizationTime );

    nlopt::opt sub(nlopt::LD_LBFGS, nv);
    sub.set_xtol_rel(1e-12);
    sub.set_lower_bounds(lb);
    sub.set_upper_bounds(ub);
    sub.set_vector_storage(32);
    opt.set_local_optimizer(sub);

    result = opt.optimize(x, minf);

    if ( int(result) > 0)
      log("[i] NLOPT phase 2 terminated successfully, code: ", int(result));
    else
      log("[w] NLOPT phase 2 failed, code: ", int(result));

  } catch (std::exception &ex) {
    log("[w] NLOPT failed in second stage, error: ", ex.what());
    return;
  }

  log("[i] Final inversion constraint violation: ",
      inversionConstraint(&x[0], nullptr));
  log("[i] Final intersection constraint violation: ",
      intersectionConstraint(&x[0], nullptr));

  if (int(result) > 0) {
    vout = mwall.vertices();
    for (size_t i=0; i<nw; ++i) {
      vout[i] += x[3*i+0] * fudir[i] + x[3*i+1] * fvdir[i];
      vout[i] += x[3*i+2] * cross(fudir[i], fvdir[i]);
    }

    // check protopentahedra for tangling
    size_t nfail = 0;
    const size_t nf = mwall.nfaces();
    Vct3 pw[3], pe[3];
    for (size_t i=0; i<nf; ++i) {
      const uint *v = mwall.face(i).vertices();
      for (int k=0; k<3; ++k) {
        pw[k] = mwall.vertex(v[k]);
        pe[k] = vout[v[k]];
      }
      Vct3 fn = cross(pw[1]-pw[0], pw[2]-pw[0]);
      if ( not penta6_posvol(pw, pe) ) {
        ++nfail;
        continue;
      }
      if ( dot(fn, pe[0]-pw[0] ) <= 0 ) {
        ++nfail;
        continue;
      }
      if ( dot(fn, pe[1]-pw[1] ) <= 0 ) {
        ++nfail;
        continue;
      }
      if ( dot(fn, pe[2]-pw[2] ) <= 0 ) {
        ++nfail;
        continue;
      }
    }
    log("[i] Number of invalid protopentahedra:", nfail);
  }

  log("[t] Total time in NLOPT run: ", clk.stop());
  log("[t] Time in objective/constraint evaluation: ", time_eval);
}

