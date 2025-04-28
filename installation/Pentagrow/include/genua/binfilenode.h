
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
 
#ifndef GENUA_BINFILENODE_H
#define GENUA_BINFILENODE_H

#include "algo.h"
#include "forward.h"
#include <boost/mpl/clear.hpp>
#include <boost/shared_array.hpp>
#include <cstring>
#include <iostream>
#include <map>

/** Raw data block for binary files.
 *
 * This is a single data block as written to binary files in the simple
 * GBF format.
 *
 * \ingroup io
 * \sa BinFileNode
 */
class BinFileBlock
{
public:

  typedef boost::shared_ptr<char[]> BlobType;

  /// create empty block
  BinFileBlock() : m_bytes(0), m_width(1) {}

  /// allocate storage
  void allocate(size_t width, size_t nbytes);

  /// create block from array, optionally copy data (legacy interface)
  template <int width>
  void create(size_t nbytes, const void *a, bool share = false) {
    this->create(size_t(width), nbytes, a, share);
  }

  /// create block from array, optionally copy data
  void create(size_t width, size_t nbytes,
              const void *a, bool share = false);

  /// copy smart pointer to block of binary data
  void create(size_t width, size_t nbytes, BlobType b);

  /// element width
  int typeWidth() const {return m_width;}

  /// number of bytes in block
  size_t bytes() const {return m_bytes;}

  /// number of array elements stored
  size_t elements() const {return m_bytes/m_width;}

  /// access pointer to block
  const char *pointer() const {return &m_block[0];}

  /// access pointer to block
  char *pointer() {return &m_block[0];}

  /// access blob as a shared pointer
  BlobType blob() const {return m_block;}

  /// release allocated storage
  void clear();

  /// store block to stream
  void write(std::ostream & os) const;

  /// read block from stream
  void read(std::istream &is);

  /// store block to stream
  //void write(BufferedFile &os) const;

  /// read block from stream
  //void read(BufferedFile &is);

protected:

  /// allocate 64-byte blocks
  size_t allocationSize(size_t nbytes) const {
    return 64*((nbytes/64) + (nbytes%64 != 0));
  }

private:

  /// raw storage
  BlobType m_block;

  /// number of bytes in block
  uint64_t m_bytes;

  /// bytes per element
  int m_width;
};

/** Node in binary file.
 *
 * This is intended to be the simplest possible format for hierarchically
 * structured binary files which support a similar type of static data
 * structure as XML files. It is possible to map most operations on XmlElement
 * to BinFileNode without too much effort, which could make sense for objects
 * which mainly store very large arrays. Large data blocks are just treated as
 * chunks of memory; there is no handling of different datatypes. It is expected
 * that a class using BinFileNode adds attrbutes identifyng the datatype stored
 * on disk.
 *
 * BinFileNode has seen little use for a long time since XmlElement does most
 * things better (although a little slower). However, due to the restricton
 * of ZIP format files to 4GB, this class will now be used as a storage backend
 * for XmlElement.
 *
 * \ingroup io
 * \sa BinFileBlock, XmlElement
 */
class BinFileNode
{
public:

  enum FileFormat { PlainBinary, CompressedLZ4, UnknownFormat };

  typedef BinFileBlock::BlobType BlobType;
  typedef std::pair<std::string, std::string> Attribute;
  typedef std::vector<Attribute> AttributeArray;
  typedef AttributeArray::const_iterator AttributeIterator;

  /// construct empty node
  explicit BinFileNode(const std::string & s, BinFileNode *parent = 0)
    : m_id(s), m_parent(parent) {}

  /// access node name
  const std::string & name() const {return m_id;}

  /// iterate over attributes
  AttributeIterator attrBegin() const {return m_attrib.begin();}

  /// iterate over attributes
  AttributeIterator attrEnd() const {return m_attrib.end();}

  /// access attribute array
  const AttributeArray & attributes() const {return m_attrib;}

  /// return whether node is at the root
  bool isRoot() const { return (m_parent == 0); }

  /// return whether node is a leaf
  bool isLeaf() const { return m_children.empty(); }

  /// set attribute
  void attribute(const std::string & key, const std::string & value);

  /// retrieve attribute (throws exception if attribute not present)
  const std::string & attribute(const std::string & key) const;

  /// check if attribute is present
  bool hasAttribute(const std::string & key);

  /// append child node
  void append(const BinFileNodePtr & pbn) {
    if (pbn != nullptr) {
      pbn->m_parent = this;
      m_children.push_back(pbn);
    }
  }

  /// take ownership of child node pointer
  void append(BinFileNode *pbn) {
    pbn->m_parent = this;
    m_children.push_back(BinFileNodePtr(pbn));
  }

  /// assign POD array to node, copy contents (legacy interface)
  template <class Type>
  void copy(size_t n, const Type a[]) {
    m_block.create<sizeof(Type)>( n*sizeof(Type), (const void *) a, false);
  }

  /// assign POD array, optionally share data
  void assign(size_t width, size_t nval, const void *a, bool share) {
    assert(a != 0 or nval*width == 0);
    m_block.create( width, nval*width, (const void *) a, share);
  }

  /// assign POD array, optionally share data
  void assign(size_t width, size_t nval, BlobType b) {
    m_block.create(width, nval*width, b);
  }

  /// assign POD array, optionally share data
  template <typename Type>
  void assign(size_t nval, const Type *a, bool share) {
    assert(a != 0 or nval == 0);
    const size_t width = sizeof(Type);
    m_block.create( width, nval*width, (const void *) a, share);
  }

  /// shortcut
  void assign(const std::string &s, bool share) {
    this->assign(s.size(), &s[0], share);
  }

  /// access data block
  size_t blockElements() const {return m_block.elements();}

  /// access data block
  size_t blockBytes() const {return m_block.bytes();}

  /// access block element width
  int blockTypeWidth() const {return m_block.typeWidth();}

  /// access data block
  const char *blockPointer() const {return m_block.pointer();}

  /// access shared pointer for stored binray data
  BlobType blob() const {return m_block.blob();}

  /// number of children
  size_t nchildren() const {return m_children.size();}

  /// access child node
  const BinFileNodePtr & childNode(size_t inode) const {
    assert(inode < m_children.size());
    return m_children[inode];
  }

  /// access child node
  BinFileNodePtr childNode(size_t inode) {
    assert(inode < m_children.size());
    return m_children[inode];
  }

  /// access children as array for iteration
  const BinFileNodeArray &children() const {return m_children;}

  /// find a child node by name, returns nil if not found
  BinFileNodePtr findChild(const std::string &id) const;

  /// write name, attributes and block size to stream
  std::ostream & summary(std::ostream & os, int indent=0) const;

  /// read from stream (called on root node only)
  bool read(std::istream &in);

  /// write to stream in specified format
  bool write(std::ostream &os, int format) const;

  /// write to file named fname
  void write(const std::string & fname, int format = PlainBinary) const;

  /// release storage for binary data block and attribute list (not children)
  void digest(bool flag) {
    if (flag) {
      m_block.clear();
      m_attrib = AttributeArray();
    }
  }

  /// compute memory required
  float megabytes() const;

  /// recursively write to LZ4 stream
  bool writeNodeLZ4(std::ostream &os, Lz4Stream &lzs,
                    bool terminate=true) const;

  /// recursively read from LZ4 stream
  bool readNodeLZ4(std::istream &in, Lz4Stream &lzs);

  /// write plain binary data to stream
  void writePlain(std::ostream & os) const;

  /// read from plain binary stream
  bool readPlain(std::istream & is);

  /// convenience function : create empty node
  static BinFileNodePtr create(const std::string &nodeName = "",
                               BinFileNode *parent = 0)
  {
    return boost::make_shared<BinFileNode>( nodeName, parent );
  }

  /// read file and return object pointer, return null object on format mismatch
  static BinFileNodePtr createFromFile(const std::string fname);

private:

  /// fixed-size header containing sizes
  struct NodeDescriptor
  {
    uint32_t magicTag;     ///< identifier used to recognize LZ4-compressed file
    uint32_t nChildNodes;  ///< number of child nodes present
    uint32_t nAttributes;  ///< number of attribute (key/value pairs)
    uint32_t nBlockTypeWidth;  ///< width of data type in block

    uint64_t nBlockBytes;  ///< bytes in data block (only written if != 0)
    uint64_t nTableBytes;   ///< bytes in string table
  };

  /// buffer for LZ4 i/o operations
  typedef std::vector<char> IoBuffer;

  /// private constructor
  BinFileNode() : m_parent(0) {}

  /// construct node descriptor
  NodeDescriptor descriptor(bool terminate=true) const;

  /// put string table into pre-allocated buffer for writing to LZ4 stream
  char *createStringTable(char *buffer) const;

  /// extract string data from temporary storage
  void extractStringTable(const NodeDescriptor &nd, const char *buffer);

private:

  /// node name
  std::string m_id;

  /// string attributes
  AttributeArray m_attrib;

  /// data block
  BinFileBlock m_block;

  /// child nodes
  BinFileNodeArray m_children;

  /// parent node
  BinFileNode *m_parent;

  /// format identification tag
  static const char s_format_tag[11];

  /// format tag for LZ4-compressed files
  static const uint32_t s_gbf_magic;

  /// child node count which indicates an unterminated node
  static const uint32_t s_unterminated;
};

#endif
