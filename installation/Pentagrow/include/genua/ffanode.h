
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
 #ifndef GENUA_FFANODE_H
#define GENUA_FFANODE_H

#include <string>
#include <vector>
#include <iosfwd>
#include <cstring>
#include <boost/shared_ptr.hpp>

#include "forward.h"
#include "strutils.h"

typedef enum { FFAInt4, FFAInt8, FFAFloat4, FFAFloat8,
               FFAComplex8, FFAComplex16,
               FFAChar, FFAString16, FFAString72,
               FFAParent } FFADataType;

template <class Type>
struct ffa_type_trait {
  static const FFADataType value = FFAChar;
};

template <>
struct ffa_type_trait<float> {
  static const FFADataType value = FFAFloat4;
};

template <>
struct ffa_type_trait<double> {
  static const FFADataType value = FFAFloat8;
};

template <>
struct ffa_type_trait<std::complex<float> > {
  static const FFADataType value = FFAComplex8;
};

template <>
struct ffa_type_trait<std::complex<double> > {
  static const FFADataType value = FFAComplex16;
};

template <>
struct ffa_type_trait<int> {
  static const FFADataType value = FFAInt4;
};

template <>
struct ffa_type_trait<int64_t> {
  static const FFADataType value = FFAInt8;
};

template <>
struct ffa_type_trait<char> {
  static const FFADataType value = FFAChar;
};

/** Node in FFA data file.

  The FFA file format is used by simulation codes implemented by the Swedish
  Aeronautical Research Establishment (FFA), which is now part of FOI
  (http://www.foi.se). The most important application of this classe inside
  libgenua is the format's use in the EDGE flow solver, which writes its meshes,
  boundary conditions and top-level configuration to FFA format files.

  FFA files are hierarchically structured, where each level of the hierarchy
  is a two-dimensional array. In some sense, it is really a tree of matrices.
  Files are stored in a fortran-compatible record-based binary format, which is
  reasonably efficient as long as nodes are suffiently highly loaded, that is,
  the number of tree nodes per unit of stored data is small.

  Unfortunately, the typical access pattern for FFA binary files makes them
  rather unsuitable for use with Windows network shares. Very often, the
  read/write times in that case are much longer than for the equivalent amount
  of data in CGNS files (for example).

  \todo Implement streaming format (version 2014)

  \ingroup mesh
  \sa MxMesh
*/
class FFANode
{

public:

  /// create empty, undefined node
  FFANode() : type(FFAParent), nrow(0), ncol(0) {}

  /// create named parent node
  FFANode(const std::string & s) : tag(s), type(FFAParent), nrow(0), ncol(0) {}

  /// size of a single element in bytes
  static int elementSize(FFADataType t) {
    static const int dtsize[] = {4, 8, 4, 8, 8, 16, 1, 16, 72, 0};
    int idx = int(t);
    assert(size_t(idx) < sizeof(dtsize));
    return dtsize[idx];
  }

  /// data type code character
  static char elementCode(FFADataType t) {
    static const char dtcode[] = "IJRDCZASLN";
    int idx = int(t);
    assert(size_t(idx) < sizeof(dtcode));
    return dtcode[idx];
  }

  /// utility
  static FFANodePtr create(const std::string &s = "") {
    return boost::make_shared<FFANode>(s);
  }

  /// access node name
  const std::string & name() const {return tag;}

  /// change node name
  void rename(const std::string & s) {tag = s;}

  /// access element type
  FFADataType contentType() const {return type;}

  /// number of rows ('size')
  size_t nrows() const {return nrow;}

  /// number of columns ('dimension')
  size_t ncols() const {return ncol;}

  /// number of values (rows*cols)
  size_t numel() const {return nrow*ncol;}

  /// number of bytes in content array
  size_t nbytes() const {return elementSize(type)*numel();}

  /// number of child nodes
  uint nchildren() const {return children.size();}

  /// access child node k
  FFANodePtr child(uint k) const {
    assert(k < children.size());
    return children[k];
  }

  /// convenience interface to facilitate iteration
  const FFANodeArray &siblings() const {return children;}

  /// locate child node named s
  uint findChild(const std::string & s) const;

  /// recursively descend path
  FFANodePtr findPath(const std::string &path) const;

  /// copy single int into node
  void copy(const int &x) {
    copy(FFAInt4, 1, 1, &x);
  }

  /// copy single int into node
  void copy(const int64_t &x) {
    copy(FFAInt8, 1, 1, &x);
  }

  /// copy single float into node
  void copy(const float &x) {
    copy(FFAFloat4, 1, 1, &x);
  }

  /// copy single double into node
  void copy(const double &x) {
    copy(FFAFloat8, 1, 1, &x);
  }

  /// copy raw data into node
  void copy(FFADataType t, int nr, int nc, const void *ptr);

  /// copy int array into node
  void copy(int nr, int nc, const int *ptr) {
    copy(FFAInt4, nr, nc, ptr);
  }

  /// copy int array into node
  void copy(int nr, int nc, const int64_t *ptr) {
    copy(FFAInt8, nr, nc, ptr);
  }

  /// copy float array into node
  void copy(int nr, int nc, const float *ptr) {
    copy(FFAFloat4, nr, nc, ptr);
  }

  /// copy double array into node
  void copy(int nr, int nc, const double *ptr) {
    copy(FFAFloat8, nr, nc, ptr);
  }

  /// copy single string into node
  void copy(const std::string & s);

  /// retrieve raw data from node
  void retrieve(void *dest) const {
    memcpy(dest, &rblock[0], nbytes());
  }

  /// put contents into string
  void retrieve(std::string & s) const {
    assert(type == FFAChar or type == FFAString16 or type == FFAString72);
    s.resize(nbytes());
    retrieve(&s[0]);
    s = strip(s);
  }

  /// retrieve a scalar value
  void retrieve(double &v) const {
    if (type == FFAFloat8) {
      memcpy( &v, &rblock[0], sizeof(double) );
    } else if (type == FFAFloat4) {
      float x;
      memcpy( &x, &rblock[0], sizeof(float) );
      v = x;
    }
  }

  /// retrieve a scalar value
  void retrieve(int &v) const {
    if (type == FFAInt4) {
      memcpy( &v, &rblock[0], sizeof(int) );
    } else if (type == FFAInt8) {
      int64_t x;
      memcpy( &x, &rblock[0], 8 );
      v = int(x);
    }
  }

  /// convenience function : find child, retreive x if found
  bool retrieve(const std::string &tag, std::string &x) const {
    uint ip = findChild(tag);
    if (ip != NotFound) {
      child(ip)->retrieve(x);
      return true;
    }
    return false;
  }

  /// convenience function : find child, retreive x if found
  bool retrieve(const std::string &tag, double &x) const {
    uint ip = findChild(tag);
    if (ip != NotFound) {
      child(ip)->retrieve(x);
      return true;
    }
    return false;
  }

  /// convenience function : find child, retreive x if found
  bool retrieve(const std::string &tag, int &x) const {
    uint ip = findChild(tag);
    if (ip != NotFound) {
      child(ip)->retrieve(x);
      return true;
    }
    return false;
  }

  /// append child node
  FFANodePtr append(const FFANodePtr & np) {
    children.push_back(np);
    return np;
  }

  /// append child node and take ownership
  FFANodePtr append(FFANode *np) {
    children.push_back(FFANodePtr(np));
    return children.back();
  }

  /// convenience function : add a named node with string content
  FFANodePtr append(const std::string &tag, const std::string &content);

  /// convenience function : add a matrix node
  template <typename NumericType>
  FFANodePtr append(const std::string &tag, int nr, int nc,
                    const NumericType values[])
  {
    FFANodePtr childNode(FFANode::create(tag));
    childNode->copy(nr, nc, values);
    this->append(childNode);
    return childNode;
  }

  /// convenience function : add a scalar value node
  FFANodePtr append(const std::string &tag, double x)
  {
    FFANodePtr childNode(FFANode::create(tag));
    childNode->copy(x);
    this->append(childNode);
    return childNode;
  }

  /// convenience function : add a scalar value node
  FFANodePtr append(const std::string &tag, int x)
  {
    FFANodePtr childNode(FFANode::create(tag));
    childNode->copy(x);
    this->append(childNode);
    return childNode;
  }

  /// convenience function : add a scalar value node
  FFANodePtr append(const std::string &tag, int64_t x)
  {
    FFANodePtr childNode(FFANode::create(tag));
    childNode->copy(x);
    this->append(childNode);
    return childNode;
  }

  /// generate summary string
  std::string summary() const;

  /// write to file; determine format by extension
  void write(const std::string & s) const;

  /// read from file; determine format by extension
  void read(const std::string & s);

  /// write to ascii file
  void awrite(std::ostream & os) const;

  /// read from ascii file
  void aread(std::istream & is);

  /// write to binary file
  void bwrite(std::ostream & os) const;

  /// read from binary file
  void bread(std::istream & is);

  // debugging: access recorded system io time
  static float systemTime() {return s_tsys;}

private:

  /// pointer to item at (i,j)
  template <class Element>
  Element *item(int i, int j) {
    assert(i < nrow);
    assert(j < ncol);
    size_t bpos = elementSize(type)*(j*nrow + i);
    return (Element *) &rblock[bpos];
  }

  /// pointer to item at (i,j)
  template <class Element>
  const Element *item(int i, int j) const {
    assert(i < nrow);
    assert(j < ncol);
    size_t bpos = elementSize(type)*(j*nrow + i);
    return (Element *) &rblock[bpos];
  }

  /// byte-swap contents
  void swapBytes() const;

private:

  /// name of this node
  std::string tag;

  /// data type of this node
  FFADataType type;

  /// number of rows and columns
  size_t nrow, ncol;

  /// array of sibling nodes
  FFANodeArray children;

  /// raw storage
  mutable std::vector<char> rblock;

  /// i/o timing data
  static float s_tsys, s_tself;
};

#endif

