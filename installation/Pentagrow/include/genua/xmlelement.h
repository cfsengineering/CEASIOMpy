
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
 
#ifndef GENUA_XMLELEMENT_H
#define GENUA_XMLELEMENT_H

#include "forward.h"
#include "sharedvector.h"
#include "xcept.h"
#include "typecode.h"
#include "algo.h"

#include <map>    
#include <list>
#include <string>
#include <cstring>
#include <boost/shared_array.hpp>

class ZipFile;

/** XML Element.

  A very simple class for reading and writing XML documents. It is intended for
  minimum fuss and maximum ease of use and not for good performance with large
  documents.

  Usage example:
  \verbatim
    XmlElement doc("sml");
    doc["version"] = "1.3";
    XmlElement fe("client");
    fe["name"] = "Oscar";
    fe["job"] = "clerk";
    fe.text() = "Lousy speaker, avid worker.";
    doc.append(fe);
    XmlElement se("client");
    se["name"] = "Lily";
    se["job"] = "CTO";
    doc.append(se);
    doc.write("clients.sml");
  \endverbatim

  XmlElement uses the expat xml parser written by James Clark <jjc@jclark.com>.
  
  TODO : Consider using a flat vector<pair<string,string>> for the
         the attribute map since there are usually very few of them.

  */
class XmlElement
{
public:

  /// supported on-disk file formats
  enum StorageFormat {PlainText, ZippedXml, Lz4Compressed};

  /// storage for binary data
  typedef boost::shared_ptr<char[]>  BlobType;

  typedef std::map<std::string, std::string> StringMap;
  typedef SharedVector<XmlElement> ElementList;
  typedef ElementList::const_iterator const_iterator;
  typedef ElementList::iterator mutable_iterator;
  typedef StringMap::const_iterator attr_iterator;

  /// create an element named tg
  explicit XmlElement(const std::string & tg = "") : m_tag(tg), m_nbytes(0) {}

  /// create an element named tg, common case with temporary as tag
  explicit XmlElement(std::string && tg) : m_tag(std::move(tg)), m_nbytes(0) {}

  /// shortcut constructor for simple string elements
  XmlElement(const std::string & tg, const std::string & content)
    : m_tag(tg) {text(content);}

  /// move constructor (turns out MSVC doesn't auto-generate this one)
  XmlElement(XmlElement &&a) :
    m_tag(std::move(a.m_tag)), m_txt(std::move(a.m_txt)),
    m_attributes(std::move(a.m_attributes)),
    m_siblings(std::move(a.m_siblings)),
    m_typecode(a.m_typecode),
    m_blob(std::move(a.m_blob)),
    m_nbytes(a.m_nbytes) {}

  /// copy constructor
  XmlElement(const XmlElement &) = default;

  /// move assignment
  XmlElement & operator= (XmlElement &&a) {
    if (&a != this) {
      m_tag = std::move(a.m_tag);
      m_txt = std::move(a.m_txt);
      m_attributes = std::move(a.m_attributes);
      m_siblings = std::move(a.m_siblings);
      m_typecode = a.m_typecode;
      m_blob = std::move(a.m_blob);
      m_nbytes = a.m_nbytes;
    }
    return *this;
  }

  /// copy assignment
  XmlElement & operator= (const XmlElement &) = default;

  /// an element is empty if there are no children, attributes, nor payload
  bool empty() const {
    return (m_siblings.size() == 0) and m_attributes.empty() and
        m_txt.empty() and (m_nbytes == 0);
  }

  /// access tag
  const std::string & name() const {return m_tag;}

  /// change tag name
  void rename(const std::string & s) {m_tag = s;}

  /// check if attribute exists
  bool hasAttribute(const std::string & key) const
  {return m_attributes.find(key) != m_attributes.end();}

  /// access attribute
  const std::string & attribute(const std::string & key) const;

  /// access attribute, provide default value
  const std::string & attribute(const std::string & key,
                                const std::string & strDefault) const;

  /// attribute iterator access
  attr_iterator attrBegin() const {return m_attributes.begin();}

  /// attribute iterator access
  attr_iterator attrEnd() const {return m_attributes.end();}

  /// if attribute present, convert to float, else return default
  double attr2float(const std::string & key, double x) const;

  /// if attribute present, convert to int, else return default
  int attr2int(const std::string & key, int x) const;

  /// if attribute present, convert to bool, else return default
  bool attr2bool(const std::string & key, bool x) const;

  /// use std::stringstream to set attrbute only when present
  template <class Streamable>
  bool fromAttribute(const std::string & key, Streamable & sth) const
  {
    attr_iterator itr = m_attributes.find(key);
    if (itr == m_attributes.end()) {
      return false;
    } else {
      std::stringstream ss;
      ss << itr->second;
      ss >> sth;
    }
    return true;
  }

  /// access attribute
  std::string & attribute(const std::string & key) {return m_attributes[key];}

  /// access attribute
  std::string & operator[] (const std::string & key) {return m_attributes[key];}

  /// access text
  const std::string & text() const {return m_txt;}

  /// change text
  std::string & text() {
    m_nbytes = 0; m_typecode = TypeCode::None; m_blob.reset();
    return m_txt;
  }

  /// change text
  void text(const std::string & s) {
    m_nbytes = 0;
    m_typecode = TypeCode::None;
    m_blob.reset();
    m_txt=s;
  }

  /// change text
  void text(const char *ptr, size_t n) {
    m_nbytes = 0;
    m_typecode = TypeCode::None;
    m_blob.reset();
    m_txt.assign(ptr, ptr+n);
  }

  /// iterate over children
  const_iterator begin() const {return m_siblings.begin();}

  /// iterate over children
  const_iterator end() const {return m_siblings.end();}

  /// find first child with tag "tg"
  const_iterator findChild(const std::string & s) const;

  /// find first node matching path, return 0 if not found
  const XmlElement *findNode(const std::string & path) const;

  /// find first element matching tag, using depth-first search
  const XmlElement *findAnyTag(const std::string &tag) const;

  /// iterate over children
  mutable_iterator mbegin() {return m_siblings.begin();}

  /// iterate over children
  mutable_iterator mend() {return m_siblings.end();}

  /// append a child element
  size_t append(const XmlElement & c) {
    m_siblings.push_back(c);
    return m_siblings.size() - 1;
  }

  /// append a child element
  size_t append(XmlElement &&c) {
    m_siblings.push_back(std::move(c));
    return m_siblings.size() - 1;
  }

  /// replace if already present, else append a child element
  size_t replaceAppend(const XmlElement &c);

  /// create a child element with tag and text content, append
  XmlElement & append(const std::string &childTag,
                      const std::string &childText = std::string());

  /// for convenience: Create an labeled child element containing vector data
  template <class ElementType>
  XmlElement & append(const std::string &childTag,
                      size_t nvalues, const ElementType values[],
                      bool share = false)
  {
    XmlElement childElement(childTag);
    childElement["count"] = std::to_string(nvalues);
    childElement.asBinary(nvalues, values, share);
    size_t idx = this->append( std::move(childElement) );
    return m_siblings[idx];
  }

  /// count child elements
  uint children() const {return m_siblings.size();}

  /// erase child element k
  void eraseChild(uint k) {
    m_siblings.erase( m_siblings.begin() + k );
  }

  /// replace child element
  void replace(uint k, const XmlElement & xe) {
    assert(k < m_siblings.size());
    m_siblings[k] = xe;
  }

  /// register binary instead of character data payload, copy or link content
  template <typename ScalarType>
  void asBinary(size_t nval, const ScalarType a[], bool share = false) {
    TypeCode tc = TypeCode::of<ScalarType>();
    m_typecode = tc.value();
    m_nbytes = nval * sizeof(ScalarType);
    if (share) {
      m_blob = BlobType((char *) a, null_deleter());
    } else {
      m_blob = BlobType(new char[m_nbytes]);
      memcpy(&m_blob[0], a, m_nbytes);
    }
    m_attributes["bdata_bytes"] = std::to_string(m_nbytes);
    m_attributes["bdata_type"] = TypeCode(m_typecode).toString();

    // default storage format is little endian
    if (is_bigendian())
      m_attributes["bdata_bigendian"] = "true";
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, int a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, uint a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, int8_t a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, uint8_t a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, int16_t a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, uint16_t a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, int64_t a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, uint64_t a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, float a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, double a[]) const {
    fetchAnything(n, a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, std::complex<float> a[]) const {
    fetchAnything(2*n, (float *) a);
  }

  /// universal access functions which use binary or text (exception on size mismatch)
  void fetch(size_t n, std::complex<double> a[]) const {
    fetchAnything(2*n, (double *) a);
  }

  /// typecode for binary payload
  int blobType() const {return m_typecode;}

  /// access pointer to binary payload
  const char *blobPointer() const {assert(m_blob); return &m_blob[0];}

  /// number of bytes in blob
  size_t blobBytes() const {return m_nbytes;}

  /// access shared pointer to block of binary data
  BlobType blob() const {return m_blob;}

  /// shrink members to minimum size
  void shrink();

  /// make a deep copy of contained data
  void detach();

  /// read from stream in specified format
  bool read(std::istream &in, int format);

  /// write to stream in specified format
  bool write(std::ostream &os, int format) const;

  /// read from any supported file
  void read(const std::string & fname);

  /// read element from currently open file in zip archive
  void read(ZipFile & zf);

  /// write to file in format provided as argument
  void write(const std::string & fname, StorageFormat fmt) const;

  /// return GBF representation
  BinFileNodePtr toGbf(bool share = true) const;

  /// construct from GBF representation
  void fromGbf(const BinFileNodePtr &bfp, bool share=true);

#ifdef HAVE_HDF5

  /// append HDF5 representation to existing group
  void toHdf5(Hdf5Group &parent) const;

#endif

  // deprecated interface
  void array2text(size_t n, const double a[]) {asBinary(n, a, false);}

  // deprecated interface
  void array2text(size_t n, const float a[]) {asBinary(n, a, false);}

  // deprecated interface
  void array2text(size_t n, const int a[]) {asBinary(n, a, false);}

  // deprecated interface
  void array2text(size_t n, const uint a[]) {asBinary(n, a, false);}

  // deprecated interface
  size_t text2array(size_t n, double a[]) const {fetch(n,a); return n;}

  // deprecated interface
  size_t text2array(size_t n, float a[]) const {fetch(n,a); return n;}

  // deprecated interface
  size_t text2array(size_t n, int a[]) const {fetch(n,a); return n;}

  // deprecated interface
  size_t text2array(size_t n, uint a[]) const {fetch(n,a); return n;}

  /// store into zip file
  void zwrite(const std::string & zfile, int compression = 1) const;

  /// read from zip file
  void zread(const std::string & zfile);

protected:

  /// write node with binary data
  void zwrite(std::ostream & xs, ZipFile & zf, uint indent) const;

  /// read child with binary data
  void zread(ZipFile & zf);

  /// write root element to plain ascii xml file
  void xwrite(const std::string & fname) const;

  /// read node recursively from plain text file, ignore binary data
  void xread(std::istream & in);

  /// write as plain xml text, dump binary to CDATA
  void xwrite(std::ostream & os, uint indent=0) const;

  /// extract array from text content
  template <typename Scalar>
  void fetchAnything(size_t n, Scalar a[]) const {
    if (m_nbytes > 0) {
      TypeCode tc(m_typecode);
      size_t nval = m_nbytes / tc.width();
      if (nval < n)
        throw Error("XmlElement::fetch() Requested more data than stored in this node.");

      if ( not tc.extract(nval, blobPointer(), a) )
        throw Error(std::string("XmlElement::fetch() Type mismatch: ")
                    +tc.toString()+" != "+TypeCode::of<Scalar>().toString());

    } else if (not m_txt.empty()) {
      const char *pos = m_txt.c_str();
      char *tail(0);
      size_t i;
      for (i=0; i<n; ++i) {
        if (not TypeCode::fromString(pos, &tail, a[i]))
          break;
        pos = tail;
      }
      if (i < n) {
        std::string msg = "XmlElement::fetch(int) failed to find "
                          "enough elements in CDATA.";
        msg += " Node: " + name() + " Expected: " + std::to_string(n)
               + " Found: " + std::to_string(i);
        msg += " Text: " + std::string(pos).substr(0, 6) + "...";
        throw Error(msg);
      }
    }
  }

  /// dump binary data to text stream
  void binaryToText(std::ostream & os) const;

private:

  /// tag name and enclosed text
  std::string m_tag, m_txt;

  /// attribute map
  StringMap m_attributes;

  /// children
  ElementList m_siblings;

  /// type of binary data included
  int m_typecode;

  /// storage for binary data
  BlobType m_blob;

  /// number of bytes stored
  size_t m_nbytes;
};



#endif
