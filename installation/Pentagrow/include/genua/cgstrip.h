
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
 
#ifndef GENUA_CGSTRIP_H
#define GENUA_CGSTRIP_H

#include "defines.h"
#include "xmlelement.h"
#include "smatrix.h"
#include <boost/shared_array.hpp>

/** Index container for triangle/line/quad strips/fans

  CgStrip stores triangle (and quad) strips using the OpenGL conventions,
  as a single long index array and an array of offsets into the index
  array which mark the beginning of each strip.

  \ingroup geometry
  \sa CgMesh
  */
class CgStrip
{
  public:

    /** Utility for glMultiDrawElements.

    This looks like it duplicates most of the data in CgStrip, but using VBO
    drawing with very many element strips (as extracted from 3dxml files) requires
    using glMultiDrawElements, which in turn needs byte offsets in the form of
    offset pointers. Recomputing them for each frame is not efficient.

    */
    class BufferOffset
    {
      public:

        // create empty offset buffer
        BufferOffset() : nstr(0) {}

        uint nstrip() const {return nstr;}

        void resizeFirstp(uint n) {
          nstr = n;
          pcount.reset(new int[n]);
          pfirst.reset(new int[n]);
        }
        void resizeOffset(uint n) {
          nstr = n;
          pcount.reset(new int[n]);
          poff.reset(new const char*[n]);
        }
        const int *count() const {
          assert(pcount);
          return pcount.get();
        }
        const int *first() const {
          assert(pfirst);
          return pfirst.get();
        }
        const char **offset() const {
          assert(poff);
          return poff.get();
        }

      private:

        // Unnecessary complication : using gcc, std::vector<const char*> works
        // fine, but MSVC's C++ lib will crash in random places when calling resize() on a
        // std::vector<const char*>. Using a reference-counted boost::shared_array works.
        boost::shared_array<int> pcount, pfirst;
        boost::shared_array<const char*> poff;
        uint nstr;
      friend class CgStrip;
    };

    /// empty strips
    CgStrip(bool strps=true) : ifirst(1), useStrips(strps) { ifirst[0] = 0; }

    /// disable use of strip indices (just array offsets )
    void strips(bool flag) {useStrips = flag;}

    /** If strips() is true, then *this stores strip indices, e.g. (triangle strips and fans),
    for use with glDrawElements etc. If false, the offsets indicate consecutive element indices
    for use with glMultiDrawArrays(). */
    bool strips() const {return useStrips;}

    /// total size of index array
    uint nindices() const {return istrip.size();}

    /// number of strips defined
    uint nstrip() const {
      return ifirst.empty() ? 0 : ifirst.size()-1;
    }

    /// storage required for strip index array
    size_t indexBytes() const {return istrip.size()*sizeof(Indices::value_type);}

    /// pointer to first index
    const uint *indexPointer() const { assert(useStrips); return &istrip[0];}

    /// offset of strip i
    uint offset(uint i) const {
      assert(i < ifirst.size());
      return ifirst[i];
    }

    /// number of indices in strip i
    uint size(uint i) const {
      assert(i+1 < ifirst.size());
      return ifirst[i+1] - ifirst[i];
    }

    /// pointer to first index of strip i
    const uint *first(uint i) const {
      assert(useStrips);
      assert(i < ifirst.size());
      assert(ifirst[i] < istrip.size());
      return &istrip[ifirst[i]];
    }

    /// fill a list of pointer offsets for glMultiDrawElements
    void pointerOffsets(BufferOffset & boff) const;

    /// add new array offset
    uint append(uint a) {
      assert(useStrips == false);
      assert(a >= ifirst.back());
      ifirst.push_back(a);
      return nstrip()-1;
    }

    /// add a single strip
    template <class Iterator>
    uint append(Iterator firsti, Iterator lasti) {
      istrip.insert(istrip.end(), firsti, lasti);
      ifirst.push_back( istrip.size() );
      return nstrip()-1;
    }

    /// decode a string representation of the form "3 4 5 1 6, 8 3 4 5, ..."
    void append(const std::string & s, uint voff=0);

    /// merge with strips using vertex offset
    void merge(const CgStrip & s, uint voff=0);

    /// convert strips to unrolled triangles
    uint strips2triangles(Indices & t) const;

    /// convert fans to unrolled triangles
    uint fans2triangles(Indices & t) const;

    /// convert polylines to plain lines
    uint poly2lines(Indices & lns, int voffset=0) const;

    /// unique set of indices between begin and end
    void uniqueIndices(Indices & idx, uint ibegin=0, uint iend=NotFound) const {
      if (iend == NotFound)
        iend = istrip.size();
      assert(ibegin < istrip.size());
      assert(iend <= istrip.size());
      idx.clear();
      idx.insert(idx.end(), istrip.begin()+ibegin, istrip.begin()+iend);
      std::sort(idx.begin(), idx.end());
      idx.erase(std::unique(idx.begin(), idx.end()), idx.end());
    }

    /// calculate how many triangles this will render
    uint ntriangles() const {return useStrips ? (istrip.size() - 2*nstrip()) : 0;}

    /// size in memory (for information, not allocation)
    float megabytes() const;

    /// swap contents
    void swap(CgStrip & a) {
      istrip.swap(a.istrip);
      ifirst.swap(a.ifirst);
      std::swap(useStrips, a.useStrips);
    }

    /// convert to xml
    XmlElement toXml(bool share = false) const;

    /// retrieve from xml representation
    void fromXml(const XmlElement & xe);

    /// delete all stored data
    void clear() {
      istrip.clear();
      ifirst.resize(1);
      ifirst[0] = 0;
    }

  private:

    /// triangle strip indices
    Indices istrip;

    /// pointer to first index for each strip
    Indices ifirst;

    /// istrip array used?
    bool useStrips;
};

#endif // CGSTRIP_H
