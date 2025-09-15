
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
#include "cgnsfile.h"
#include "cgnszone.h"
#include "cgnssection.h"
#include "cgnssol.h"
#include "cgnsdescriptor.h"
#include "cgnsfwd.h"
#include "zipfile.h"
#include "trimesh.h"
#include "basicedge.h"
#include "meshfields.h"
#include "dbprint.h"

#include <sstream>

using namespace std;

bool MxMesh::loadAny(const std::string &fname)
{
  dbprint("MxMesh::loadAny(): ", fname);
  string sfx = toLower(filename_suffix(fname));

  // first attempt: LZ4 or GBF format
  BinFileNodePtr bfp = BinFileNode::createFromFile(fname);
  if (bfp)
  {

    XmlElement xe;
    xe.fromGbf(bfp, true);
    fromXml(xe);
  }
  else if (ZipFile::isZip(fname))
  {

    XmlElement xz;
    xz.zread(fname);
    clear();
    if (xz.name() == "MxMesh")
    {
      fromXml(xz);
    }
    else if (xz.name() == "Triangulation")
    {
      TriMesh tm;
      tm.fromXml(xz);
      appendSection(tm);
    }
    else
    {
      return false;
    }
  }
  else if (CgnsFile::isCgns(fname))
  {

    clear();
    readCgns(fname);
  }
  else if (sfx == ".bmsh")
  {

    clear();
    readFFA(fname);

#if defined(HAVE_RPLY)
  }
  else if (TriMesh::isPLY(fname))
  {

    TriMesh tm;
    tm.fromPLY(fname);
    appendSection(tm);

#endif

#if defined(HAVE_NETCDF)
  }
  else if (sfx == ".taumesh")
  {

    clear();
    readTau(fname);

#endif
  }
  else if (sfx == ".su2")
  {

    clear();
    readSU2(fname);
  }
  else if (sfx == ".vtk")
  {

    clear();
    readLegacyVtk(fname);
  }
  else if (sfx == ".bout")
  {

    if (nnodes() == 0)
      return false;

    appendFFAFields(fname);
  }
  else if (sfx == ".stl")
  {

    clear();

    TriMesh tm;
    tm.readSTL(fname);
    tm.detectEdges(rad(44.0), 1e-6);
    if (tm.nfaces() > 0)
    {
      uint tsec = appendSection(tm);
      section(tsec).rename(fname);
    }

    std::vector<BasicEdge> redges;
    const size_t ne = tm.nedges();
    for (size_t i = 0; i < ne; ++i)
    {
      if (tm.edegree(i) != 2)
      {
        const TriEdge &edg(tm.edge(i));
        redges.push_back(BasicEdge(edg.source(), edg.target()));
      }
    }
    std::sort(redges.begin(), redges.end());
    redges.erase(std::unique(redges.begin(), redges.end()), redges.end());

    const size_t nre = redges.size();
    Indices rlv(2 * nre);
    for (size_t i = 0; i < nre; ++i)
    {
      rlv[2 * i + 0] = redges[i].source();
      rlv[2 * i + 1] = redges[i].target();
    }
    if (not rlv.empty())
    {
      uint rsec = appendSection(Mx::Line2, rlv);
      section(rsec).rename("Ridges");
    }
  }
  else if (sfx == ".node" or sfx == ".ele" or sfx == ".face")
  {

    clear();
    DVector<uint> ftags;

    // NOTE: This assumes that boundary faces are ead first, so that the
    // first nface elements in the mesh are triangles, and tets follow
    readTetgen(fname, &ftags);
    size_t nface = ftags.size();

    assert(nsections() == 2);
    assert(section(0).elementType() == Mx::Tri3);
    const Indices &idx(section(0).nodes());
    assert(3 * nface == idx.size());

    // count how many elements are associated with each marker tag;
    // if this number is above the limit, then create a boco set for
    // the tag, otherwise, just ignore it
    const size_t min_nel_tag = 16;

    DVector<uint> alltags(ftags);
    sort_unique(alltags);
    const uint ntags = alltags.size();
    for (uint j = 0; j < ntags; ++j)
    {

      uint jtag = alltags[j];
      size_t nel = std::count(ftags.begin(), ftags.end(), jtag);

      if (nel >= min_nel_tag)
      {
        string tagname = "Marker " + str(jtag);
        Indices eli(3 * nel);
        uint k = 0;
        for (size_t i = 0; i < nface; ++i)
        {
          if (ftags[i] == jtag)
          {
            const uint *vi = &idx[3 * i];
            std::copy(vi, vi + 3, &eli[3 * k]);
            ++k;
          }
        }
        assert(k == nel);

        MxMeshBoco bg(Mx::BcElementSet);
        bg.rename(tagname);
        bg.appendElements(eli);
        bg.tag(jtag);
        bocos.push_back(bg);
      }
    }
  }
  else if (sfx == ".inp")
  {

    clear();
    readAbaqus(fname);
  }
  else if (fname.find("AERELPLOT") != string::npos)
  {

    dbprint("Trying to import from AEREL plot format.");
    clear();
    readAerel(fname);
  }
  else
  {

    // try to read as xml
    XmlElement xe;
    try
    {
      xe.read(fname);
    }
    catch (Error &xcp)
    {
      dbprint("Attempt to read MxMesh from plain xml failed: ", xcp.what());
      return false;
    }

    string xtype = xe.name();
    if (xtype == "MxMesh")
    {
      fromXml(xe);
    }
    else if (xtype == "MeshViz")
    {
      MeshFields mvz;
      mvz.fromXml(xe);
      importMvz(mvz);
    }
    else if (xtype == "Triangulation")
    {
      TriMesh tm;
      tm.fromXml(xe);
      appendSection(tm);
    }
    else if (xtype == "Mesh")
    {
      XmlElement::const_iterator itr;
      itr = xe.findChild("Triangulation");
      if (itr != xe.end())
      {
        TriMesh tm;
        tm.fromXml(*itr);
        appendSection(tm);
      }
    }
    else
    {
      return false;
    }
  }

  return true;
}

void MxMesh::readCgns(const std::string &fname)
{
  CgnsFile cgf;
  cgf.ropen(fname);

  clear();
  CgnsZone cgz = cgf.readZone(1);

  // check for annotations
  CgnsDescriptor cgd;
  int nd = cgd.nnodes(cgf.index(), "/Base1/MxMesh");
  for (int i = 0; i < nd; ++i)
  {
    cgd.read(i + 1);
    if (cgd.name() == "MxMeshNote")
    {
      stringstream ss;
      ss.str(cgd.text());
      xnote.read(ss, XmlElement::PlainText);

      // recover deformation from xml payload
      XmlElement::const_iterator itr, last;
      last = xnote.end();
      for (itr = xnote.begin(); itr != last; ++itr)
      {
        if (itr->name() == "MxMeshDeform")
        {
          deforms.push_back(MxMeshDeform(this));
          deforms.back().fromXml(*itr);
        }
      }
    }
  }

  cgz.readNodes(vtx);
  const int ns = cgz.nsections();
  sections.resize(ns);
  nelm = 0;
  for (int i = 0; i < ns; ++i)
  {
    CgnsSection cgs = cgz.readSection(i + 1);
    sections[i] = MxMeshSection(this);
    sections[i].readCgns(cgs);
    sections[i].indexOffset(nelm);
    nelm += sections[i].nelements();
  }

  const int nb = cgz.nbocos();
  bocos.resize(nb);
  for (int i = 0; i < nb; ++i)
  {
    CgnsBoco cb = cgz.readBoco(i + 1);
    bocos[i].readCgns(cb);
  }

  bool nodal(true);
  const int nsol = cgz.nsols();
  for (int j = 0; j < nsol; ++j)
  {
    CgnsSol cs = cgz.readSol(j + 1);
    if (cs.location() == cgns::Vertex)
      nodal = true;
    else if (cs.location() == cgns::CellCenter)
      nodal = false;
    else
      continue;

    const int nf = cs.nfields();
    for (int i = 0; i < nf; ++i)
    {
      MxMeshField f(this, nodal);
      f.readCgns(cs, i + 1);
      f.solutionIndex(j);
      fields.push_back(f);
    }
  }

  // rebuild vector fields
  assembleVectorFields();
}

void MxMesh::writeCgns(const std::string &fname, bool bcAsSections) const
{
  CgnsFile cgf;
  cgf.wopen(fname);

  // count volume elements in all sections
  uint ne(0), ncell(0);
  const int ns = sections.size();
  for (int i = 0; i < ns; ++i)
  {
    ne += section(i).nelements();
    if (section(i).volumeElements())
      ncell += section(i).nelements();
  }

  // create a single unstructured zone which contains the whole mesh
  CgnsZone cgz = cgf.newZone("MxMesh", vtx.size(), ncell);

  // store deformation as xml
  XmlElement xtmp(xnote);
  if (not deforms.empty())
  {
    if (xtmp.name() != "MxMeshNote")
      xtmp = XmlElement("MxMeshNote");
    for (uint i = 0; i < deforms.size(); ++i)
      xtmp.append(deforms[i].toXml(true));
  }

  // annotation goes into the Zone_t node
  if (xtmp.name() == "MxMeshNote")
  {
    stringstream ss;
    xtmp.write(ss, XmlElement::PlainText);

    CgnsDescriptor cgd("MxMeshNote");
    cgd.text(ss.str());
    cgd.write(cgf.index(), "/Base1/MxMesh");
  }

  // nodal data
  cgz.writeNodes(vtx);

  // add all sections
  ne = 0;
  for (int i = 0; i < ns; ++i)
  {

    // when exporting boundaries as sections, skip all surface sections here
    if (bcAsSections and (not section(i).volumeElements()))
      continue;

    CgnsSection cgs(cgf.index(), cgf.base(), cgz.index(), 0);
    cgs.elementOffset(ne);
    sections[i].writeCgns(cgs, i);
    ne += sections[i].nelements();
  }

  // add bc definitions
  const int nbc = bocos.size();
  if (bcAsSections)
  {

    // write all BC markers as sections
    for (int i = 0; i < nbc; ++i)
    {
      if (boco(i).nelements() == 0)
        continue;
      uint isec = containedInSection(i);
      if (isec == NotFound) // cannot write in this format
        continue;
      CgnsSection cgs(cgf.index(), cgf.base(), cgz.index(), 0);
      cgs.elementOffset(ne);
      Mx::ElementType etype = section(isec).elementType();
      cgns::ElementType_t ctype = MxElementType2Cgns(etype);
      if (ctype == cgns::ElementTypeNull)
        continue;
      cgs.rename(boco(i).name());
      cgs.elementType(ctype);

      Indices elix;
      boco(i).elements(elix);
      const int nbe = elix.size();
      const int nve = nElementNodes(etype);
      uint eloff = section(isec).indexOffset();

      CgnsIntMatrix em(nve, nbe);
      for (int j = 0; j < nbe; ++j)
      {
        assert(elix[j] >= eloff and elix[j] < eloff + section(isec).nelements());
        const uint *vi = section(isec).element(elix[j] - eloff);
        for (int k = 0; k < nve; ++k)
        {
          em(k, j) = vi[k] + 1;
        }
      }
      cgs.writeElements(em);
      ne += nbe;
    }
  }
  else
  {
    // proper CGNS, element sets
    for (int i = 0; i < nbc; ++i)
    {
      if (boco(i).nelements() == 0)
        continue;
      CgnsBoco cgb(cgf.index(), cgf.base(), cgz.index(), 0);
      bocos[i].writeCgns(cgb);
    }
  }

  uint nvs(0), ncs(0);
  for (uint i = 0; i < nfields(); ++i)
  {
    if (fields[i].nodal())
      nvs++;
    else
      ncs++;
  }

  if (nvs > 0)
  {
    CgnsSol vsol = cgz.newSolution("Node-based data", cgns::Vertex);
    for (uint i = 0; i < nfields(); ++i)
    {
      if (fields[i].nodal())
        fields[i].writeCgns(vsol);
    }
  }

  if (ncs > 0)
  {
    CgnsSol csol = cgz.newSolution("Cell-based data", cgns::CellCenter);
    for (uint i = 0; i < nfields(); ++i)
    {
      if (not fields[i].nodal())
        fields[i].writeCgns(csol);
    }
  }
}
