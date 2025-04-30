/* Copyright (C) 2015 David Eller <david@larosterna.com>
 *
 * This program is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free Software
 * Foundation; either version 2 of the License, or (at your option) any later
 * version. This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
 * details. You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
 */

#include "binfilenode.h"
#include "lz4stream.h"
#include "strutils.h"
#include "xcept.h"
#include "algo.h"
#include "ioglue.h"
// #include "bufferedfile.h"

#include <ios>
#include <exception>

using std::string;

// magic string which identifies binary files
const char BinFileNode::s_format_tag[11] = "GBF_NODE";
const uint32_t BinFileNode::s_gbf_magic = 0xbfcf4f8b;
const uint32_t BinFileNode::s_unterminated = std::numeric_limits<uint32_t>::max()-1;

// --------------------------------------------------------------------------

template <class Stream>
static inline void bf_write_size(uint64_t s, Stream & os)
{
  uint64_t n(s);
  //  if (is_bigendian())
  //    swap_bytes<8>(8, (char *) &n);
  os.write((const char *) &n, 8);
}

template <class Stream>
static inline uint64_t bf_read_size(Stream & is)
{
  uint64_t n;
  is.read((char *) &n, 8);
  //  if (is_bigendian())
  //    swap_bytes<8>(8, (char *) &n);
  return n;
}

template <class Stream>
static inline void bf_write_string(const string & s, Stream & os)
{
  bf_write_size( s.size(), os );
  if (not s.empty())
    os.write((const char *) &s[0], s.size());
}

template <class Stream>
static inline string bf_read_string(Stream & is)
{
  uint64_t n = bf_read_size(is);
  string s;
  if (n > 0) {
    s.resize(n);
    is.read( (char *) &s[0], n );
  }
  return s;
}

// ------------------- BinFileBlock ------------------------------------------


void BinFileBlock::allocate(size_t width, size_t nbytes)
{
  m_width = width;
  m_bytes = nbytes;
  if (nbytes > 0) {
    size_t abytes = allocationSize(nbytes);
    assert(abytes > 0);
    m_block.reset( new char[abytes] );
  } else {
    m_block.reset();
  }
}

void BinFileBlock::create(size_t width, size_t nbytes,
                          const void *a, bool share)
{
  m_width = width;
  m_bytes = nbytes;
  if (share) {
    m_block.reset( (char *) a, null_deleter() );
  } else {
    allocate(width, nbytes);
    memcpy(m_block.get(), a, nbytes);
  }
}

void BinFileBlock::create(size_t width, size_t nbytes, BinFileBlock::BlobType b)
{
  m_width = width;
  m_bytes = nbytes;
  m_block = b;
}

void BinFileBlock::clear()
{
  m_bytes = 0;
  m_width = 0;
  m_block.reset();
}

void BinFileBlock::write(std::ostream & os) const
{
  bf_write_size( m_bytes, os );
  bf_write_size( m_width, os );
  if (m_bytes > 0)
    os.write( m_block.get(), m_bytes );
}

void BinFileBlock::read(std::istream & is)
{
  m_bytes = bf_read_size(is);
  m_width = (int) bf_read_size(is);
  try {
    allocate(m_width, m_bytes);
  } catch (std::bad_alloc &) {
    throw Error("BinFileBlock: Failed to allocate block, nbytes = "+str(m_bytes));
  }
  if (m_bytes > 0)
    is.read(m_block.get(), m_bytes);
}

//void BinFileBlock::write(BufferedFile &os) const
//{
//  bf_write_size( m_bytes, os );
//  bf_write_size( m_width, os );
//  if (m_bytes > 0)
//    os.write( m_block.get(), m_bytes );
//}

//void BinFileBlock::read(BufferedFile & is)
//{
//  m_bytes = bf_read_size(is);
//  m_width = (int) bf_read_size(is);
//  try {
//    m_block.reset( new char[m_bytes] );
//  } catch (std::bad_alloc &) {
//    throw Error("BinFileBlock: Failed to allocate block, nbytes = "+str(m_bytes));
//  }
//  if (m_bytes > 0)
//    is.read(m_block.get(), m_bytes);
//}

// ------------------- BinFileNode --------------------------------------------

struct AttribPred
{
  AttribPred(const std::string & s) : m_key(s) {}

  bool operator() ( const BinFileNode::Attribute & a ) const {
    return (a.first == m_key);
  }

  const std::string & m_key;
};

bool BinFileNode::hasAttribute(const string &key)
{
  AttribPred pred(key);
  AttributeArray::const_iterator pos;
  pos = std::find_if(m_attrib.begin(), m_attrib.end(), pred);
  return (pos != m_attrib.end());
}

void BinFileNode::attribute(const string &key, const string &value)
{
  AttribPred pred(key);
  AttributeArray::iterator pos;
  pos = std::find_if(m_attrib.begin(), m_attrib.end(), pred);
  if (pos == m_attrib.end()) {
    m_attrib.push_back( std::make_pair(key, value) );
  } else {
    pos->second = value;
  }
}

const std::string & BinFileNode::attribute(const std::string & key) const
{
  AttribPred pred(key);
  AttributeArray::const_iterator pos;
  pos = std::find_if(m_attrib.begin(), m_attrib.end(), pred);

  if (pos != m_attrib.end())
    return pos->second;
  else
    throw Error("BinFileNode "+m_id+" doesn't have attribute "+key);
}

BinFileNodePtr BinFileNode::findChild(const string &id) const
{
  BinFileNodePtr bfp;
  const size_t n = nchildren();
  for (size_t i=0; i<n; ++i) {
    if (childNode(i) and childNode(i)->name() == id)
      return childNode(i);
  }
  return bfp;
}


void BinFileNode::writePlain(std::ostream & os) const
{
  // identification tag and node identifier
  os.write( s_format_tag, sizeof(s_format_tag) );
  bf_write_string( m_id, os );

  // write attributes
  bf_write_size( m_attrib.size(), os );
  const int na = m_attrib.size();
  for (int i=0; i<na; ++i) {
    bf_write_string( m_attrib[i].first, os );
    bf_write_string( m_attrib[i].second, os );
  }

  // write data block
  m_block.write( os );

  // write all children if any
  size_t nc = m_children.size();
  bf_write_size( nc, os );
  for (size_t i=0; i<nc; ++i)
    m_children[i]->writePlain(os);
}

bool BinFileNode::readPlain(std::istream & is)
{ 
  // check that identification tag is present
  const int tagSize = sizeof(s_format_tag);
  char tag[tagSize];
  is.read( tag, tagSize );
  if ( strcmp(tag, s_format_tag) != 0 )
    return false;
  
  // read node name
  m_id = bf_read_string(is);
  
  // read attributes
  m_attrib.clear();
  size_t nattr = bf_read_size(is);
  string key, value;
  for (size_t i=0; i<nattr; ++i) {
    key = bf_read_string(is);
    value = bf_read_string(is);
    attribute(key, value);
  }
  
  // read data block
  m_block.read(is);
  
  // read child nodes
  size_t nc = bf_read_size(is);
  m_children.resize(nc);
  for (size_t i=0; i<nc; ++i) {
    m_children[i] = BinFileNode::create("", this);
    m_children[i]->readPlain(is);
  }

  return true;
}

BinFileNodePtr BinFileNode::createFromFile(const std::string fname)
{
  BinFileNodePtr bfn = BinFileNode::create("Root", 0); // root node

  // try to open as LZ4 stream first
  ifstream inz( asPath(fname).c_str(), std::ios::in | std::ios::binary);
  Lz4Stream lzs;
  if (lzs.openRead(inz)) {
    if ( not bfn->readNodeLZ4( inz, lzs ) )
      throw Error("Extraction of node from LZ4-compressed file failed.");
    if ( not lzs.closeRead(inz) )
      throw Error("Checksum error, corrupt LZ4 file.");
    return bfn;
  }

  // arrive here only if attempt to read LZ4 stream failed
  inz.close();
  ifstream inp( asPath(fname).c_str(), std::ios::in | std::ios::binary);
  if ( bfn->readPlain(inp) )
    return bfn;
  else
    return BinFileNodePtr();
}

std::ostream & BinFileNode::summary(ostream &os, int indent) const
{
  string pfx(indent, ' ');
  os << pfx << "Node: " << m_id << endl;
  os << pfx << "Block: " << m_block.bytes() << endl;
  os << pfx << m_attrib.size() << " attributes: " << endl;
  for (size_t i=0; i<m_attrib.size(); ++i)
    os << pfx << '[' << i << "] " << m_attrib[i].first
       << " = " << m_attrib[i].second << endl;
  for (size_t j=0; j<m_children.size(); ++j)
    m_children[j]->summary(os, indent+2);
  os << pfx << "End of Node: [" << m_id  << ']' << endl;
  return os;
}

bool BinFileNode::read(std::istream &in)
{
  // try to open as LZ4 stream first
  Lz4Stream lzs;
  if (lzs.openRead(in)) {
    if ( not readNodeLZ4( in, lzs ) )
      throw Error("Extraction of node from LZ4-compressed file failed.");
    if ( not lzs.closeRead(in) )
      throw Error("Checksum error, corrupt LZ4 file.");
    return true;
  } else {
    return readPlain(in);
  }
  return false;
}

bool BinFileNode::write(std::ostream &os, int format) const
{
  if (format == PlainBinary) {
    writePlain(os);
  } else if (format == CompressedLZ4) {
    Lz4Stream lzs;
    lzs.openWrite(os);
    writeNodeLZ4(os, lzs);
    lzs.closeWrite(os);
  } else {
    return false;
  }
  return true;
}

void BinFileNode::write(const std::string & fname, int format) const
{
  ofstream os( asPath(fname).c_str(), std::ios::out | std::ios::binary);
  if (format == PlainBinary or format == CompressedLZ4) {
    write(os, format);
  } else {
    throw Error("BinFileNode: File format not recognized.");
  }
}

float BinFileNode::megabytes() const
{
  float b = 1.0e-6f * (sizeof(BinFileNode) + m_block.bytes());
  for (size_t i=0; i<nchildren(); ++i)
    b += childNode(i)->megabytes();
  return b;
}

bool BinFileNode::writeNodeLZ4(ostream &os,
                               Lz4Stream &lzs, bool terminate) const
{
  // write fixed-size descriptor containing dataset sizes
  NodeDescriptor nd = descriptor(terminate);
  size_t bw = lzs.write(os, (const char *) &nd, sizeof(nd));
  bool status = (bw == sizeof(nd));

  // write string table
  {
    std::vector<char> tmp( nd.nTableBytes );
    createStringTable(&tmp[0]);
    bw = lzs.write(os, &tmp[0], nd.nTableBytes);
    status &= (bw == nd.nTableBytes);
  }

  // write data block
  if (nd.nBlockBytes > 0) {
    bw = lzs.write(os, m_block.pointer(), nd.nBlockBytes);
    status &= (bw == nd.nBlockBytes);
  }

  for (size_t i=0; i<m_children.size(); ++i)
    status &= m_children[i]->writeNodeLZ4(os, lzs);

  return status;
}

bool BinFileNode::readNodeLZ4(istream &in, Lz4Stream &lzs)
{
  NodeDescriptor nd;
  uint64_t nrd(0);
  nrd = lzs.read(in, (char *) &nd, sizeof(nd));
  if (nrd != sizeof(nd))
    return false;
  else if (nd.magicTag != s_gbf_magic)
    return false;

  // fetch string data: id and attributes
  {
    size_t bufSize = Lz4Stream::bufferSize(nd.nTableBytes);
    std::vector<char> tmp( bufSize );
    nrd = lzs.read(in, &tmp[0], nd.nTableBytes);
    if (nrd != nd.nTableBytes)
      return false;
    extractStringTable(nd, &tmp[0]);
  }

  // retrieve data block
  if (nd.nBlockBytes > 0) {
    m_block.allocate( nd.nBlockTypeWidth, nd.nBlockBytes );
    nrd = lzs.read(in, m_block.pointer(), nd.nBlockBytes);
    if (nrd != nd.nBlockBytes)
      return false;
  }

  if (nd.nChildNodes != s_unterminated) {
    m_children.resize(nd.nChildNodes);
    for (uint32_t i=0; i<nd.nChildNodes; ++i) {
      BinFileNodePtr bfp = BinFileNode::create("", this);
      if (not bfp->readNodeLZ4(in, lzs))
        return false;
      m_children[i] = bfp;
    }
  } else {
    m_children.clear();
    m_children.reserve(16);
    bool nodeRead = false;
    do {
      BinFileNodePtr bfp = BinFileNode::create("", this);
      nodeRead = bfp->readNodeLZ4(in, lzs);
      if (nodeRead)
        this->append(bfp);
    } while (nodeRead);
  }

  return true;
}

BinFileNode::NodeDescriptor BinFileNode::descriptor(bool terminate) const
{
  NodeDescriptor nd;
  nd.magicTag = s_gbf_magic;
  nd.nAttributes = m_attrib.size();
  nd.nBlockBytes = m_block.bytes();
  nd.nBlockTypeWidth = m_block.typeWidth();
  nd.nChildNodes = terminate ? m_children.size() : s_unterminated;

  // determine table size
  nd.nTableBytes = 4 + m_id.size();
  for (size_t i=0; i<m_attrib.size(); ++i) {
    nd.nTableBytes += 4 + m_attrib[i].first.size();
    nd.nTableBytes += 4 + m_attrib[i].second.size();
  }

  return nd;
}

static inline char *append_table(const std::string &s, char *buffer)
{
  uint32_t nbytes = s.size();
  memcpy(buffer, &nbytes, 4);
  buffer += 4;
  memcpy(buffer, s.data(), nbytes);
  return buffer + nbytes;
}

char *BinFileNode::createStringTable(char *buffer) const
{
  buffer = append_table( m_id, buffer );
  for (size_t i=0; i<m_attrib.size(); ++i) {
    buffer = append_table( m_attrib[i].first, buffer );
    buffer = append_table( m_attrib[i].second, buffer );
  }
  return buffer;
}

static inline const char *extract_table(const char *buffer, std::string &s)
{
  int32_t nbytes;
  memcpy(&nbytes, buffer, 4);
  buffer += 4;
  assert(nbytes >= 0);
  assert(nbytes < (1 << 16));  // debug
  if (nbytes > 0) {
    s = std::string( buffer, buffer+nbytes );
    buffer += nbytes;
  } else {
    s.clear();
  }
  return buffer;
}

void BinFileNode::extractStringTable(const NodeDescriptor &nd,
                                     const char *buffer)
{
  const char *itr = buffer;
  itr = extract_table( itr, m_id );
  m_attrib.resize( nd.nAttributes );
  for (uint32_t i=0; i<nd.nAttributes; ++i) {
    itr = extract_table( itr, m_attrib[i].first );
    assert(itr <= buffer+nd.nTableBytes);
    itr = extract_table( itr, m_attrib[i].second );
    assert(itr <= buffer+nd.nTableBytes);
  }
  assert(itr == buffer+nd.nTableBytes);
}
