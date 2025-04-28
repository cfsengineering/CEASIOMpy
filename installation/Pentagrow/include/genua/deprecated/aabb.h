#ifndef AABB_H
#define AABB_H

#include "defines.h"

/** Axis-aligned bounding box in N dimensions.
  */
template <int N, typename FloatType>
class AABBox
{
  public:

    /// create undefined box
    AABBox() {reset();}

    /// access low coordinates
    const FloatType *low() const {return plo;}

    /// access low coordinates
    const FloatType *high() const {return phi;}

    /// reset box
    void reset() {
      const FloatType bigval = std::numeric_limits<FloatType>::max();
      for (int i=0; i<N; ++i) {
        plo[i] = +bigval;
        phi[i] = -bigval;
      }
    }

    /// expand coordinate c to enclose x
    template <int c>
    void expand(float x) {
      plo[c] = std::min(plo[c], x);
      phi[c] = std::max(phi[c], x);
    }

    /// expand box so that p is inside
    void enclose(const FloatType p[]) {
      for (int i=0; i<N; ++i) {
        plo[i] = std::min(plo[i], p[i]);
        phi[i] = std::max(phi[i], p[i]);
      }
    }

    /// expand box to enclose n vertices
    void enclose(int n, const FloatType vtx[]) {
      reset();
      for (int i=0; i<n; ++i)
        enclose( &vtx[N*i] );
    }

    /// expand box to enclose indexed vertices
    template <class Iterator>
    void enclose(const FloatType vtx[], Iterator first, Iterator last) {
      reset();
      for (Iterator itr=first; itr != last; ++itr) {
        const uint eix = *itr;
        enclose( &vtx[N*eix] );
      }
    }

    /// expand box to enclose elements indexed by elix; each element has NV vertices
    template <int NV, class Iterator>
    void enclose(const FloatType vtx[], const uint elix[],
                 Iterator first, Iterator last)
    {
      reset();
      for (Iterator itr=first; itr != last; ++itr) {
        const uint eix = *itr;
        const uint *vi = &elix[NV*eix];
        for (int k=0; k<NV; ++k)
          enclose( &vtx[N*vi[k]] );
      }
    }

    /// expand box so that b is inside
    void enclose(const AABBox<N,FloatType> & b) {
      for (int i=0; i<N; ++i) {
        plo[i] = std::min(plo[i], b.plo[i]);
        phi[i] = std::max(phi[i], b.phi[i]);
      }
    }

    /// check for box-box intersection, with branches
    bool intersects(const AABBox<N,FloatType> & b) const {
      for (int i=0; i<N; ++i) {
        if (plo[i] > b.phi[i] or phi[i] < b.plo[i])
          return false;
      }
      return true;
    }

    /// axis aligned minimum distance (will be negative for intersection)
    FloatType alignedDistance(const AABBox<N,FloatType> & b) const {
      FloatType mindst = std::numeric_limits<FloatType>::max();
      FloatType ab, ba;
      for (int i=0; i<N; ++i) {
        ab = plo[i] - b.phi[i];
        ba = b.plo[i] - phi[i];
        if (fabs(ab) < fabs(ba))
          mindst = std::min(mindst, ab);
        else
          mindst = std::min(mindst, ba);
      }
      return mindst;
    }

    /// compute box center
    void center(FloatType ctr[]) const {
      const FloatType half(0.5);
      for (int k=0; k<N; ++k)
        ctr[k] = half * (plo[k] + phi[k]);
    }

  private:

    /// upper and lower vertex
    FloatType plo[N], phi[N];
};

#endif // AABB_H
