
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

#include "xmlelement.h"
#include "defines.h"
#include "xcept.h"
#include "zipfile.h"
#include "strutils.h"
#include "algo.h"
#include "timing.h"
#include "binfilenode.h"
#include "ioglue.h"
#include "dbprint.h"

#include <boost/smart_ptr/make_shared_array.hpp>
#include <stack>
#include <cstdlib>
#include "expat/expat.h"

using std::string;
using std::stringstream;

typedef std::stack<XmlElement> ElmStack;

// handler functions for expat with C linkage
extern "C"
{
static void handle_start(void *udata, const XML_Char *element, const XML_Char **attr);
static void handle_end(void *udata, const XML_Char *element);
static void handle_text(void *udata, const XML_Char *buf, int len);
}

// ----------------- XmlElement --------------------------------

XmlElement::const_iterator XmlElement::findChild(const string & tg) const
{
  // find first child named tg
  const_iterator last(end()), itr = begin();
  while (itr != last and itr->name() != tg)
    ++itr;
  return itr;
}

const XmlElement *XmlElement::findNode(const string &path) const
{
  // look for first slash in string
  string::size_type pslash = path.find_first_of('/');

  // handle leading or trailing slash
  if (pslash == path.length()-1)
    return findNode( path.substr(0,pslash) );
  else if (pslash == 0)
    return findNode(path.substr(1));

  // slice path at first slash
  if (pslash != string::npos) {

    // look for child named as the leading part of the path
    const_iterator ichild = findChild( path.substr(0,pslash) );
    if (ichild == end())
      return nullptr;

    // recurse for path chopped off at the front
    return ichild->findNode( path.substr(pslash+1) );

  } else {
    const_iterator itr = findChild(path);
    if (itr == end())
      return nullptr;
    else
      return &(*itr);
  }
}

const XmlElement *XmlElement::findAnyTag(const std::string &tag) const
{
  if (name() == tag)
    return this;

  for (const XmlElement &child : m_siblings) {
    const XmlElement *p = child.findAnyTag(tag);
    if (p != nullptr)
      return p;
  }

  return nullptr;
}

size_t XmlElement::replaceAppend(const XmlElement &c)
{
  const_iterator pos = findChild(c.name());
  while (pos != end()) {
    eraseChild( std::distance(begin(), pos) );
    pos = findChild(c.name());
  }
  return append(c);
}

XmlElement &XmlElement::append(const std::string &childTag,
                               const std::string &childText)
{
  XmlElement child(childTag);
  if (not childText.empty())
    child.text(childText);
  m_siblings.push_back(child);
  return m_siblings.back();
}

const string & XmlElement::attribute(const string & key) const
{     
  StringMap::const_iterator itm = m_attributes.find(key);
  if (itm != m_attributes.end())
    return itm->second;
  else
    throw Error("Element "+m_tag+" has no attribute named "+key);
}

const string & XmlElement::attribute(const string & key,
                                     const string & strDefault) const
{
  StringMap::const_iterator itm = m_attributes.find(key);
  if (itm != m_attributes.end())
    return itm->second;
  else
    return strDefault;
}

double XmlElement::attr2float(const std::string & key, double x) const
{
  StringMap::const_iterator itm = m_attributes.find(key);
  if (itm != m_attributes.end())
    return atof( itm->second.c_str() );
  else
    return x;
}

int XmlElement::attr2int(const std::string & key, int x) const
{
  StringMap::const_iterator itm = m_attributes.find(key);
  if (itm != m_attributes.end())
    return atol( itm->second.c_str() );
  else
    return x;
}

bool XmlElement::attr2bool(const std::string &key, bool x) const
{
  bool flag = x;
  StringMap::const_iterator itm = m_attributes.find(key);
  if (itm != m_attributes.end())
    fromString( itm->second.c_str(), flag );
  return flag;
}

void XmlElement::shrink()
{
  // trim off whitespace from character data content
  if (not m_txt.empty()) {
    string::size_type p1, p2;
    p1 = m_txt.find_first_not_of(" \n\t\r");
    p2 = m_txt.find_last_not_of(" \n\t\r");
    if ( (p1 == string::npos and p2 == string::npos) or p1 > p2 )
      string().swap(m_txt);
    else
      string(m_txt, p1, p2-p1+1).swap(m_txt);
  }
}

void XmlElement::detach()
{
  m_siblings.detach();
  if ((m_nbytes > 0) and (not m_blob.unique())) {
    char *tmp = new char[m_nbytes];
    memcpy(tmp, m_blob.get(), m_nbytes);
    m_blob = BlobType(tmp);
  }
}

bool XmlElement::read(std::istream &in, int format)
{
  BinFileNodePtr bfp;
  switch (format) {
  case PlainText:
    this->xread(in);
    return true;
  case ZippedXml:
    // ZipFile interface needs a file
    return false;
  case Lz4Compressed:
  default:
    bfp = BinFileNode::create("XmlElement");
    bfp->read(in);
    fromGbf(bfp, true);
    return true;
  }

  return false;
}

bool XmlElement::write(std::ostream &os, int format) const
{
  BinFileNodePtr bfp;
  switch (format) {
  case PlainText:
    this->xwrite(os);
    return true;
  case ZippedXml:
    // ZipFile interface needs a file
    return false;
  case Lz4Compressed:
  default:
    bfp = toGbf(true);
    return bfp->write(os, BinFileNode::CompressedLZ4);
  }

  return false;
}

void XmlElement::write(const string & fname, StorageFormat fmt) const
{
  BinFileNodePtr bfp;
  switch (fmt) {
  case PlainText:
    this->xwrite(fname);
    break;
  case ZippedXml:
    this->zwrite(fname);
    break;
  case Lz4Compressed:
  default:
    bfp = this->toGbf(true);
    bfp->write(fname, BinFileNode::CompressedLZ4);
    break;
  }
}

void XmlElement::xwrite(const string & fname) const
{
  ofstream os(asPath(fname).c_str());
  if (not os)
    throw Error("Cannot write to file: "+fname);

  // this function call actually requests to dump all data, including
  // binary, to text format, so we call xwrite for the conversion
  os << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
  xwrite(os);
}

void XmlElement::xwrite(std::ostream & os, uint indent) const
{
  if (m_tag.size() == 0)
    return;
  
  string pre(indent, ' ');
  os << pre << '<' << m_tag;
  
  // when writing attributes to plain text xml, drop all internally
  // used "bdata_" attributes unless there actually is binary data stored
  StringMap::const_iterator itm;
  for (itm = m_attributes.begin(); itm != m_attributes.end(); ++itm) {
    os << ' ' << itm->first << "=\"" << itm->second << "\"";
  }
  
  if (m_siblings.size() == 0 and m_txt.size() == 0 and m_nbytes == 0)
    os << "/>\n";
  else {
    os << ">\n";

    if (m_txt.size() > 0)
      os << "<![CDATA[" << m_txt << "]]>";
    else if (m_nbytes > 0)
      binaryToText(os);
    
    const_iterator itr;
    for (itr = begin(); itr != end(); ++itr)
      itr->xwrite(os,indent+2);

    os << pre << "</" << m_tag << ">\n";
  }
}

void XmlElement::read(ZipFile & zf)
{
  // initialize expat and parse document
  XML_Parser p = XML_ParserCreate(0);

  ElmStack *es = new ElmStack;
  XML_SetUserData(p, (void*) es);
  XML_SetStartElementHandler(p, handle_start);
  XML_SetEndElementHandler(p, handle_end);
  XML_SetCharacterDataHandler(p, handle_text);

  // process files in 128k chunks
  char *buf(0);
  const int bufbytes(131072);
  int rbytes(0);

  XML_Bool final;
  XML_Status stat;

  if (not zf.openCurrentFile())
    throw Error("XmlElement: Cannot open current file in archive.");

  do {

    buf = (char *) XML_GetBuffer(p, bufbytes);
    if (buf == 0)
      throw Error("expat : out of memory.");

    rbytes = zf.read(bufbytes, buf);
    final = (rbytes == bufbytes) ? XML_FALSE : XML_TRUE;

    stat = XML_ParseBuffer(p, rbytes, final);

  } while (final == XML_FALSE and stat == XML_STATUS_OK);

  zf.closeCurrentFile();

  if (stat != XML_STATUS_OK) {

    stringstream ss;
    XML_Error code = XML_GetErrorCode(p);
    ss << "libexpat reported XML parsing error (" << code << "): " << endl;
    ss << XML_ErrorString(code);
    ss << "\n at line " << XML_GetCurrentLineNumber(p);
    ss << ", column " << XML_GetCurrentColumnNumber(p);

    delete es;
    XML_ParserFree(p);
    throw Error(ss.str());
  }

  // copy root element
  assert(es->size() == 1);
  *this = es->top();

  // cleanup
  delete es;
  XML_ParserFree(p);
}

void XmlElement::read(const string & fname)
{
  // read zipped file if applicable
  if (ZipFile::isZip(fname)) {
    zread(fname);
    return;
  }
  
  // try to read as LZ4-compressed bindary
  BinFileNodePtr bfp = BinFileNode::createFromFile(fname);
  if (bfp) {
    fromGbf(bfp, true);
    return;
  }

  // fallback : try to read as plain-text XML
  ifstream in(asPath(fname).c_str());
  if (not in) {
    string msg("Cannot read file named '");
    msg += fname + "'";
    throw Error(msg);
  }

  xread(in);
}

void XmlElement::xread(std::istream & in)
{
  // initialize expat and parse document
  XML_Parser p = XML_ParserCreate(0);
  
  ElmStack *es = new ElmStack;
  XML_SetUserData(p, (void*) es);
  XML_SetStartElementHandler(p, handle_start);
  XML_SetEndElementHandler(p, handle_end);
  XML_SetCharacterDataHandler(p, handle_text);
  
  // process files in 128k chunks
  char *buf(0);
  const int bufbytes(131072);
  int rbytes(0);
  
  XML_Bool final;
  XML_Status stat;
  do {

    buf = (char *) XML_GetBuffer(p, bufbytes);
    if (buf == 0)
      throw Error("expat : out of memory.");
    
    in.read(buf, bufbytes);
    rbytes = in.gcount();
    final = (rbytes == bufbytes) ? XML_FALSE : XML_TRUE;
    
    stat = XML_ParseBuffer(p, rbytes, final);
    
  } while (final == XML_FALSE and stat == XML_STATUS_OK);
  
  if (stat != XML_STATUS_OK) {
    
    stringstream ss;
    XML_Error code = XML_GetErrorCode(p);
    ss << "libexpat reported XML parsing error (" << code << "): " << endl;
    ss << XML_ErrorString(code);
    ss << "\n at line " << XML_GetCurrentLineNumber(p);
    ss << ", column " << XML_GetCurrentColumnNumber(p);

    delete es;
    XML_ParserFree(p);
    throw Error(ss.str());
  }
  
  // copy root element
  assert(es->size() == 1);
  *this = es->top();

  // cleanup
  delete es;
  XML_ParserFree(p);
}

template <typename ElementType>
static inline void dumpIntText(size_t nByte, const ElementType a[],
                               std::ostream & os)
{
  const size_t n = nByte / sizeof(ElementType);
  if (n == 0)
    return;

  os << "<![CDATA[" << endl;
  const size_t nrows = n/8;
  for (size_t ir=0; ir<nrows; ++ir) {
    os << (+a[8*ir]) << ' ' << (+a[8*ir+1]) << ' ';
    os << (+a[8*ir+2]) << ' ' << (+a[8*ir+3]) << ' ';
    os << (+a[8*ir+4]) << ' ' << (+a[8*ir+5]) << ' ';
    os << (+a[8*ir+6]) << ' ' << (+a[8*ir+7]) << '\n';
  }
  for (size_t i=8*nrows; i<n; ++i)
    os << (+a[i]) << ' ';
  if (8*nrows < n)
    os << '\n';
  os << "]]>";
}

template <typename ElementType>
static inline void dumpFloatText(size_t nByte, const ElementType a[],
                                 std::ostream & os)
{
  size_t n = nByte/sizeof(ElementType);
  if (n == 0)
    return;

  os << "<![CDATA[" << endl;
  os << std::scientific;
  size_t nrows = n/8;
  for (size_t ir=0; ir<nrows; ++ir) {
    os << a[8*ir] << ' ' << a[8*ir+1] << ' ';
    os << a[8*ir+2] << ' ' << a[8*ir+3] << ' ';
    os << a[8*ir+4] << ' ' << a[8*ir+5] << ' ';
    os << a[8*ir+6] << ' ' << a[8*ir+7] << '\n';
  }
  for (size_t i=8*nrows; i<n; ++i)
    os << a[i] << ' ';
  if (8*nrows < n)
    os << '\n';
  os << "]]>";
}

void XmlElement::binaryToText(std::ostream & os) const
{
  switch (m_typecode) {
  case TypeCode::None:
    os << "<![CDATA[";
    os.write(&m_blob[0], m_nbytes);
    os << "]]>";
    break;
  case TypeCode::Int8:
    dumpIntText(m_nbytes, (const int8_t *) blobPointer(), os);
    break;
  case TypeCode::UInt8:
    dumpIntText(m_nbytes, (const uint8_t *) blobPointer(), os);
    break;
  case TypeCode::Int16:
    dumpIntText(m_nbytes, (const int16_t *) blobPointer(), os);
    break;
  case TypeCode::UInt16:
    dumpIntText(m_nbytes, (const uint16_t *) blobPointer(), os);
    break;
  case TypeCode::Int32:
    dumpIntText(m_nbytes, (const int32_t *) blobPointer(), os);
    break;
  case TypeCode::UInt32:
    dumpIntText(m_nbytes, (const uint32_t *) blobPointer(), os);
    break;
  case TypeCode::Int64:
    dumpIntText(m_nbytes, (const int64_t *) blobPointer(), os);
    break;
  case TypeCode::UInt64:
    dumpIntText(m_nbytes, (const uint64_t *) blobPointer(), os);
    break;
  case TypeCode::Float32:
  case TypeCode::Complex64:
    os.precision(7);
    dumpFloatText(m_nbytes, (const float *) blobPointer(), os);
    break;
  case TypeCode::Float64:
  case TypeCode::Complex128:
    os.precision(15);
    dumpFloatText(m_nbytes, (const double *) blobPointer(), os);
    break;
  }
}

void XmlElement::zwrite(const std::string & zfile, int compression) const
{
  ZipFile zf;
  if (not zf.createArchive(zfile))
    throw Error("XmlElement::zwrite could not create zip archive: "+zfile);

  // open the binary blob file in archive, compression level 1 turns out
  // not to be any worse than default level, but twice as fast
  if (not zf.newFile("bdata", compression))
    throw Error("XmlElement::zwrite could not create binary archive file.");

  stringstream xss;
  xss << "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n";
  zwrite(xss, zf, 0);
  xss.flush();
  if (not zf.closeFile())
    throw Error("XmlElement::zwrite could not close archive file.");

  // binary data is dumped into zip archive, while xml stream ends up in xss
  if (not zf.newFile("content.xml", compression))
    throw Error("XmlElement::zwrite could not create xml archive file.");

  // drop xml file into zip archive
  const string & s(xss.str());
  if (not zf.write(s.size(), s.c_str()))
    throw Error("XmlElement::zwrite could not write xml archive file.");

  if (not zf.closeFile())
    throw Error("XmlElement::zwrite could not close archive file.");

  if (not zf.closeArchive())
    throw Error("XmlElement::zwrite could not close archive.");
}

void XmlElement::zwrite(std::ostream & xs, ZipFile & zf, uint indent) const
{
  if (m_tag.size() == 0)
    return;
  
  string pre(indent, ' ');
  xs << pre << '<' << m_tag;

  StringMap::const_iterator itm;
  for (itm = m_attributes.begin(); itm != m_attributes.end(); ++itm) {

    // skip bdata_offset entries (written below)
    if (strstr(itm->first.c_str(), "bdata_offset") != 0)
      continue;

    // write attributes, but write bdata_* key attribute only when
    // there actually is binary data, so as not to confuse zread
    bool isbda = strstr(itm->first.c_str(), "bdata_") != 0;
    if ( (not isbda) or (m_nbytes > 0) )
      xs << " " << itm->first << "=\"" << itm->second << "\"";
  }

  // add (uncompressed) binary data offset before witing chunk
  if (m_nbytes != 0)
    xs << " bdata_offset=\"" << zf.writeOffset() << "\" ";
  
  if (m_siblings.size() == 0 and m_txt.size() == 0 and m_nbytes == 0) {
    xs << "/>\n";
  } else {
    xs << ">\n";

    // can only have text or binary payload
    if (m_txt.size() > 0) {
      xs << "<![CDATA[" << m_txt << "]]>";
    } else if (m_nbytes > 0) {

      // dump binary blob into zipfile and increment offset
      zf.write(m_nbytes, &m_blob[0]);
    }

    // write children
    const_iterator itr;
    for (itr = begin(); itr != end(); ++itr)
      itr->zwrite(xs, zf, indent+2);
    
    xs << pre << "</" << m_tag << ">\n";
  }
}

void XmlElement::zread(const std::string & zfile) 
{
  ZipFile zf;

  if (not zf.openArchive(zfile))
    throw Error("XmlElement::zread cannot open archive "+zfile);

  // retrieve xml content to be read first
  if (not zf.locateFile("content.xml")) {
    stringstream ss;
    ss << "XmlElement::zread cannot find content.xml in '" << zfile << "'.";
    ss << "Files found: ";
    do {
      ss << zf.currentFile() << ", ";
    } while (zf.nextFile());
    throw Error(ss.str());
  }

  // uncompress xml content into string stream
  stringstream xss;
  zf.dumpFile(xss);

  // then read xml document from string
  xread(xss);

  // access binary data file and open for reading
  if (not zf.locateFile("bdata"))
    throw Error("XmlElement::zread cannot find binary file in "+zfile);
  if (not zf.openCurrentFile())
    throw Error("XmlElement::zread cannot open binary file in "+zfile);

  // extract binary data
  zread(zf);

  if (not zf.closeCurrentFile())
    throw Error("XmlElement::zread could not close archive file.");
}

void XmlElement::zread(ZipFile & zf)
{
  // read binary data for this node, if any
  bool bswap = false;
  m_typecode = TypeCode::None;
  m_nbytes = 0;

  StringMap::const_iterator itm;
  itm = m_attributes.find("bdata_bytes");
  if (itm != m_attributes.end()) {
    char *tail;
    m_nbytes = genua_strtoul( itm->second.c_str(), &tail, 10 );
    if ( tail == itm->second.c_str() )
      throw Error("Cannot read bytecount: "+ itm->second);

    if (m_nbytes != 0) {

      // determine typecode
      itm = m_attributes.find("bdata_type");
      if (itm != m_attributes.end()) {
        const string & tp = itm->second;
        m_typecode = TypeCode::fromString( tp ).value();
      }

      // figure out whether we need to swap bytes
      itm = m_attributes.find("bdata_bigendian");
      if (itm == m_attributes.end())
        bswap = is_bigendian();
      else
        bswap = (itm->second == "true") and (not is_bigendian());

      // support backward compatibility - read files which may contain
      // more data than we actually need by skipping some
      itm = m_attributes.find("bdata_offset");
      if (itm != m_attributes.end()) {
        size_t tpos = genua_strtoul(itm->second.c_str(), &tail, 10);
        size_t rpos = zf.readOffset();
        // dbprint("Position: ", rpos, " offset: ", tpos);
        if (tpos > rpos) {
          size_t nskip = tpos - rpos;
          size_t stat = zf.skip(nskip);
          if (stat != nskip)
            throw Error("Attempted to skip "+str(nskip)
                        +" bytes, got only "+str(stat));
        }
      }

      // allocate space and fetch data from zip file
      try {
        m_blob = BlobType(new char[m_nbytes]);
      } catch (std::bad_alloc) {
        throw Error("XmlElement::zread failed to allocate memory, "
                    "nbytes="+str(m_nbytes));
      }

      size_t nbr = zf.read(m_nbytes, &m_blob[0]);
      if (nbr != m_nbytes)
        throw Error("XmlElement::zread failed to read binary data for object: "
                    +name()+". Expected "+str(m_nbytes)
                    +"bytes, found "+str(nbr));

      // swap bytes if necessary
      if (bswap) {
        if (TypeCode(m_typecode).width() == 2)
          swap_bytes<2>(m_nbytes, &m_blob[0]);
        else if (TypeCode(m_typecode).width() == 4)
          swap_bytes<4>(m_nbytes, &m_blob[0]);
        else if (TypeCode(m_typecode).width() == 8)
          swap_bytes<8>(m_nbytes, &m_blob[0]);
      }
    }
  }

  // fetch children recursively
  for (XmlElement &child : m_siblings)
    child.zread(zf);
}

BinFileNodePtr XmlElement::toGbf(bool share) const
{
  BinFileNodePtr bfp = BinFileNode::create( this->m_tag );

  // attributes
  bfp->attribute("gbf_format_generator", "XmlElement");
  attr_iterator ait, alast = attrEnd();
  for (ait = attrBegin(); ait != alast; ++ait)
    bfp->attribute(ait->first, ait->second);

  // TODO: Adapt when XmlElement has been switched to "typecode.h"
  if ( not m_txt.empty() ) {
    bfp->attribute("gbf_format_payload_type", "Str8");
    bfp->assign( 1, m_txt.size(), m_txt.data(), share );
  } else if (m_nbytes > 0) {
    TypeCode tc(m_typecode);
    bfp->attribute("gbf_format_payload_type", tc.toString());
    int width = tc.width();
    if (share)
      bfp->assign( width, m_nbytes/width, m_blob );
    else
      bfp->assign( width, m_nbytes/width, m_blob.get(), share );
  } else {
    bfp->attribute("gbf_format_payload_type", "Empty");
  }

  // children
  const_iterator itr, last = end();
  for (itr = begin(); itr != last; ++itr)
    bfp->append( itr->toGbf(share) );

  return bfp;
}

void XmlElement::fromGbf(const BinFileNodePtr &bfp, bool share)
{
  *this = XmlElement();
  if (hint_unlikely(bfp == nullptr))
    return;

  rename( bfp->name() );

  // attributes
  BinFileNode::AttributeIterator ait, alast = bfp->attrEnd();

  // exploit that map<string,string>::value_type is pair<string,string>
  string fmt("Empty");
  for (ait = bfp->attrBegin(); ait != alast; ++ait) {
    if (ait->first.find("gbf_format_") == string::npos)
      m_attributes.insert( *ait );
    else
      fmt = ait->second;
  }

  m_nbytes = 0;
  m_typecode = TypeCode::None;
  if ( fmt == "Str8" ) {
    text( bfp->blockPointer(), bfp->blockBytes() );
  } else if ( fmt != "Empty" ) {

    m_typecode = TypeCode::fromString( fmt ).value();
    if (TypeCode(m_typecode).width() == 0)
      throw Error("Could not identify type: "+fmt);

    // allocate space and fetch data
    m_nbytes = bfp->blockBytes();
    if (m_nbytes > 0) {
      if (share) {
        m_blob = bfp->blob();
      } else {
        try {
          // copy memory block
          m_blob.reset( new char[m_nbytes] );
          memcpy( &m_blob[0], bfp->blockPointer(), m_nbytes );
        } catch (const std::bad_alloc &) {
          throw Error("XmlElement::fromGbf failed to allocate memory, nbytes="
                      +str(m_nbytes));
        }
      }
    }
  }

  // children
  const size_t nc = bfp->nchildren();
  m_siblings.reserve(nc);
  for (size_t i=0; i<nc; ++i) {
    const BinFileNodePtr & child = bfp->childNode(i);
    m_siblings.push_back( XmlElement() );
    m_siblings.back().fromGbf(child, share);
  }
}

// -------------- expat interface ---------------------------------

void handle_start(void *udata, const XML_Char *element, const XML_Char **attr)
{
  ElmStack *es = static_cast<ElmStack *>( udata );
  es->push( XmlElement(element) );

  XmlElement & xe( es->top() );
  for (uint i=0; attr[i] != 0; i += 2) {
    string key(attr[i]);
    string val(attr[i+1]);
    xe.attribute(key) = val;
  }
}

void handle_end(void *udata, const XML_Char *)
{
  ElmStack *es = static_cast<ElmStack *>( udata );
  if (es->size() > 1) {
    XmlElement last = es->top();
    last.shrink();
    es->pop();
    es->top().append(last);
  }
}

void handle_text(void *udata, const XML_Char *buf, int len)
{
  string txt(buf, len);
  ElmStack *es = static_cast<ElmStack *>( udata );
  es->top().text() += txt;
}





