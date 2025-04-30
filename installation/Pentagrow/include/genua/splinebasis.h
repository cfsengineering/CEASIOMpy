
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
 
#ifndef GENUA_SPLINEBASIS_H
#define GENUA_SPLINEBASIS_H

#include "svector.h"
#include "dvector.h"
#include "piegl.h"

#ifndef MATLAB_MEX_FILE
#include "xmlelement.h"
#endif

/** Spline Basis.

  SplineBasis contains knot vector and order (degree) of a nurbs basis.
  The ancient original interface of this class makes use of recursive basis
  function evaluations and is rather inefficient.

  For much more efficient evaluation abd derivatives, use the templatized
  interface eval<N>(u,b) and derive<N>() for fixed size degree or consider
  the low-level functions in piegl.h

  */
class SplineBasis
{
  public:

    /// construction
    SplineBasis() : p(3) {}

    /// construction
    SplineBasis(uint deg, const Vector & knots);

    /// construction from unique knots and multiplicities
    const Vector & init(uint deg, uint nuk, const Real knots[], const int mtp[]);

    /// initialize from parameter values and degree
    const Vector & init(uint deg, const Vector & parm);

    /// return number of knots
    uint size() const {return k.size();}

    /// compute number of control points
    uint ncontrol() const {return k.size()-p-1;}
    
    /// evaluate a single basis function using recursion
    Real eval(int i, Real u) const {
      assert(k.size() != 0);
      return SplineBasis::recurse(i,p,u);
    }

    /** Faster basis evaluation.
    Computes all non-zero basis functions, puts them into b
    and returns the span to which u belongs.  */
    template <uint N>
    uint eval(Real u, SVector<N> & b) const {
      assert(p+1 == N);
      int s = findSpan(u);
      Piegl::sEvalBasis<Real,N-1>(u, s, k, b);
      return s;
    }
    
    /// evaluate for arbitrary degree <= 15, return span
    uint eval(Real u, Vector & b) const {
      int s = findSpan(u);
      b.resize(p+1);
      Piegl::dEvalBasis(u, s, p, k.pointer(), b.pointer());
      return s;
    }

    /// evaluate for arbitrary degree <= 15, low-level version
    uint lleval(Real u, Real b[]) const {
      int s = findSpan(u);
      Piegl::dEvalBasis(u, s, p, k.pointer(), b);
      return s;
    }
    
    /** Fixed-size basis function derivation.
    Computes all non-zero basis functions derivatives, puts them into b
    and returns the span to which u belongs.  */
    template <uint N, uint K>
    uint derive(Real u, SMatrix<K, N> & b) const {
      assert(p+1 <= N);
      int s = findSpan(u);
      Piegl::sDeriveBasis<Real, N-1, K-1>(u, s, k, b);
      return s;
    }
    
    /// derive for arbitrary degree <= 7, return span
    uint derive(Real u, int ndev, Matrix & b) const {
      int s = findSpan(u);
      b.resize(ndev+1, p+1);
      Piegl::dDeriveBasis(u, s, p, ndev, k, b);
      return s;
    }

    /// derive for arbitrary degree <= 7, return span
    uint derive(Real u, int ndev, int lda, Real pb[]) const {
      int s = findSpan(u);
      Piegl::dDeriveBasis(u, s, p, ndev, k, lda, pb);
      return s;
    }

    /// derive d-times using recursion
    Real derive(int i, Real u, int d) const {
      assert(k.size() != 0);
      return SplineBasis::recurse_derive(i,p,u,d);
    }

    /// search span
    int findSpan(Real u) const {
      // returns span index
      // [Pie97] Algorithm 2.1
      int bot, top, mid, n = k.size() - p - 2;
      assert(u >= k[0] and u <= k[k.size()-1]);

      // handle special case: last span
      if (u == k[n+1])
        return n;
      else if (u == k[0])
        return p;

      // binary search
      bot = p;
      top = n+1;
      mid = (bot+top) / 2;
      while (u < k[mid] or u >= k[mid+1]) {
        if (u < k[mid])
          top = mid;
        else
          bot = mid;
        if (top-bot < 2)
          return bot;
        mid = (bot+top) / 2;
      }
      return mid;
    }

    /// compute block matrix with integral of square of 2nd derivatives
    template <uint N>
    uint omega(int i, SMatrix<N,N> &m) const {
      assert(p+1 == N);
      assert(i+1 < k.size());
      m = 0.0;
      Real du = k[i+1] - k[i];
      if (du == 0)
        return NotFound;

      SMatrix<3,N> ba, bb;  // 0th, 1st, 2nd derivatives
      Real ua = (2*k[i] + k[i+1]) / 3.0;
      Real ub = (k[i] + 2*k[i+1]) / 3.0;
      uint span = derive(ua, ba);
      derive(ub, bb);

      for (int ki=0; ki<N; ++ki) {
        Real a13 = ba(2,ki);
        Real a23 = bb(2,ki);
        for (int kj=0; kj<N; ++kj) {
          Real b13 = ba(2,kj);
          Real b23 = bb(2,kj);
          m(ki,kj) = du*(a13*b13 - 0.5*(a13*b23 + a23*b13) + a23*b23);
        }
      }

      return span;
    }

    /// return knot vector
    const Vector & getKnots() const {return k;}

    /// set knot vector
    void setKnots(const Vector & knots) {k = knots;}

    /// return degree
    uint degree() const {return p;}

    /// insert knot, update control points
    template <class CpArray>
    uint insertKnot(Real u, CpArray &cpts) {
      assert(u >= k.front());
      assert(u <= k.back());
      const int ncp = cpts.size();
      const int span = findSpan(u);
      assert(k[span] <= u and k[span+1] > u);
      CpArray ctmp(ncp + 1);
      Real alpha;
      ctmp.front() = cpts.front();
      for (int i=1; i<ncp; ++i) {
        if (i <= (span - int(p)))
          alpha = 1.0;
        else if (i <= span)
          alpha = (u - k[i]) / (k[i+p] - k[i]);
        else
          alpha = 0.0;
        ctmp[i] = alpha*cpts[i] + (1.0 - alpha)*cpts[i-1];
      }
      ctmp.back() = cpts.back();
      ctmp.swap(cpts);
      k.insert(std::lower_bound(k.begin(), k.end(), u), u);
      return span;
    }

    /// split spline at u, make *this the lower-parameter curve
    template <class CpArray>
    void split(Real u, CpArray &cpts, SplineBasis &hib, CpArray &hcp) {
      for (int i=0; i<int(p); ++i)
        insertKnot(u, cpts);

      // construct new knot vectors
      Vector::iterator posl, posu;
      posl = std::lower_bound(k.begin(), k.end(), u); // first s.th. *posu == u
      posu = posl + p;
      Vector knl, knh;
      knl.insert(knl.end(), k.begin(), posu);
      knl.push_back(u);
      knl /= knl.back();

      knh.push_back(u);
      knh.insert(knh.end(), posl, k.end());
      knh -= knh.front();
      knh /= knh.back();

      // split control point set
      const uint ncpl = knl.size() - p - 1;
      const uint ncph = knh.size() - p - 1;
      CpArray lcp;
      lcp.insert(lcp.end(), cpts.begin(), cpts.begin()+ncpl);
      hcp.clear();
      hcp.insert(hcp.end(), cpts.begin() + cpts.size() - ncph, cpts.end());
      lcp.swap(cpts);

      // assign split knot vectors to new basis functions
      k.swap(knl);
      hib = SplineBasis(p, knh);
    }

#ifndef MATLAB_MEX_FILE

    /// export as xml representation 
    XmlElement toXml(bool share=false) const;
    
    /// import from xml representation 
    void fromXml(const XmlElement & xe);
    
#endif

  private:

    /// recursive basis evaluation
    Real recurse(int i, int deg, Real u) const;

    /// redcursive basis derivation
    Real recurse_derive(int i, int degree, Real u, int d) const;

  private:
  
    /// degree
    uint p;
  
    /// basis knots 
    Vector k;
};

#endif

