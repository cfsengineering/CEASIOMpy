
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

#include "mxmesh.h"
#include "mxsolutiontree.h"
#include "cgmesh.h"
#include "ffanode.h"
#include "trimesh.h"
#include "dbprint.h"
#include "meshfields.h"
#include "ioglue.h"
#include "xmlelement.h"
#include <sstream>
#include <set>

using std::string;
using std::stringstream;

// ----------------- local scope --------------------------------------------

typedef std::vector<Indices> ElmCollector; // element buckets
typedef std::pair<uint, uint> ElmID;       // bucket, index
typedef std::vector<ElmID> MarkerID;       // one ElmID for each element

static string findTetgenHeader(istream &is)
{
  string line;
  while (std::getline(is, line))
  {

    // skip comment lines
    if (strchr(line.c_str(), '#') != 0)
      continue;

    line = strip(line);
    if (line.empty())
      continue;

    return line;
  }

  return string("");
}

static inline uint su2_strkey(const std::string &line, const char key[])
{
  const char *pos(0);
  char *tail(0);
  pos = strstr(line.c_str(), key);
  if (pos == 0)
    return NotFound;
  return genua_strtol(pos + strlen(key), &tail, 10);
}

static inline void su2_read_marker(uint nme, istream &in,
                                   ElmCollector &ecollect, MarkerID &mid)
{
  mid.resize(nme);

  string line;
  const char *s(0);
  char *tail;
  for (uint i = 0; i < nme; ++i)
  {
    if (not in)
      throw Error("Error in SU2 file: File ends before all marker"
                  " elements have been found.");

    // extract element type code
    std::getline(in, line);
    s = line.c_str();
    uint ecode = genua_strtol(s, &tail, 10);
    assert(tail != s);
    s = tail;
    Mx::ElementType etype = Mx::vtk2ElementType(ecode);

    // append element vertex indices to bucket
    Indices &vix(ecollect[(int)etype]);
    const int nve = MxMeshSection::nElementNodes(etype);

    // store bucket index and position in bucket for marker element
    mid[i] = std::make_pair(uint(etype), uint(vix.size() / nve));

    // extract element vertex indices
    for (int k = 0; k < nve; ++k)
    {
      uint vik = genua_strtol(s, &tail, 10);
      assert(s != tail);
      vix.push_back(vik);
      s = tail;
    }
  }
}

// ------------------- MxMesh ------------------------------------------------

void MxMesh::writeAs(const string &fname, int fmt, int compression) const
{
  BinFileNodePtr bfp;
  switch (fmt)
  {
  case Mx::NativeFormat:
    bfp = toXml(true).toGbf(true);
    bfp->write(append_suffix(fname, ".zml"),
               compression ? BinFileNode::CompressedLZ4
                           : BinFileNode::PlainBinary);
    break;
  case Mx::GbfFormat:
    bfp = gbfNode(true);
    bfp->write(append_suffix(fname, ".gbf"), BinFileNode::PlainBinary);
    break;
  case Mx::TextXmlFormat:
    toXml(true).write(append_suffix(fname, ".xml"), XmlElement::PlainText);
    break;
  case Mx::ZippedXmlFormat:
    toXml(true).zwrite(append_suffix(fname, ".zml"), compression);
    break;
  case Mx::StdCgnsFormat:
    writeCgns(append_suffix(fname, ".cgns"), false);
    break;
  case Mx::SecCgnsFormat:
    writeCgns(append_suffix(fname, ".cgns"), true);
    break;
  case Mx::FfaFormat:
    writeFFA(fname);
    break;
  case Mx::AbaqusFormat:
    writeAbaqus(append_suffix(fname, ".inp"));
    break;
  case Mx::NastranBulkFormat:
    writeNastran(append_suffix(fname, ".blk"));
    break;
  case Mx::Su2Format:
    writeSU2(append_suffix(fname, ".su2"));
    break;
  case Mx::LegacyVtkFormat:
    writeLegacyVtk(append_suffix(fname, ".vtk"));
    break;
#ifdef HAVE_NETCDF
  case Mx::TauFormat:
    writeTau(append_suffix(fname, ".taumesh"));
    break;
#endif
  case Mx::StlBinaryFormat:
    writeSTL(append_suffix(fname, ".stl"), true);
    break;
  case Mx::StlTextFormat:
    writeSTL(append_suffix(fname, ".txt"), false);
    break;
#ifdef HAVE_RPLY
  case Mx::PlyTextFormat:
    writePLY(append_suffix(fname, ".ply"), false);
    break;
  case Mx::PlyBinaryFormat:
    writePLY(append_suffix(fname, ".ply"), true);
    break;
#endif
  default:
    throw Error("MxMesh: Output format not supported.");
  }
}

void MxMesh::importMvz(const MeshFields &mvz)
{
  clear();

  // copy nodes
  const int nv = mvz.nvertices();
  vtx.resize(nv);
  for (int i = 0; i < nv; ++i)
  {
    vtx[i] = mvz.node(i);
    if (not std::isfinite(dot(vtx[i], vtx[i])))
      throw Error("Infinite node coordinates not allowed in MxMesh.");
  }

  // copy elements
  if (mvz.nline2() > 0)
  {
    MxMeshSection sec(this, Mx::Line2);
    sec.appendElements(mvz.nline2(), mvz.line2Vertices(0));
    sec.rename("Line Elements");
    appendSection(sec);
  }

  if (mvz.ntri3() > 0)
  {
    MxMeshSection sec(this, Mx::Tri3);
    sec.appendElements(mvz.ntri3(), mvz.tri3Vertices(0));
    sec.rename("Triangles");
    appendSection(sec);
  }

  if (mvz.nquad4() > 0)
  {
    MxMeshSection sec(this, Mx::Quad4);
    sec.appendElements(mvz.nquad4(), mvz.quad4Vertices(0));
    sec.rename("Quadrilaterals");
    appendSection(sec);
  }

  if (mvz.markerIndices().size() > 0)
  {
    MxMeshSection sec(this, Mx::Point);
    sec.appendElements(mvz.markerIndices());
    sec.rename("Point Marker");
    appendSection(sec);
  }

  // copy modeshapes first (must have lowest indices so that they do not
  // get swapped around when saving to CGNS which splits nodal/cell fields)
  const int nm = mvz.nmodes();
  Indices iegm;
  for (int i = 0; i < nm; ++i)
  {
    uint k = appendField(mvz.modename(i), mvz.eigenmode(i));
    iegm.push_back(k);
  }

  // copy real-valued scalar fields
  const int nf = mvz.nfields();
  for (int i = 0; i < nf; ++i)
  {
    if (mvz.isNodalField(i))
      appendField(mvz.fieldname(i), mvz.field(i));
  }

  // copy vector fields
  const int nvf = mvz.nvfields();
  for (int i = 0; i < nvf; ++i)
  {
    const string &fname = mvz.vfieldname(i);
    appendField(fname, mvz.vectorField(i));
  }

  // copy component sets as integer-valued cell-data
  const int ncs = mvz.ncompsets();
  for (int i = 0; i < ncs; ++i)
  {
    const Indices &idx(mvz.componentSet(i));
    DVector<int> fi(idx.begin(), idx.end());
    if (fi.size() == nelements())
      appendField(mvz.csetname(i), fi);
  }

  for (uint i = 0; i < iegm.size(); ++i)
    field(iegm[i]).annotate(XmlElement("Eigenmode"));

  // try to assemble flutter modes from named shapes
  const int nns = mvz.nshapes();
  const int nem = iegm.size();
  CpxVector flm(nem);
  bool findReal = true;
  for (int i = 1; i < nns; ++i)
  {
    const Vector &shape(mvz.namedshape(i));
    if (shape.size() != uint(nem))
      continue;

    const string &s(mvz.shapename(i));
    if (findReal)
    {
      if (s.size() >= 3 && s.compare(0, 3, "Re ") == 0)
      {
        findReal = false;
        for (int j = 0; j < nem; ++j)
          flm[j] = Complex(shape[j], 0.0);
      }
    }
    else
    {
      if (s.size() >= 3 && s.compare(0, 3, "Im ") == 0)
      {
        findReal = true;
        for (int j = 0; j < nem; ++j)
          flm[j] += Complex(0.0, shape[j]);

        uint km = appendFlutterMode(Complex(0.0, 1.0), flm);
        deforms[km].rename(strip(s.substr(2, s.size() - 2)));
      }
    }
  }
}

TriMeshPtr MxMesh::toTriMesh() const
{
  // extract nodes used by triangle sections
  Indices triNodes;
  size_t nf(0);
  for (uint i = 0; i < nsections(); ++i)
  {
    if (section(i).elementType() == Mx::Tri3)
    {
      nf += section(i).nelements();
      Indices nds;
      section(i).usedNodes(nds);
      if (triNodes.empty())
      {
        triNodes = nds;
      }
      else
      {
        size_t n = triNodes.size();
        triNodes.insert(triNodes.end(), nds.begin(), nds.end());
        std::inplace_merge(triNodes.begin(),
                           triNodes.begin() + n, triNodes.end());
      }
    }
  }

  // copy only required nodes
  const size_t np = triNodes.size();
  TriMeshPtr ptm = boost::make_shared<TriMesh>();
  for (size_t i = 0; i < np; ++i)
    ptm->addVertex(vtx[triNodes[i]]);

  // create trianglular elements, tagged with section index
  for (size_t i = 0; i < nsections(); ++i)
  {
    if (section(i).elementType() == Mx::Tri3)
    {
      uint vk[3];
      const size_t ne = section(i).nelements();
      for (size_t j = 0; j < ne; ++j)
      {
        const uint *v = section(i).element(j);
        for (int k = 0; k < 3; ++k)
          vk[k] = sorted_index(triNodes, v[k]);
        ptm->addFace(vk, int(i));
      }
      ptm->tagName(int(i), section(i).name());
    }
  }
  ptm->fixate();

  return ptm;
}

CgMeshPtr MxMesh::toCgMesh() const
{
  // triangle and line vertex indices
  Indices trix, lnx;
  for (uint i = 0; i < nsections(); ++i)
  {
    const Indices &nds(section(i).nodes());
    if (section(i).elementType() == Mx::Tri3)
    {
      trix.insert(trix.end(), nds.begin(), nds.end());
    }
    else if (section(i).elementType() == Mx::Line2)
    {
      lnx.insert(lnx.end(), nds.begin(), nds.end());
    }
  }

  Indices idx(trix);
  idx.insert(idx.end(), lnx.begin(), lnx.end());
  std::sort(idx.begin(), idx.end());
  idx.erase(std::unique(idx.begin(), idx.end()), idx.end());

  CgMeshPtr cgm = boost::make_shared<CgMesh>();
  const size_t nv = idx.size();
  const size_t ntv = trix.size();
  const size_t nlv = lnx.size();

  cgm->reserve(nv, ntv / 3, nlv / 2);
  for (size_t i = 0; i < nv; ++i)
    cgm->appendVertex(node(idx[i]));

  for (size_t i = 0; i < ntv; ++i)
    trix[i] = sorted_index(idx, trix[i]);
  for (size_t i = 0; i < nlv; ++i)
    lnx[i] = sorted_index(idx, lnx[i]);

  cgm->appendLines(lnx);
  return cgm;
}

void MxMesh::readAbaqus(const string &fname)
{
  clear();

  ifstream in(asPath(fname).c_str());
  string ln, lnlo;

  DVector<int> gid, eid;
  gid.reserve(8192);
  eid.reserve(8192);

  XmlElement xabq("Abaqus");

  getline(in, ln);
  lnlo = toLower(strip(ln));
  while (in)
  {
    if (lnlo.find("*node") != string::npos)
      ln = readAbaqusNodes(in, gid);
    else if (lnlo.find("*element") != string::npos)
      ln = readAbaqusElements(lnlo, in, eid);
    else if (lnlo.find("*elset") != string::npos)
      ln = readAbaqusSet(lnlo, eid, in);
    else if (lnlo.find("*end part") != string::npos)
      break;
    else if ((not lnlo.empty()) and lnlo[0] == '*')
      ln = readAbaqusKeyword(lnlo, in, xabq);
    else
      getline(in, ln);
    lnlo = toLower(strip(ln));
  }

  countElements();
  appendField("GID", gid);
  appendField("EID", eid);

  // map node indices in elements to GIDs
  typedef std::map<uint, uint> IndexMap;
  const int nn = gid.size();
  IndexMap gidmap;
  for (int i = 0; i < nn; ++i)
    gidmap[gid[i]] = i;

  const int nsec = nsections();
  for (int i = 0; i < nsec; ++i)
  {
    Indices idx = sections[i].nodes();
    const int nv = idx.size();
    for (int j = 0; j < nv; ++j)
    {
      IndexMap::const_iterator pos = gidmap.find(idx[j]);
      assert(pos != gidmap.end());
      idx[j] = pos->second;
    }
    sections[i].swapElements(sections[i].elementType(), idx);
  }

  annotate(xabq);
}

std::string MxMesh::readAbaqusNodes(std::istream &in, DVector<int> &gid)
{
  string ln;
  int id;
  Real x, y, z;
  char *tail;

  while (getline(in, ln))
  {
    const char *s = ln.c_str();
    id = genua_strtol(s, &tail, 10);
    if (tail == s)
      break;
    s = tail + 1; // skip comma
    x = genua_strtod(s, &tail);
    if (tail == s)
      break;
    s = tail + 1;
    y = genua_strtod(s, &tail);
    if (tail == s)
      break;
    s = tail + 1;
    z = genua_strtod(s, &tail);
    if (tail == s)
      break;

    gid.push_back(id);
    appendNode(Vct3(x, y, z));
  }

  return ln;
}

std::string MxMesh::readAbaqusElements(const std::string &header,
                                       istream &in, DVector<int> &eid)
{
  string ln;

  // determine element type
  string::size_type p1, p2;
  p1 = header.find_first_of("type");
  p2 = header.find_first_of(',');
  if (p1 == string::npos)
    return ln;
  p1 = header.find_first_of('=', p1);
  if (p1 == string::npos)
    return ln;
  ++p1;
  p2 = header.find_first_of(',', p1);
  if (p2 == string::npos)
    p2 = header.find_first_of(' ', p1);

  const int MAX_ELN(27);
  string ets = strip(header.substr(p1, p2 - p1));

  cout << "Abaqus element type: '" << ets << "'" << endl;

  Mx::ElementType et = Mx::Undefined;
  if ((ets.find("b2") != string::npos) or
      (ets.find("t3d2") != string::npos))
    et = Mx::Line2;
  else if ((ets.find("b3") != string::npos) or
           (ets.find("t3d3") != string::npos))
    et = Mx::Line3;
  else if (ets.find("s3") != string::npos)
    et = Mx::Tri3;
  else if (ets.find("stri6") != string::npos)
    et = Mx::Tri6;
  else if (ets.find("s4") != string::npos)
    et = Mx::Quad4;
  else if (ets.find("s8") != string::npos)
    et = Mx::Quad8;
  else if (ets.find("s9") != string::npos)
    et = Mx::Quad9;
  else
    cerr << "Unknown Abaqus element type: '" << ets << "'" << endl;

  if (et == Mx::Undefined)
    return ln;

  const int nv = MxMeshSection::nElementNodes(et);
  int id;
  Indices vix;
  vix.reserve(8192);
  char *tail;
  while (getline(in, ln))
  {
    const char *s = ln.c_str();
    id = genua_strtol(s, &tail, 10);
    if (tail == s)
      break;
    s = tail + 1; // skip comma

    int vtmp[MAX_ELN], k;
    for (k = 0; k < nv; ++k)
    {
      vtmp[k] = genua_strtol(s, &tail, 10);
      if (tail == s)
        break;
      s = tail + 1;
    }
    if (k != nv)
      break;

    eid.push_back(id);
    vix.insert(vix.end(), vtmp, vtmp + nv);
  }

  uint isec = appendSection(et, vix);

  XmlElement note("Abaqus");
  XmlElement net("Element");
  net["type"] = ets;
  note.append(net);

  section(isec).annotate(note);

  return ln;
}

string MxMesh::readAbaqusSet(const string &header,
                             const DVector<int> &eid, istream &in)
{
  std::map<uint, uint> eidmap;
  const int ne = eid.size();
  for (int i = 0; i < ne; ++i)
    eidmap[eid[i]] = i;

  string ln, setname;
  const char *s = header.c_str();
  const char *p = strchr(s, '=');
  if (p == 0)
    return ln;
  ++p;

  const char *q = strchr(p, ',');
  if (q == 0)
    q = strchr(p, ' ');
  if (q == 0)
    setname.assign(p);
  else
    setname.assign(p, q);

  bool generateSet = (strstr(p, "generate") != 0);

  Indices idx;
  idx.reserve(8192);
  uint id;
  char *tail;

  while (getline(in, ln))
  {
    s = ln.c_str();
    if (strchr(s, '*') != 0)
      break;

    if (generateSet)
    {
      uint first = genua_strtol(s, &tail, 10);
      if (tail == s)
        break;
      s = tail + 1;
      uint last = genua_strtol(s, &tail, 10);
      if (tail == s)
        break;
      s = tail + 1;
      uint incr = genua_strtol(s, &tail, 10);
      if (tail == s)
        break;
      for (id = first; id <= last; id += incr)
        idx.push_back(id);
    }
    else
    {
      id = genua_strtol(s, &tail, 10);
      while (tail != s and *tail != 0)
      {
        idx.push_back(id);
        s = tail + 1;
        id = genua_strtol(s, &tail, 10);
      }
      idx.push_back(id);
    }
  }

  // translate indices
  const int nx = idx.size();
  Indices mix;
  mix.reserve(nx);
  std::map<uint, uint>::const_iterator pos;
  for (int i = 0; i < nx; ++i)
  {
    pos = eidmap.find(idx[i]);
    if (pos != eidmap.end())
      mix.push_back(pos->second);
  }
  sort_unique(mix);

  MxMeshBoco bc(Mx::BcElementSet);
  bc.appendElements(mix.begin(), mix.end());
  bc.rename(setname);
  appendBoco(bc);

  return ln;
}

string MxMesh::readAbaqusKeyword(const string &header, istream &in,
                                 XmlElement &xabq)
{
  string ln;
  if (header.size() < 2)
    return ln;

  // skip comments
  if (header[1] == '*')
    return ln;

  // identify keyword
  const char *s = header.c_str() + 1;
  const char *p = strchr(s, ',');
  string key;
  if (p == 0)
    key.assign(s);
  else
    key.assign(s, p);
  key = strip(key);

  XmlElement xkey("AbaqusSection");
  xkey["AbaqusKeyword"] = key;

  // extract attributes
  string ak, av;
  while (p != 0)
  {
    s = p + 1;
    p = strchr(s, ',');
    const char *t = strchr(s, '=');
    av.clear();
    ak.clear();
    if (t != 0 and t < p)
    {
      ak.assign(s, t);
      if (p != 0)
        av.assign(t + 1, p);
      else
        av.assign(t + 1);
    }
    else if (p != 0)
    {
      ak.assign(s, p);
    }
    else
    {
      ak.assign(s);
    }
    ak = strip(ak);
    av = strip(av);
    xkey[ak] = av;
  }

  stringstream ss;
  while (getline(in, ln))
  {
    string::size_type p1 = ln.find_first_not_of(" \t\n\r");
    if (p1 == string::npos)
      continue;
    if (ln[p1] == '*')
      break;
    ss << ln << endl;
  }
  xkey.text(ss.str());

  xabq.append(xkey);
  return ln;
}

void MxMesh::writeAbaqus(const string &fname) const
{
  ofstream os(asPath(fname).c_str());

  // look for fields which identify node IDs
  const int nn = vtx.size();
  const int ne = nelements();
  Indices gid(nn), eid(ne);
  uint fgid = findField("GID");
  uint feid = findField("EID");

  if (fgid != NotFound)
  {
    const MxMeshField &fg(field(fgid));
    if ((not fg.nodal()) or (fg.realField()))
    {
      fgid = NotFound;
      for (int i = 0; i < nn; ++i)
        gid[i] = i + 1;
    }
    else
    {
      for (int i = 0; i < nn; ++i)
        fg.scalar(i, gid[i]);
    }
  }
  else
  {
    for (int i = 0; i < nn; ++i)
      gid[i] = i + 1;
  }

  if (feid != NotFound)
  {
    const MxMeshField &fg(field(feid));
    if ((fg.size() != uint(ne)) or (fg.realField()))
    {
      feid = NotFound;
      for (int i = 0; i < ne; ++i)
        eid[i] = i + 1;
    }
    else
    {
      for (int i = 0; i < ne; ++i)
        fg.scalar(i, eid[i]);
    }
  }
  else
  {
    for (int i = 0; i < ne; ++i)
      eid[i] = i + 1;
  }

  // node section
  os << "*Node" << endl;
  os.precision(12);
  for (int i = 0; i < nn; ++i)
  {
    os << gid[i] << ", " << vtx[i][0] << ", " << vtx[i][1] << ", "
       << vtx[i][2] << endl;
  }

  for (uint i = 0; i < nsections(); ++i)
    section(i).writeAbaqus(gid, eid, os);
  for (uint i = 0; i < nbocos(); ++i)
    boco(i).writeAbaqus(gid, eid, os);

  // check for any additional keywords to be written
  const XmlElement *xabq = xnote.findNode("Abaqus");
  if (xabq != 0)
  {
    XmlElement::const_iterator itr, last = xabq->end();
    for (itr = xabq->begin(); itr != last; ++itr)
    {
      os << '*' << itr->attribute("AbaqusKeyword");
      XmlElement::attr_iterator ita, alast = itr->attrEnd();
      for (ita = itr->attrBegin(); ita != alast; ++ita)
      {
        if (ita->first == "AbaqusKeyword")
          continue;
        os << ", " << ita->first;
        if (not ita->second.empty())
          os << "=" << ita->second;
      }
      os << endl;
      os << itr->text();
    }
  }
}

void MxMesh::writeNastran(const std::string &fname,
                          size_t nodeOffset, size_t eidOffset) const
{
  ofstream os(asPath(fname));
  this->writeNastran(os, nodeOffset, eidOffset);
}

void MxMesh::writeNastran(std::ostream &os,
                          size_t nodeOffset, size_t eidOffset) const
{
  const size_t nv = nnodes();
  os << "$ All grid points " << endl;
  for (size_t i = 0; i < nv; ++i)
  {
    const Vct3 &p(node(i));
    os << "GRID, " << i + 1 + nodeOffset << ", 0, " << nstr(p[0])
       << ", " << nstr(p[1]) << ", " << nstr(p[2]) << ", " << endl;
  }

  // check if there is a field named 'PID'; if so, use it to
  // assign element properties from field
  std::vector<int> pid;
  uint ifpid = findField("PID");
  if (ifpid != NotFound)
  {
    pid.resize(field(ifpid).size());
    field(ifpid).fetch(pid);
  }

  std::vector<int> mcid;
  uint ifmcid = findField("MCID");
  if (ifmcid != NotFound)
  {
    mcid.resize(field(ifmcid).size());
    field(ifmcid).fetch(mcid);
  }

  uint eix(1), epid, emcid;
  for (uint isec = 0; isec < nsections(); ++isec)
  {
    const MxMeshSection &sec(section(isec));
    const int ne = sec.nelements();
    epid = isec + 1;
    emcid = 0;
    if (sec.elementType() == Mx::Tri3)
    {
      for (int i = 0; i < ne; ++i)
      {
        const uint *vi = sec.element(i);
        if (not pid.empty())
          epid = pid[sec.indexOffset() + i];
        if (not mcid.empty())
          emcid = mcid[sec.indexOffset() + i];
        if (epid != 0)
        {
          os << "CTRIA3, " << eix + eidOffset << ',' << epid;
          for (int k = 0; k < 3; ++k)
            os << ',' << vi[k] + 1 + nodeOffset;
          os << ", " << emcid << endl;
        }
        ++eix;
      }
    }
    else if (sec.elementType() == Mx::Tri6)
    {
      for (int i = 0; i < ne; ++i)
      {
        const uint *vi = sec.element(i);
        if (not pid.empty())
          epid = pid[sec.indexOffset() + i];
        if (not mcid.empty())
          emcid = mcid[sec.indexOffset() + i];
        if (epid != 0)
        {
          os << "CTRIA6, " << eix + eidOffset << ',' << epid;
          for (int k = 0; k < 6; ++k)
            os << ',' << vi[k] + 1 + nodeOffset;
          os << endl;
          if (emcid != 0)
            os << ", " << emcid << endl;
        }
        ++eix;
      }
    }
    else if (sec.elementType() == Mx::Quad4)
    {
      for (int i = 0; i < ne; ++i)
      {
        if (not pid.empty())
          epid = pid[sec.indexOffset() + i];
        if (not mcid.empty())
          emcid = mcid[sec.indexOffset() + i];
        const uint *vi = sec.element(i);
        if (epid != 0)
        {
          os << "CQUAD4, " << eix + eidOffset << ',' << epid;
          for (int k = 0; k < 4; ++k)
            os << ',' << vi[k] + 1 + nodeOffset;
          os << ", " << emcid << endl;
        }
        ++eix;
      }
    }
    else if (sec.elementType() == Mx::Quad8)
    {
      for (int i = 0; i < ne; ++i)
      {
        if (not pid.empty())
          epid = pid[sec.indexOffset() + i];
        if (not mcid.empty())
          emcid = mcid[sec.indexOffset() + i];
        const uint *vi = sec.element(i);
        if (epid != 0)
        {
          os << "CQUAD8, " << eix + eidOffset << ',' << epid;
          for (int k = 0; k < 6; ++k)
            os << ',' << vi[k] + 1 + nodeOffset;
          for (int k = 0; k < 2; ++k)
            os << ',' << vi[6 + k] + 1 + nodeOffset;
          os << ",,,," << emcid << endl;
        }
        ++eix;
      }
    }
    else if (sec.elementType() == Mx::Line2)
    {

      // beam elements require orientation vectors
      const XmlElement &xn = sec.note();
      XmlElement::const_iterator itr = xn.findChild("BeamOrientation");
      if (itr == xn.end())
      {
        dbprint("Beam orientation not present in mesh section, skipping.");
        continue;
      }

      PointList<3> ori(ne);
      assert(Int(itr->attribute("count")) >= ne);
      itr->fetch(3 * ne * sizeof(Real), ori.pointer());

      for (int i = 0; i < ne; ++i)
      {
        if (not pid.empty())
          epid = pid[sec.indexOffset() + i];
        if (not mcid.empty())
          emcid = mcid[sec.indexOffset() + i];
        const uint *vi = sec.element(i);
        if (epid != 0)
        {
          os << "CBEAM, " << eix + eidOffset << ',' << epid;
          for (int k = 0; k < 2; ++k)
            os << ',' << vi[k] + 1 + nodeOffset;
          for (int k = 0; k < 3; ++k)
            os << ',' << nstr(ori[i][k]);
          os << endl;
        }
        ++eix;
      }
    }
  }
}

XmlElement MxMesh::toVTK() const
{
  XmlElement xv("VTKFile");
  xv["type"] = "UnstructuredGrid";

  XmlElement xu("UnstructuredGrid");
  for (uint i = 0; i < sections.size(); ++i)
    xu.append(sections[i].toVTK());
  xv.append(xu);

  return xv;
}

BinFileNodePtr MxMesh::gbfNode(bool share) const
{
  BinFileNodePtr np = boost::make_shared<BinFileNode>("MxMesh");

  BinFileNodePtr vn = boost::make_shared<BinFileNode>("MxMeshVertices");
  vn->assign(3 * vtx.size(), vtx.pointer(), share);
  np->append(vn);

  {
    const int ns = nsections();
    for (int i = 0; i < ns; ++i)
      np->append(sections[i].gbfNode(share));
  }

  {
    const int ns = nbocos();
    for (int i = 0; i < ns; ++i)
      np->append(bocos[i].gbfNode(share));
  }

  {
    const int ns = nfields();
    for (int i = 0; i < ns; ++i)
      np->append(fields[i].gbfNode(share));
  }

  if (soltree)
    np->append(soltree->toXml(true).toGbf(share));

  return np;
}

void MxMesh::fromGbf(const BinFileNodePtr &np, bool digestNode)
{
  if (np->name() != "MxMesh")
    throw Error("Incompatible binary file representation for MxMesh.");

  np->digest(digestNode);

  clear();
  const int nchild = np->nchildren();
  for (int i = 0; i < nchild; ++i)
  {
    BinFileNodePtr cn = np->childNode(i);
    if (cn->name() == "MxMeshVertices")
    {
      const int nv = cn->blockElements() / 3;
      vtx.resize(nv);
      memcpy(vtx.pointer(), cn->blockPointer(), 3 * nv * sizeof(Real));
      cn->digest(digestNode);
    }
    else if (cn->name() == "MxMeshSection")
    {
      MxMeshSection sec(this, Mx::Undefined);
      sections.push_back(sec);
      sections.back().fromGbf(cn, digestNode);
    }
    else if (cn->name() == "MxMeshBoco")
    {
      MxMeshBoco bc;
      bocos.push_back(bc);
      bocos.back().fromGbf(cn, digestNode);
    }
    else if (cn->name() == "MxMeshField")
    {
      MxMeshField fd(this);
      fields.push_back(fd);
      fields.back().fromGbf(cn, digestNode);
    }
  }
  countElements();
}

XmlElement MxMesh::toXml(bool share) const
{
  XmlElement xe("MxMesh");

  // make sure that annotations come first
  if (not xnote.name().empty())
    xe.append(xnote);

  if (soltree)
    xe.append(soltree->toXml(share));

  XmlElement xv("MxMeshVertices");
  xv["count"] = str(vtx.size());
  if (not vtx.empty())
    xv.asBinary(3 * vtx.size(), vtx.pointer(), share);
  xe.append(std::move(xv));

  for (uint i = 0; i < sections.size(); ++i)
    xe.append(sections[i].toXml(share));
  for (uint i = 0; i < bocos.size(); ++i)
    xe.append(bocos[i].toXml(share));
  for (uint i = 0; i < fields.size(); ++i)
    xe.append(fields[i].toXml(share));
  for (uint i = 0; i < deforms.size(); ++i)
    xe.append(deforms[i].toXml(share));

  return xe;
}

void MxMesh::fromXml(const XmlElement &xe)
{
  if (xe.name() != "MxMesh")
    throw Error("Incompatible XML representation for MxMesh.");

  clear();

  XmlElement::const_iterator itr, last;
  last = xe.end();
  for (itr = xe.begin(); itr != last; ++itr)
  {
    string s = itr->name();
    if (s == "MxMeshVertices")
    {
      size_t n = Int(itr->attribute("count"));
      vtx.resize(n);
      if (n > 0)
        itr->fetch(3 * n, vtx.pointer());
    }
    else if (s == "MxMeshSection")
    {
      sections.push_back(MxMeshSection(this));
      sections.back().fromXml(*itr);
    }
    else if (s == "MxMeshBoco")
    {
      bocos.push_back(MxMeshBoco());
      bocos.back().fromXml(*itr);
    }
    else if (s == "MxMeshField")
    {
      fields.push_back(MxMeshField(this));
      fields.back().fromXml(*itr);
    }
    else if (s == "MxMeshDeform")
    {
      deforms.push_back(MxMeshDeform(this));
      deforms.back().fromXml(*itr);
    }
    else if (s == "MxMeshNote" or s == "MxNote")
    {
      note(*itr);
      MxAnnotated::xnote.detach();
    }
    else if (s == "MxSolutionTree")
    {
      soltree.reset(new MxSolutionTree);
      soltree->fromXml(*itr);
    }
  }
  countElements();
}

void MxMesh::writeZml(const std::string &fname, int compression) const
{
  toXml(true).zwrite(fname, compression);
}

void MxMesh::readZml(const std::string &fname)
{
  XmlElement xe;
  xe.read(fname);
  fromXml(xe);
}

void MxMesh::writeLegacyVtk(const string &fname) const
{
  ofstream os(asPath(fname).c_str());
  os << "# vtk DataFile Version 2.0" << endl;
  os << "File written by libgenua, http://www.larosterna.com" << endl;
  os << "ASCII" << endl;
  os << "DATASET UNSTRUCTURED_GRID" << endl;

  const size_t nn = vtx.size();
  os << "POINTS " << nn << " float" << endl;
  os.precision(15);
  os << std::scientific;
  for (size_t i = 0; i < nn; ++i)
    os << vtx[i][0] << ' ' << vtx[i][1] << ' ' << vtx[i][2] << endl;

  // count number of element vertex indices used
  int nev = 0;
  int nel = 0;
  for (uint i = 0; i < nsections(); ++i)
  {
    int ecode = Mx::elementType2Vtk(section(i).elementType());
    if (ecode == 0)
      continue;
    uint ne = section(i).nelements();
    nel += ne;
    nev += ne * section(i).nElementNodes();
  }

  os << "CELLS " << nel << ' ' << nev + nel << endl;
  Indices elmTyp(nel);
  int offset = 0;
  for (uint i = 0; i < nsections(); ++i)
  {
    int ecode = Mx::elementType2Vtk(section(i).elementType());
    if (ecode == 0)
      continue;
    int ne = section(i).nelements();
    int nv = section(i).nElementNodes();
    for (int j = 0; j < ne; ++j)
    {
      elmTyp[offset + j] = ecode;
      const uint *vi = section(i).element(j);
      os << nv;
      for (int k = 0; k < nv; ++k)
        os << ' ' << vi[k];
      os << endl;
    }
    offset += ne;
  }

  os << "CELL_TYPES " << nel << endl;
  for (int i = 0; i < nel; ++i)
    os << elmTyp[i] << endl;

  os << "POINT_DATA " << nn << endl;
  for (uint i = 0; i < nfields(); ++i)
  {
    const MxMeshField &f(field(i));
    if (not f.nodal())
      continue;
    if (not f.realField())
      continue;
    const int ndim = f.ndimension();
    if (ndim == 1)
    {
      os << "SCALARS " << f.name() << " float 1" << endl;
      for (size_t j = 0; j < nn; ++j)
      {
        double x;
        f.scalar(j, x);
        os << x << endl;
      }
    }
    else if (ndim == 3)
    {
      os << "VECTORS " << f.name() << " float" << endl;
      for (size_t j = 0; j < nn; ++j)
      {
        Vct3 x;
        f.value(j, x);
        os << x[0] << ' ' << x[1] << ' ' << x[2] << endl;
      }
    }
  }
}

void MxMesh::readLegacyVtk(const string &fname)
{
  clear();

  ifstream in(asPath(fname).c_str());
  string line;

  Indices evlist, ctlist;
  const char *s(0), *pos(0);
  char *tail(0);
  uint npoints(NotFound), ncell(NotFound), nclsize(NotFound), nct(NotFound);
  uint rpoints(0);

  while (std::getline(in, line))
  {

    s = line.c_str();
    if (npoints == NotFound)
    {
      pos = strstr(s, "POINTS");
      if (pos != 0)
      {
        npoints = genua_strtol(pos + strlen("POINTS"), &tail, 10);
        dbprint("VTK import: Expecting", npoints, "nodes.");
        continue;
      }
    }
    else if (rpoints < npoints)
    {

      Vct3 p;

      // all points can be on one line, so just loop until line exhausted
      do
      {

        p[0] = genua_strtod(s, &tail);
        if (tail == s)
          break;
        s = tail;
        p[1] = genua_strtod(s, &tail);
        if (tail == s)
          break;
        s = tail;
        p[2] = genua_strtod(s, &tail);
        if (tail == s)
          break;
        appendNode(p);
        ++rpoints;

        s = tail;
        while (isblank(*s) and *s != 0)
          ++s;
        if (*s == 0)
          break;

      } while (rpoints < npoints);
      if (rpoints == npoints)
        dbprint("Found all nodes: ", rpoints);
      continue;
    }

    if (ncell == NotFound)
    {
      pos = strstr(s, "CELLS ");
      if (pos != 0)
      {
        pos += strlen("CELLS ");
        ncell = genua_strtol(pos, &tail, 10);
        assert(tail != pos);
        pos = tail;
        nclsize = genua_strtol(pos, &tail, 10);
        assert(tail != pos);
        ctlist.reserve(ncell);
        evlist.reserve(nclsize);
        dbprint("VTK import: Expecting", ncell, "cells, indices = ", nclsize);
        continue;
      }
    }
    else if (evlist.size() < nclsize)
    {
      uint v = genua_strtol(s, &tail, 10);
      while (tail != s)
      {
        evlist.push_back(v);
        s = tail;
        v = genua_strtol(s, &tail, 10);
      }
      if (evlist.size() == nclsize)
        dbprint("Found cells list:", evlist.size());
      continue;
    }

    if (nct == NotFound)
    {
      pos = strstr(s, "CELL_TYPES");
      if (pos != 0)
      {
        nct = genua_strtol(pos + strlen("CELL_TYPES"), &tail, 10);
        dbprint("VTK import: Expecting", nct, "cell type flags.");
        continue;
      }
    }
    else if (ctlist.size() < nct)
    {
      uint v = genua_strtol(s, &tail, 10);
      while (tail != s)
      {
        ctlist.push_back(v);
        s = tail;
        v = genua_strtol(s, &tail, 10);
      }
      if (ctlist.size() == nct)
        dbprint("All cell type flags identified.");
      continue;
    }

    // extract field data after element construction
    if (strstr(s, "POINT_DATA") != 0)
      break;
  }

  if (ctlist.size() != ncell)
    throw Error("VTK reader: Number of cells does not match number "
                "of cell type tags.");

  // build mesh from vertex indices
  ElmCollector ecollect((int)Mx::NElmTypes);
  uint offset = 0;
  for (uint i = 0; i < ncell; ++i)
  {
    const uint *pvi = &evlist[offset];
    uint nve = pvi[0];
    offset += nve + 1;
    Mx::ElementType etype = Mx::vtk2ElementType(ctlist[i]);
    if (etype == Mx::Undefined)
      continue;
    Indices &vix(ecollect[(int)etype]);
    vix.insert(vix.end(), pvi + 1, pvi + 1 + nve);
  }

  for (uint it = 0; it < ecollect.size(); ++it)
  {
    const Indices &vix(ecollect[it]);
    if (vix.empty())
      continue;
    appendSection(Mx::ElementType(it), vix);
  }
  dbprint("Created", nsections(), "mesh sections.");

  // look for nodal fields
  string fieldName;
  uint nfv(0), nfdim(NotFound);
  Vector sfld;
  PointList<3> vfld(nnodes());
  size_t spos = 0;

  while (std::getline(in, line))
  {

    // extract scalar fields
    s = line.c_str();
    if (nfdim == NotFound)
    {
      pos = strstr(s, "SCALARS ");
      if (pos != 0)
      {
        s = pos + strlen("SCALARS ");
        pos = strstr(pos, "float");
        if (pos == 0)
          continue;
        fieldName.assign(s, pos - s);
        string::size_type p1 = fieldName.find_first_not_of('\"');
        string::size_type p2 = fieldName.find_last_not_of('\"');
        if (p1 != 0 and p2 - p1 > 2)
          fieldName = fieldName.substr(p1, p2 - p1 - 1);
        s = pos + strlen("float");
        nfdim = genua_strtol(pos, &tail, 10);
        if (pos == tail)
          nfdim = 1;
        assert(nfdim < 5);
        nfv = 0;
        spos = 0;
        sfld.resize(nnodes() * nfdim);
        dbprint("Scanning field", fieldName, "dim", nfdim);
        continue;
      }
    }
    else if (nfv < nnodes())
    {

      Real v = genua_strtod(s, &tail);
      while ((s != tail) and (spos < sfld.size()))
      {
        sfld[spos] = v;
        ++spos;
        s = tail;
        v = genua_strtod(s, &tail);
      }
      if (spos == sfld.size())
      {
        MxMeshField kfield(this, true);
        kfield.copyReal(fieldName, nfdim, sfld.pointer());
        appendField(kfield);
        nfdim = NotFound; // look for next field
      }
      continue;
    }

    // extract vector fields
    if (nfdim == NotFound)
    {
      pos = strstr(s, "VECTORS ");
      if (pos != 0)
      {
        s = pos + strlen("VECTORS ");
        pos = strstr(pos, "float");
        if (pos == 0)
          continue;
        fieldName.assign(s, pos - s);
        nfdim = 3;
        nfv = 0;
        dbprint("Scanning vector field", fieldName);
        continue;
      }
    }
    else if (nfv < nnodes())
    {
      for (uint k = 0; k < 3; ++k)
      {
        vfld[nfv][k] = genua_strtod(s, &tail);
        assert(s != tail);
        s = tail;
      }
      ++nfv;
      if (nfv == nnodes())
      {
        MxMeshField kfield(this, true);
        kfield.copyReal(fieldName, 3, sfld.pointer());
        appendField(kfield);
        nfdim = NotFound; // look for next field
      }
      continue;
    }
  }
}

// --------- helper functions for aerelplot import

static inline void fetch_five(const string &line, Vector &val)
{
  stringstream mode_p1(line);
  for (int k = 0; k < 5; ++k)
  {
    double u;
    mode_p1 >> u;
    for (int uu = 0; uu < 4; ++uu)
      val.push_back(u);
  }
}

static inline bool is_this_empty(const string &s)
{
  if (s.empty())
    return true;
  for (size_t i = 0; i < s.size(); ++i)
  {
    if (!isspace(s[i]))
    {
      return false;
    }
  }
  return true;
}

static inline bool is_this_mode(const string &s)
{
  if (s.empty())
    return false;
  if (s.find("Mode") != string::npos)
    return true;
  return false;
}

static inline std::string keyword_line(const string &prefix, int n)
{
  assert(n < 1000);
  std::stringstream ss;
  ss << prefix;
  if (n < 100)
    ss << ' ';
  if (n < 10)
    ss << ' ';
  ss << n;
  return ss.str();
}

void MxMesh::readAerel(const std::string &fname)
{
  MxSolutionTreePtr psroot = boost::make_shared<MxSolutionTree>("Subcases");
  MxSolutionTreePtr pssubcase, pseigenmodes;
  pseigenmodes = boost::make_shared<MxSolutionTree>("DeformationModes");
  psroot->append(pseigenmodes);

  // vertices of quad element
  Vct3 pts[4];

  // all quad indices
  Indices quads;
  Vector rcp_values, icp_values;
  std::vector<PointList<3>> k_modes;
  std::vector<Vector> k_rcp, k_icp;

  double mnm(0); // mode number for mode (displacement)
  double Sref(1.0), Lref(1.0), Mach(0.1);
  int nfreq(0);
  int npanels(0), nmodes(0), modenum(0);
  PointList<3> mode;

  // read AEREL plot file line by line
  std::string line;
  ifstream in(fname.c_str());
  if (!in)
    throw("AEREL plot file could not be opened: " + fname);

  while (getline(in, line))
  {

    // skip to number of panels
    if (line.find("Number of panels, and number of modes") != string::npos)
    {
      getline(in, line);
      stringstream ss(line);
      ss >> npanels >> nmodes;
      assert(npanels > 0);
    }

    // read points for one element
    if (line.find("Element") != string::npos)
    {
      for (int k = 0; k < 3; ++k)
      {
        getline(in, line);
        stringstream coord(line);
        coord >> pts[0][k] >> pts[1][k] >> pts[2][k] >> pts[3][k];
      }
      for (int k = 0; k < 4; ++k)
        quads.push_back(appendNode(pts[k]));
    }

    // extract reference values
    if (line.find("Sref, Lref") != string::npos)
    {
      getline(in, line);
      stringstream ref(line);
      ref >> nfreq >> Sref >> Lref >> Mach;
      cout << "Sref = " << Sref << " Lref = " << Lref << endl;
    }

    // read modeshapes ...
    Vector u_points;
    for (int ii = 0; ii < npanels; ++ii)
    {
      string keyword = keyword_line("on panel", ii + 1);
      if (line.find(keyword) != string::npos)
      {
        ++mnm;
        getline(in, line);
        while (!is_this_mode(line) and !is_this_empty(line))
        {
          fetch_five(line, u_points);
          getline(in, line);
        } // (!is_this_empty(line))
      }
    }

    if (!u_points.empty())
    {
      ++modenum;
      int ndz = u_points.size();
      mode.resize(ndz);
      for (int nn = 0; nn < ndz; ++nn)
        mode[nn][2] = u_points[nn];
      k_modes.push_back(mode);
    } // !u_points.empty()

    // Real and imaginary parts for panels follow eachother in the input file
    double machnr, freq;
    int panelnr, modenr;
    pssubcase = boost::make_shared<MxSolutionTree>("Subcase");

    // Panels
    if (line.find("Real DCP") != string::npos)
    {
      getline(in, line);
      stringstream rcp_info(line);
      rcp_info >> panelnr >> modenr >> machnr >> freq;

      // aerel prints k/Lref
      freq *= Lref;
      if (panelnr < 2)
      {
        rcp_values.clear();
        icp_values.clear();
      }
      getline(in, line);

      // until an empty line is reached:
      while (!is_this_empty(line))
      {
        fetch_five(line, rcp_values);
        getline(in, line);
      } // (!is_this_empty(line))

      if (panelnr > npanels - 1)
        k_rcp.push_back(rcp_values);
    } // (line.find("Real DCP") != string::npos)

    if (line.find("Imag DCP") != string::npos)
    {
      getline(in, line);
      getline(in, line);
      while (!is_this_empty(line))
      {
        fetch_five(line, icp_values);
        getline(in, line);
      } // (!is_this_empty(line))

      if (panelnr > npanels - 1)
        k_icp.push_back(icp_values);
      if ((panelnr > npanels - 1) and (modenr > nmodes - 1))
      {
        assert(pssubcase != nullptr);

        pssubcase->rename("Reduced freq. " + str(0.01 * std::round(freq * 100.0)));
        pssubcase->attribute("ReducedFrequency", str(freq));
        pssubcase->attribute("MachNumber", str(machnr));
        pssubcase->attribute("ModeNr", str(modenr));
        // cout << "Case named: " << pssubcase->name() << endl;

        psroot->append(pssubcase);
        for (int ii = 0; ii < nmodes; ++ii)
        {
          std::stringstream ss;
          ss << "Mode " << ii + 1 << " k " << 0.01 * std::round(freq * 100.0);
          string s = ss.str();

          // AEREL stores DCP fields scaled by Lref
          uint ire = appendField("ReDCp " + s, k_rcp[ii] / Lref);
          field(ire).valueClass(MxMeshField::ValueClass::ReDCp);
          pssubcase->appendField(ire);
          uint iim = appendField("ImDCp " + s, k_icp[ii] / Lref);
          field(iim).valueClass(MxMeshField::ValueClass::ImDCp);
          pssubcase->appendField(iim);
        }
        k_icp.clear();
        k_rcp.clear();
      }

    } // (line.find("Imag DCP") != string::npos)
  } // (getline(in, line))

  // gathered all elements; create a mesh section
  uint isec = appendSection(Mx::Quad4, quads);
  section(isec).rename("AerelElements");

  // deformation modes
  if (k_modes.size() != size_t(nmodes))
    throw Error("Corrupt file: Expected " + str(nmodes) +
                " modes, found " + str(k_modes.size()));

  for (int ii = 0; ii < nmodes; ++ii)
  {
    uint imodes = appendField("Mode " + str(ii + 1), k_modes[ii]);
    field(imodes).valueClass(MxMeshField::ValueClass::Eigenmode);
    field(imodes).attribute("ModeNr", str(ii + 1));
    pseigenmodes->appendField(imodes);
  }

  // attach solution tree
  solutionTree(psroot);
}

void MxMesh::writeSU2(const string &fname) const
{
  ofstream os(asPath(fname).c_str());

  // publicity!
  os << "% Mesh for Stanford University Unstructured (SU2)" << endl;
  os << "% mesh written by libgenua, http://www.larosterna.com" << endl;
  os << "% nodes: " << nnodes() << " elements: " << nelements() << endl;

  // dimensions, always 3
  os << "NDIME=3" << endl;

  // count volume elements
  uint nve = 0;
  for (uint i = 0; i < nsections(); ++i)
  {
    const MxMeshSection &sec(section(i));
    nve += sec.volumeElements() ? sec.nelements() : 0;
  }
  os << "NELEM=" << nve << endl;

  // write volume elements
  for (uint i = 0; i < nsections(); ++i)
  {
    const MxMeshSection &sec(section(i));
    if (sec.volumeElements())
      sec.writeSU2(os);
  }

  // write nodes
  const int nn = vtx.size();
  os << "NPOIN=" << nn << endl;
  os.precision(15);
  os << std::scientific;
  for (int i = 0; i < nn; ++i)
    os << vtx[i][0] << ' ' << vtx[i][1] << ' ' << vtx[i][2] << ' ' << i << endl;

  // write boundaries
  Indices elix;
  const int nbc = nbocos();
  os << "NMARK=" << nbc << endl;
  for (int ibc = 0; ibc != nbc; ++ibc)
  {
    const MxMeshBoco &bc(boco(ibc));
    os << "MARKER_TAG=" << bc.name() << endl;
    bc.elements(elix);
    const int ne = elix.size();
    os << "MARKER_ELEMS=" << ne << endl;
    for (int i = 0; i < ne; ++i)
    {
      uint nv, isec;
      const uint *vi = globalElement(elix[i], nv, isec);
      os << Mx::elementType2Vtk(section(isec).elementType());
      for (uint k = 0; k < nv; ++k)
        os << ' ' << vi[k];
      os << endl;
    }
  }
}

void MxMesh::readSU2(const std::string &fname)
{
  clear();
  ifstream in(asPath(fname).c_str());

  // array dimensions from file
  uint ndime(NotFound), nelem(NotFound), npoin(NotFound), nmark(NotFound);

  // number of marker elements
  uint nme(NotFound);

  // number of entries found
  uint relem(0), rpoin(0), rmark(0);

  // marker tags
  StringArray markTags;

  // one array of ElmID for each marker
  std::vector<MarkerID> markerID;

  // collect volume elements first
  ElmCollector ecollect;
  ecollect.resize(Mx::NElmTypes);

  string line, bcName;
  char *tail(0);
  while (getline(in, line))
  {

    if (ndime == NotFound)
    {
      ndime = su2_strkey(line, "NDIME=");
      if (ndime != NotFound)
      {
        continue;
        dbprint("NDIME = ", ndime);
      }
    }

    if (nelem == NotFound)
    {
      nelem = su2_strkey(line, "NELEM=");
      if (nelem != NotFound)
      {
        continue;
        dbprint("NELEM = ", nelem);
      }
    }
    else if (relem < nelem)
    {
      const char *s = line.c_str();
      uint code = genua_strtol(s, &tail, 10);
      if (tail == s)
        continue;
      Mx::ElementType etype = Mx::vtk2ElementType(code);
      if (etype == Mx::Undefined)
        continue;
      Indices &vix(ecollect[(int)etype]);
      int nev = MxMeshSection::nElementNodes(etype);
      s = tail;
      for (int k = 0; k < nev; ++k)
      {
        uint vik = genua_strtod(s, &tail);
        assert(tail != s);
        vix.push_back(vik);
      }
      ++relem;
      if (relem == nelem)
        dbprint(relem, " domain elements identified.");
      continue;
    }

    if (npoin == NotFound)
    {
      npoin = su2_strkey(line, "NPOIN=");
      if (npoin != NotFound)
        dbprint("SU2: Looking for ", npoin, " points.");
      continue;
    }
    else if (rpoin < npoin)
    {
      Vct3 p;
      const char *s = line.c_str();
      if (ndime == 2)
      {
        p[0] = genua_strtod(s, &tail);
        if (tail == s)
          continue;
        s = tail;
        p[1] = genua_strtod(s, &tail);
        if (tail == s)
          continue;
        appendNode(p);
        ++rpoin;
      }
      else
      {
        p[0] = genua_strtod(s, &tail);
        if (tail == s)
          continue;
        s = tail;
        p[1] = genua_strtod(s, &tail);
        if (tail == s)
          continue;
        s = tail;
        p[2] = genua_strtod(s, &tail);
        if (tail == s)
          continue;
        appendNode(p);
        ++rpoin;
      }
      if (rpoin == npoin)
        dbprint(npoin, " points identified.");
    }

    if (nmark == NotFound)
    {
      nmark = su2_strkey(line, "NMARK=");
      if (nmark != NotFound)
      {
        markerID.resize(nmark);
        markTags.resize(nmark);
        dbprint("Looking for ", nmark, "markers.");
      }
      continue;
    }
    else if (rmark < nmark)
    {

      // end up here when looking for next marker
      if (bcName.empty())
      {
        const char *pos = strstr(line.c_str(), "MARKER_TAG=");
        if (pos != 0)
        {
          bcName.assign(pos + strlen("MARKER_TAG="));
          if (nme == NotFound)
            continue;
        }
      }

      // locate number of elements in this marker
      if (nme == NotFound)
      {
        nme = su2_strkey(line, "MARKER_ELEMS=");
        if (bcName.empty())
          continue;
      }

      // arrive here when both bcName and nme are defined
      markTags[rmark] = bcName;
      su2_read_marker(nme, in, ecollect, markerID[rmark]);
      dbprint("Processed marker ", bcName);
      ++rmark;
      dbprint(rmark, "markers found.");
      nme = NotFound;
      bcName.clear();
    }
  }

  // construct sections
  const int net = ecollect.size();
  Indices sectionIndex(net, NotFound);
  for (int iet = 0; iet < net; ++iet)
  {
    if (ecollect[iet].empty())
      continue;
    uint isec = appendSection(Mx::ElementType(iet), ecollect[iet]);
    sectionIndex[iet] = isec;
  }

  // generate boundary sections
  if (nmark != NotFound)
  {
    for (uint i = 0; i < nmark; ++i)
    {
      MxMeshBoco bc; // type unknown; not in this file
      bc.rename(markTags[i]);
      const MarkerID &mid(markerID[i]);
      const int ne = mid.size();
      for (int j = 0; j < ne; ++j)
      {
        uint isec = sectionIndex[mid[j].first];
        assert(isec != NotFound);
        uint elix = section(isec).indexOffset() + mid[j].second;
        bc.appendElement(elix);
      }
      appendBoco(bc);
    }
  }
  else
  {
    dbprint("No marker tags in SU2 file.");
  }
}

static string strip_path(const std::string &s)
{
#ifdef GENUA_WIN32
  char sep = '\\';
#else
  char sep = '/';
#endif
  size_t posn = s.find_last_of(sep);
  if (posn == string::npos)
    return s;
  else
    return s.substr(posn + 1, string::npos);
}

void MxMesh::writeEnsight(const std::string &basename) const
{
  string bname = basename.substr(0, basename.find(".case"));
  string geofile = string(bname + ".geometry");
  StringArray varfiles;
  Indices outFields;

  // case file
  {
    ofstream os(string(bname + ".case").c_str());
    os << "FORMAT" << endl
       << "type:  ensight gold" << endl
       << endl;
    os << "GEOMETRY" << endl;
    os << "model:   " << strip_path(geofile) << endl
       << endl;

    // determine which fields to output
    for (uint i = 0; i < nfields(); ++i)
    {
      int nd = field(i).ndimension();
      if (not field(i).realField())
        continue;
      if (not field(i).nodal())
        continue;
      if (nd != 1 and nd != 3)
        continue;
      outFields.push_back(i);

      string fcmp = field(i).name();
      std::replace(fcmp.begin(), fcmp.end(), ' ', '_');
      std::replace(fcmp.begin(), fcmp.end(), ',', '_');
      varfiles.push_back(bname + '.' + fcmp);
    }

    if (not outFields.empty())
    {
      os << "VARIABLE" << endl;
      for (uint i = 0; i < outFields.size(); ++i)
      {
        const MxMeshField &f(field(outFields[i]));
        if (f.ndimension() == 1)
          os << "scalar per ";
        else if (f.ndimension() == 3)
          os << "vector per ";
        if (f.nodal())
          os << "node: ";
        else
          os << "element: ";

        // does not enforce the 19 character limit on variable descriptions
        string dsc = f.name();
        std::replace(dsc.begin(), dsc.end(), ' ', '_');
        os << dsc << "  ";
        os << strip_path(varfiles[i]) << endl;
      }
      os << endl;
    }

    os.close();
  }

  // geometry file
  {
    ofstream os(geofile.c_str(), std::ios::out | std::ios::binary);

    char hdr[5 * 80];
    memset(hdr, ' ', sizeof(hdr));
    strcpy(&hdr[0], "C Binary");

    size_t nchar = std::min(size_t(80), meshName.size());
    if (nchar > 0)
      std::copy(meshName.begin(), meshName.begin() + nchar, &hdr[1 * 80]);
    else
      strcpy(&hdr[1 * 80], "MxMesh written by libgenua");

    string info;
    info = str(nnodes()) + " nodes, " + str(nelements()) + " elements";
    nchar = std::min(size_t(80), info.size());
    std::copy(info.begin(), info.begin() + nchar, &hdr[2 * 80]);

    strcpy(&hdr[3 * 80], "node id given");
    strcpy(&hdr[4 * 80], "element id given");

    // write header
    os.write(hdr, sizeof(hdr));

    // write each section as one part
    for (uint i = 0; i < nsections(); ++i)
      section(i).writeEnsight(i + 1, os);
    os.close();
  }

  // variable files - one file per field
  {
    char hdr[80];
    for (uint i = 0; i < outFields.size(); ++i)
    {
      const MxMeshField &f(field(outFields[i]));
      memset(hdr, ' ', sizeof(hdr));
      ofstream os(varfiles[i].c_str(), std::ios::binary | std::ios::out);
      size_t nchar = std::min(size_t(80), f.name().size());
      std::copy(f.name().begin(), f.name().begin() + nchar, hdr);
      os.write(hdr, sizeof(hdr));
      for (uint j = 0; j < nsections(); ++j)
        section(j).writeEnsight(j + 1, f, os);
      os.close();
    }
  }
}

static int id_flags(const char *s)
{
  int flags = 0;
  if (strstr(s, "off"))
    flags = Mx::OffId;
  else if (strstr(s, "assign"))
    flags = Mx::AssignId;
  else if (strstr(s, "given"))
    flags = Mx::GivenId;
  else if (strstr(s, "ignore"))
    flags = Mx::IgnoreId;

  if (strstr(s, "element id"))
    flags = (flags << 8);
  return flags;
}

void MxMesh::readEnsight(const std::string &casename)
{
#ifdef GENUA_WIN32
  const char sep = '\\';
#else
  const char sep = '/';
#endif

  // extract path prefix from case file name
  string bpath;
  string::size_type posn = casename.find_last_of(sep);
  if (posn != string::npos)
    bpath = casename.substr(0, posn + 1);

  // read casefile
  string geofile;
  StringArray varfiles;
  Indices vardim;
  {
    const char *keys[] = {"model:", "scalar per node:", "vector per node:"};
    ifstream in(casename.c_str());
    string line;
    while (getline(in, line))
    {
      line = strip(line);
      posn = line.find(keys[0]);
      if (posn == 0)
      {
        posn = line.find_last_of(" \t");
        geofile = bpath + line.substr(posn + 1, string::npos);
        cout << "Geometry file name: " << geofile << endl;
        continue;
      }
      posn = line.find(keys[1]);
      if (posn == 0)
      {
        posn = line.find_last_of(" \t");
        varfiles.push_back(bpath + line.substr(posn + 1, string::npos));
        vardim.push_back(1);
        cout << "Scalar variable file name: " << varfiles.back() << endl;
        continue;
      }
      posn = line.find(keys[2]);
      if (posn == 0)
      {
        posn = line.find_last_of(" \t");
        varfiles.push_back(bpath + line.substr(posn + 1, string::npos));
        vardim.push_back(3);
        cout << "Vector variable file name: " << varfiles.back() << endl;
        continue;
      }
    }
  }

  if (geofile.empty())
    throw Error("readEnsight(): No geometry file found.");

  // read geometry file
  {
    uint flags = 0;
    ifstream in(geofile.c_str(), std::ios::binary | std::ios::in);
    char hdr[5 * 80];
    in.read((char *)&hdr, sizeof(hdr));
    for (int i = 0; i < 5; ++i)
      hdr[i * 80 + 79] = '\0';
    if (strstr(hdr, "C Binary") == 0)
      throw Error("readEnsight(): Only 'C Binary' file format supported.");

    // extract node/element id flags
    flags = id_flags(&hdr[3 * 80]) | id_flags(&hdr[4 * 80]);
    while (in)
      MxMeshSection::createFromEnsight(this, flags, in);
  }
}

void MxMesh::writeFFA(const std::string &basename) const
{
  // build filenames
  string bmsh = append_suffix(basename, ".bmsh");
  string aboc = append_suffix(basename, ".aboc");

  // mesh geometry : coordinates and elements
  {
    FFANodePtr root(new FFANode("unstr_grid_data"));
    FFANode *title = new FFANode("title");
    title->copy("Mesh generated by sumo+tetgen");
    root->append(title);

    FFANodePtr region(new FFANode("region"));
    FFANodePtr region_name(new FFANode("region_name"));
    region_name->copy("fluid domain");
    region->append(region_name);
    root->append(region);

    // convert coordinate format
    dbprint("Converting coordinates...");
    {
      const size_t nv = vtx.size();
      Vector xyz(3 * nv);
      for (size_t i = 0; i < nv; ++i)
      {
        xyz[i] = vtx[i][0];
        xyz[nv + i] = vtx[i][1];
        xyz[2 * nv + i] = vtx[i][2];
      }
      dbprint("Coordinate conversion OK, creating FFA node...");

      FFANode *coord = new FFANode("coordinates");
      coord->copy(nv, 3, &xyz[0]);
      region->append(coord);
    }
    dbprint("Coordinate node appended.");

    // append volume mesh regions
    const int nsec = nsections();
    for (int i = 0; i < nsec; ++i)
    {
      if (section(i).nelements() > 0)
        section(i).toFFA(*region);
    }

    ofstream mos(asPath(bmsh).c_str(), ofstream::binary);
    root->bwrite(mos);
  }

  // boundary conditions
  {
    FFANodePtr bocroot(new FFANode("boundary_data"));
    FFANodePtr region(new FFANode("region"));
    FFANodePtr region_name(new FFANode("region_name"));
    region_name->copy("fluid domain");
    region->append(region_name);
    bocroot->append(region);

    // append volume mesh regions
    const int nbc = nbocos();
    for (int i = 0; i < nbc; ++i)
      boco(i).toFFA(*region);

    ofstream bos(asPath(aboc).c_str());
    bocroot->awrite(bos);
  }
}

void MxMesh::readFFA(const std::string &bmeshFile)
{
  clear();

  FFANode root;
  root.read(bmeshFile);

  FFANodePtr region, child;
  uint ipos = root.findChild("region");
  if (ipos == NotFound)
  {
    ipos = root.findChild("coordinates");
    if (ipos == NotFound)
      throw Error(".bmesh root node does not contain child node 'coordinates'.");
    child = root.child(ipos);
  }
  else
  {
    region = root.child(ipos);
    ipos = region->findChild("coordinates");
    if (ipos == NotFound)
      throw Error(".bmesh region node does not contain child node 'coordinates'.");
    child = region->child(ipos);
  }

  int nv = child->nrows();
  int nd = child->ncols();
  if (nd > 3)
    throw Error("MxMesh::readFFA - Coordinate dimensions >3 not supported.");

  if (child->contentType() != FFAFloat8)
    throw Error("MxMesh::readFFA - Coordinates not stored in 8-byte reals.");

  Vector xyz(nv * nd);
  child->retrieve((void *)xyz.pointer());

  // convert from the peculiar bmsh coordinate format
  vtx.resize(nv);
  for (int j = 0; j < nv; ++j)
  {
    for (int k = 0; k < nd; ++k)
      vtx[j][k] = xyz[k * nv + j];
  }

  if (not region)
  {
    const int n = root.nchildren();
    for (int i = 0; i < n; ++i)
      readFFARegion(*root.child(i));
  }
  else
  {
    const int n = region->nchildren();
    for (int i = 0; i < n; ++i)
      readFFARegion(*region->child(i));
  }
  countElements();

  // create one boco group for each section
  // TODO : pass abocFile, parse and map BC codes
  const int nsec = nsections();
  for (int i = 0; i < nsec; ++i)
  {
    if (section(i).surfaceElements())
    {
      MxMeshBoco bc;
      bc.rename(section(i).name());
      uint ibegin = section(i).indexOffset();
      uint iend = ibegin + section(i).nelements();
      bc.setRange(ibegin, iend);
      appendBoco(bc);
    }
  }
}

bool MxMesh::appendFFAFields(const std::string &boutFile)
{
  FFANode root;
  root.read(boutFile);
  uint ipos = root.findChild("region");
  if (ipos != NotFound)
  {

    // extract freestream data if possible
    MxSolutionTreePtr pcase = MxSolutionTree::create("Solution");
    uint fpos = root.findChild("free_stream_data");
    if (fpos != NotFound)
    {
      XmlElement xe("FreestreamData");
      double val, T(288.0), Rs(287.), gamma(1.4), aoo(0.0);
      SVector<3, double> ufar;
      FFANodePtr child = root.child(fpos);
      int n = child->nchildren();
      for (int i = 0; i < n; ++i)
      {
        FFANodePtr elm = child->child(i);
        size_t nval = elm->nrows() * elm->ncols();
        if (elm->contentType() == FFAFloat8)
        {
          if (nval == 1)
          {
            elm->retrieve(&val);
            xe.attribute(elm->name()) = str(val);
            if (elm->name() == "temperature")
              T = val;
            else if (elm->name() == "gamma")
              gamma = val;
            else if (elm->name() == "rgas")
              Rs = val;
          }
          else if (nval == 3)
          {
            elm->retrieve(ufar.pointer());
            xe.attribute(elm->name()) = str(ufar);
          }
        }
      }
      aoo = std::sqrt(gamma * Rs * T);
      pcase->annotate(xe);

      // name subcase if all data found
      if (aoo != 0 and sq(ufar) != 0)
      {
        Real Mach = norm(ufar) / aoo;
        Real alpha = deg(atan(ufar[2] / ufar[0]));
        Real beta = deg(asin(ufar[1] / norm(ufar)));
        stringstream ss;
        ss.precision(3);
        ss << "Mach " << Mach << " alfa " << alpha;
        if (beta != 0)
          ss << " beta " << beta;
        pcase->rename(ss.str());
      }

      // region may contains fields or time steps
      FFANodePtr pregion = root.child(ipos);
      if (pregion->findChild("time") == NotFound)
      {
        MxSolutionTreePtr psub = appendSubcase(pregion);
        if (psub != nullptr)
          pcase->appendFields(psub->fields());
      }
      else
      {
        const int nt = pregion->nchildren();
        for (int j = 0; j < nt; ++j)
        {
          FFANodePtr ptime = pregion->child(j);
          if (ptime->name() == "time")
          {
            MxSolutionTreePtr psub = appendSubcase(ptime);
            if (psub->fields().size() != 0)
              pcase->append(psub);
          }
        }
      }

      // append solution tree
      if (soltree == nullptr)
        soltree = boost::make_shared<MxSolutionTree>("Subcases");
      soltree->append(pcase);
    }
  }
  else
  {
    clog << "[w] Expected to find 'region' node below root, not found." << endl;
    return false;
  }

  return true;
}

size_t MxMesh::writeFieldsBdis(const std::string &basename) const
{
  const size_t nf = nfields();
  size_t ifield = 1;
  for (size_t i = 0; i < nf; ++i)
  {
    const MxMeshField &f(field(i));
    if (f.nodal() and f.ndimension() >= 3)
    {
      bool ok = f.writeBdis(basename + str(ifield) + ".bdis");
      if (ok)
        ++ifield;
    }
  }

  return ifield - 1;
}

MxSolutionTreePtr MxMesh::appendSubcase(FFANodePtr pregion)
{
  MxSolutionTreePtr pcase = MxSolutionTree::create("Region");
  const int n = pregion->nchildren();
  for (int i = 0; i < n; ++i)
  {
    MxMeshField f(this, true); // nodal fields only
    FFANodePtr pchild = pregion->child(i);
    if (pchild->name() == "n_timestep")
    {
      int nstep;
      pchild->retrieve(nstep);
      pcase->rename("TimeStep " + str(nstep));
    }
    uint ifield = NotFound;
    if (f.fromFFA(*pchild))
    {
      ifield = appendField(std::move(f));
      pcase->appendField(ifield);
    }
  }
  return pcase;
}

void MxMesh::readFFARegion(const FFANode &root)
{
  if (root.name() == "element_group")
  {
    MxMeshSection sec(this);
    sec.rename("Section " + str(sections.size() + 1));
    sections.push_back(sec);
    if (not sections.back().fromFFA(root))
      sections.pop_back();
  }
  else if (root.name() == "boundary")
  {
    uint npos = root.findChild("boundary_name");
    uint ipos = root.findChild("belem_group");
    if (ipos != NotFound)
    {
      MxMeshSection sec(this);
      if (npos != NotFound)
      {
        string bname;
        root.child(npos)->retrieve(bname);
        sec.rename(bname);
      }
      else
        sec.rename("Section " + str(sections.size() + 1));
      sections.push_back(sec);
      if (not sections.back().fromFFA(*root.child(ipos)))
        sections.pop_back();
      else
        dbprint("Boundary element section", sections.size() - 1,
                " ne ", sections.back().nelements());
    }
  }
}

void MxMesh::readFFABoundary(const FFANode &root)
{
  assert(root.name() == "boundary");

  MxMeshSection sec(this);
  string bname;
  bool ok = false;
  const int nch = root.nchildren();
  for (int i = 0; i < nch; ++i)
  {
    FFANodePtr child = root.child(i);
    string cn = child->name();
    if (cn == "boundary_name")
    {
      child->retrieve(bname);
      sec.rename(bname);
    }
    else if (cn == "belem_group")
    {
      ok = sec.fromFFA(*child);
    }
  }

  if (ok)
  {
    appendSection(sec);
  }
}

void MxMesh::fakeNastran(const std::string &fname) const
{
  // write mesh topology to file
  ofstream os(asPath(fname).c_str());
  const size_t nv = nnodes();
  os << "$ .f06-lookalike written by libgenua/MxMesh::fakeNastran() " << endl;
  os << "ID " << fname << endl;
  os << "SOL 103" << endl;
  os << "CEND" << endl;
  os << "BEGIN BULK" << endl;

  // write grid points and elements
  writeNastran(os, 0, 0);

  // check for eigenmodes
  Indices iegm;
  Vector gk, gm;

  // figure out which vector fields contain eigenmode shapes
  // this data is stored in a mesh annotation
  XmlElement::const_iterator itr, last;
  const int nf = nfields();
  for (int i = 0; i < nf; ++i)
  {
    last = field(i).noteEnd();
    for (itr = field(i).noteBegin(); itr != last; ++itr)
    {
      if (itr->name() == "Eigenmode")
      {
        iegm.push_back(i);
        gk.push_back(itr->attr2float("modal_stiffness", 0.0));
        gm.push_back(itr->attr2float("modal_mass", 1.0));
      }
    }
  }

  if (iegm.empty())
    return;

  os << endl
     << endl;
  os << "R E A L   E I G E N V A L U E S" << endl
     << endl;
  const int nm = iegm.size();
  for (int jm = 0; jm < nm; ++jm)
  {
    Real omega = sqrt(gk[jm] / gm[jm]);
    Real f = omega / (2 * PI);
    os << "     " << jm + 1 << "    " << jm + 1;
    os << "     " << nstr(gk[jm]) << "     " << nstr(omega);
    os << "     " << nstr(f);
    os << "     " << nstr(gm[jm]) << "     " << nstr(gk[jm]) << endl;
  }

  for (int jm = 0; jm < nm; ++jm)
  {

    const MxMeshField &mxf(field(iegm[jm]));

    Real f = sqrt(gk[jm] / gm[jm]) / (2 * PI);
    os << endl;
    os << "      EIGENVALUE =  " << nstr(gk[jm]) << endl;
    os << "          CYCLES =  " << nstr(f);
    os << "         R E A L   E I G E N V E C T O R   N O .          ";
    os << jm + 1 << endl
       << endl
       << endl;

    for (size_t i = 0; i < nv; ++i)
    {
      Vct3 dx;
      mxf.value(i, dx);
      os << "         " << i + 1 << "   G   " << nstr(dx[0]) << "  "
         << nstr(dx[1]) << "  " << nstr(dx[2]) << "  0.0 0.0 0.0" << endl;
    }

    os << endl
       << endl;
  }
}

void MxMesh::writeSTL(const std::string &fname, bool binaryStl) const
{
  Indices tri;
  for (const MxMeshSection &sec : sections)
    sec.toTriangles(tri);

  TriMesh tms;
  tms.importMesh(vtx, tri);
  if (binaryStl)
    tms.writeBinarySTL(fname);
  else
    tms.writeAsciiSTL(fname);
}

void MxMesh::writePLY(const std::string &fname, bool binary) const
{
  Indices tri;
  for (const MxMeshSection &sec : sections)
    sec.toTriangles(tri);

  TriMesh tms;
  tms.importMesh(vtx, tri);
  tms.toPLY(fname, binary);
}

void MxMesh::writeSmesh(const std::string &fname,
                        const PointList<3> &holes,
                        const PointList<3> &regionMarkers,
                        const Vector &regionAttr) const
{
  ofstream os(asPath(fname).c_str());
  os.precision(16);
  os << std::scientific;

  os << endl;
  os << "# node list" << endl;
  const int nv = nnodes();
  os << nv << " 3 0 0" << endl;
  for (int i = 0; i < nv; ++i)
    os << i << ' ' << vtx[i][0] << ' '
       << vtx[i][1] << ' ' << vtx[i][2] << endl;
  os << endl;

  // count triangles
  int nf = 0;
  const int nsec = sections.size();
  for (int i = 0; i < nsec; ++i)
  {
    if (section(i).elementType() == Mx::Tri3)
      nf += section(i).nelements();
  }

  if (size_t(nf) != nelements())
    dbprint("[W] MxMesh::writeSmesh() trying to write mesh with"
            " incompatible element types.");

  // assemble boundary tags
  Indices btags(nelements(), 0);
  for (uint ibc = 0; ibc < nbocos(); ++ibc)
  {
    Indices elix;
    boco(ibc).elements(elix);
    const int ne = elix.size();
    for (int i = 0; i < ne; ++i)
      btags[elix[i]] = ibc + 1;
  }

  os << "# face list" << endl;
  os << nf << " 1" << endl;
  for (int isec = 0; isec < nsec; ++isec)
  {
    const MxMeshSection &sec(section(isec));
    if (sec.elementType() != Mx::Tri3)
      continue;
    const int eloff = sec.indexOffset();
    const int ne = sec.nelements();
    for (int i = 0; i < ne; ++i)
    {
      const uint *vi = sec.element(i);
      os << "3  " << vi[0] << ' ' << vi[1]
         << ' ' << vi[2] << ' ' << btags[eloff + i] << endl;
    }
  }
  os << endl;

  os << "# hole list" << endl;
  os << holes.size() << endl;
  for (uint i = 0; i < holes.size(); ++i)
    os << i << ' ' << holes[i][0] << ' '
       << holes[i][1] << ' ' << holes[i][2] << endl;
  os << endl;

  size_t nreg = regionMarkers.size();
  assert(regionAttr.size() == nreg);
  os << "# region attribute list" << endl;
  os << nreg << endl;
  for (size_t i = 0; i < nreg; ++i)
    os << i << ' ' << regionMarkers[i] << ' ' << regionAttr[i] << endl;
  os << endl;
}

void MxMesh::readTetgen(const std::string &basename, DVector<uint> *ftags)
{
  clear();
  string nodefile = append_suffix(basename, ".node");
  string elefile = append_suffix(basename, ".ele");
  string facefile = append_suffix(basename, ".face");

  uint offs(0);
  ifstream nis(asPath(nodefile).c_str());
  if (not nis)
    throw Error("Cannot open tetgen node file: " + nodefile);
  offs = readTetgenNodes(nis);
  nis.close();

  ifstream fis(asPath(facefile).c_str());
  if (not fis)
    throw Error("Cannot open tetgen face file: " + facefile);
  readTetgenFaces(fis, offs, ftags);
  fis.close();

  ifstream eis(asPath(elefile).c_str());
  if (eis)
  {
    readTetgenElements(eis, offs);
    eis.close();
  }
}

int MxMesh::readTetgenNodes(std::istream &is)
{
  int nn(0), offs(0);

  // analyse header line
  string line = findTetgenHeader(is);
  const char *pos;
  char *tail;
  pos = line.c_str();

  nn = genua_strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("MxMesh::readTetgenNodes() cannot find valid node file header.");

  vtx.resize(nn);
  if (nn == 0)
    return 0;

  // read first node line to determine node index offset
  getline(is, line);
  pos = line.c_str();
  offs = genua_strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("MxMesh::readTetgenNodes() - invalid first node line.");

  for (int k = 0; k < 3; ++k)
  {
    pos = tail;
    vtx[0][k] = genua_strtod(pos, &tail);
    assert(pos != tail);
  }

  int j(1);
  while (getline(is, line))
  {

    pos = line.c_str();
    genua_strtol(pos, &tail, 10);
    assert(pos != tail);
    for (int k = 0; k < 3; ++k)
    {
      pos = tail;
      vtx[j][k] = genua_strtod(pos, &tail);
      assert(pos != tail);
    }

    ++j;
    if (j == nn)
      break;
  }

  return offs;
}

void MxMesh::readTetgenFaces(std::istream &is, int offs, DVector<uint> *ptags)
{
  int nface(0), nbm(0);

  // analyse header line
  string line = findTetgenHeader(is);
  const char *pos;
  char *tail;
  pos = line.c_str();

  nface = genua_strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("MxMesh::readTetgenFaces() cannot find "
                "valid face file header.");

  pos = tail;
  nbm = genua_strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("MxMesh::readTetgenFaces() cannot find "
                "valid face file header.");

  if (nface == 0)
    return;

  Indices idx(3 * nface);
  DVector<uint> tags(nface);
  int jf(0);
  while (getline(is, line))
  {

    pos = line.c_str();
    genua_strtol(pos, &tail, 10);
    assert(pos != tail);
    for (int k = 0; k < 3; ++k)
    {
      pos = tail;
      idx[3 * jf + k] = genua_strtol(pos, &tail, 10) - offs;
      assert(pos != tail);
    }

    if (nbm > 0)
    {
      pos = tail;
      tags[jf] = genua_strtoul(pos, &tail, 10);
    }

    ++jf;
    if (jf == nface)
      break;
  }

  // create mesh sections and boundary groups
  if (nbm == 0 or ptags != 0)
  {
    appendSection(Mx::Tri3, idx);
  }
  else
  {

    DVector<uint> alltags(tags);
    sort_unique(alltags);

    uint eloff = nelements();
    const int ntags = alltags.size();
    for (int j = 0; j < ntags; ++j)
    {

      uint jtag = alltags[j];
      string tagname = "Marker " + str(jtag);
      uint nel = std::count(tags.begin(), tags.end(), jtag);
      Indices eli(3 * nel);
      uint k(0);
      for (int i = 0; i < nface; ++i)
      {
        if (tags[i] == jtag)
        {
          const uint *vi = &idx[3 * i];
          std::copy(vi, vi + 3, &eli[3 * k]);
          ++k;
        }
      }
      assert(k == nel);
      appendSection(Mx::Tri3, eli);
      section(j).rename(tagname);
      section(j).tag(jtag);

      MxMeshBoco bg(Mx::BcWall);
      bg.rename(tagname);
      bg.setRange(eloff, eloff + nel);
      bg.tag(jtag);
      bocos.push_back(bg);
      eloff += nel;
    }
  }

  if (ptags != 0)
    ptags->swap(tags);

  countElements();
}

void MxMesh::readTetgenElements(std::istream &is, int offs)
{
  int nele(0);

  // analyse header line
  string line = findTetgenHeader(is);
  const char *pos;
  char *tail;
  pos = line.c_str();

  nele = genua_strtol(pos, &tail, 10);
  if (tail == pos)
    throw Error("MxMesh::readTetgenElements() cannot find "
                "valid element file header.");

  if (nele == 0)
    return;

  Indices idx(4 * nele);
  int j(0);
  while (getline(is, line))
  {

    pos = line.c_str();
    genua_strtol(pos, &tail, 10);
    assert(pos != tail);
    for (int k = 0; k < 4; ++k)
    {
      pos = tail;
      idx[4 * j + k] = genua_strtol(pos, &tail, 10) - offs;
      assert(pos != tail);
    }

    ++j;
    if (j == nele)
      break;
  }

  appendSection(Mx::Tet4, idx);
  sections.back().rename("TetRegion");
  countElements();
}
