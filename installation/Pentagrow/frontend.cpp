#include "frontend.h"
#include <surf/tgrefiner.h>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <genua/configparser.h>
#include <genua/transformation.h>
#include <genua/cgnsfile.h>

#include <algorithm>
#include <iostream>
#include <fstream>
#include <cstdio>

// Modified by Cass
using namespace std;

void create_nearfield(const ConfigParser &cfg, const PentaGrow &pg,
                      TriMesh &nearf)
{
  nearf.clear();

  Real refinedRegionEdge = cfg.getFloat("NearfieldEdgeLength", 0.0);
  Real refinedRegionSize = cfg.getFloat("NearfieldSize", 3.5);
  if (refinedRegionEdge == 0.0)
    return;

  // if user gives a negative edge length, determine a reasonable
  // edge length from the envelope mesh edge lengths
  if (refinedRegionEdge < 0.0)
  {
    Real envlmax, envlmean;
    pg.envelopeEdgeStats(envlmean, envlmax);
    refinedRegionEdge = std::max(2 * envlmax, 8 * envlmean);
    cout << "[i] Suggested nearfield edge length: " << refinedRegionEdge << endl;
  }

  Vct3 ctr, hax;
  if (cfg.hasKey("NearfieldCenter"))
  {
    ctr = cfg.getVct3("NearfieldCenter");
    hax = cfg.getVct3("NearfieldSemiAxes");
  }
  else
  {
    Vct3 plo, phi;
    pg.envelopeBounds(plo, phi);
    hax = 0.5 * (phi - plo) * refinedRegionSize;
    ctr = 0.5 * (plo + phi);
  }
  cout << "[i] Nearfield region semi-axes: " << hax << endl;

  // check whether ellipsoid would intersect envelope
  if (not pg.ellipsoidEncloses(ctr, hax))
    throw Error("Nearfield ellipsoid does not enclose envelope mesh.");

  // approximate surface area of ellipsoid
  int refLevel(3);
  {
    const Real p(1.6075);
    Real a = std::pow(hax[0], p);
    Real b = std::pow(hax[1], p);
    Real c = std::pow(hax[2], p);
    Real sfa = pow((a * b + a * c + b * c) / 3.0, 1.0 / p);
    Real tla = 0.25 * std::sqrt(3.0) * sq(refinedRegionEdge);
    int ntriopt = sfa / tla;
    int ntrir = 1280;
    while (ntrir < ntriopt)
    {
      ++refLevel;
      ntrir *= 4;
    }
    refLevel = std::min(5, refLevel);
    cout << "[i] Using refinement level "
         << refLevel << " for nearfield boundary." << endl;
  }

  // create ellipsoid from center and half-axis dimensions
  nearf.sphere(Vct3(0.0, 0.0, 0.0), 1.0, refLevel);
  nearf.faceTag(PentaGrow::maximumTagValue() - 1);
  Mtx44 tfm;
  for (int k = 0; k < 3; ++k)
  {
    tfm(k, k) = hax[k];
    tfm(k, 3) = ctr[k];
  }
  tfm(3, 3) = 1.0;

  Trafo3d::transformList(tfm, nearf.vertices());
}

void smoothed_edgelength(Real xpf, int niter,
                         MxMesh &msh, Vector &ledg)
{
  Wallclock clk;

  ConnectMap map;
  clk.start("[t] Building node connectivity... ");
  msh.fixate();
  msh.v2vMap(map);
  clk.stop("[t] done: ");

  clk.start("[t] Distributing edge length field... ");

  size_t nv = msh.nnodes();
  if (ledg.size() != nv)
    ledg.resize(nv);

#pragma omp parallel for schedule(static, 1024)
  for (size_t i = 0; i < nv; ++i)
  {
    ConnectMap::const_iterator itr, last = map.end(i);
    int nnb = map.size(i);
    if (nnb > 1)
    {
      for (itr = map.begin(i); itr != last; ++itr)
        ledg[i] += norm(msh.node(*itr) - msh.node(i));
      ledg[i] /= (nnb - 1);
    }
  }

  Vector a(ledg), b(nv);
  for (int j = 0; j < niter; ++j)
  {

#pragma omp parallel for schedule(static, 1024)
    for (size_t i = 0; i < nv; ++i)
    {
      Real ai = a[i];
      b[i] = 0.5 * ai;
      ConnectMap::const_iterator itr, last = map.end(i);
      Real sum = 0;
      for (itr = map.begin(i); itr != last; ++itr)
        sum += std::min(ai, xpf * a[*itr]);
      b[i] += 0.5 * sum / map.size(i);
    }
    a.swap(b);
  }

  ledg.swap(a);

  clk.stop("[t] done: ");
}

// ----------------------------------------------------------------------

FrontEnd::FrontEnd(int argc, char *argv[])
{
  // extract configuration
  if (argc > 2)
  {
    ifstream in(argv[2]);
    m_cfg.read(in);
  }

  Real refinedRegionEdge = m_cfg.getFloat("NearfieldEdgeLength", 0.0);
  m_tgoDefault = (refinedRegionEdge > 0.0) ? ("-pq1.2a") : ("-pq1.2");

  Real edgeGrowthFactor = m_cfg.getFloat("TetGrowthFactor", 0.0);
  m_refinementPass = (edgeGrowthFactor != 0.0);
}

void FrontEnd::run(const std::string &fname)
{
  bool symmetry = m_cfg.getBool("Symmetry", false);
  Real y0 = m_cfg.getFloat("YPlaneCut", 0);

  // which phase to run (default is both)
  ProgPhase phase = TwoPass;
  string spass = toLower(m_cfg.value("Pass", "both"));

  if (spass == "first")
    phase = FirstPass;
  else if (spass == "second")
    phase = SecondPass;

  int iter = 1;
  if (phase & FirstPass)
  {
    generateBoundaries(fname, symmetry, y0);
    firstTetgenPass(symmetry, y0);
    iter = generateMetric(iter);
  }
  else if (m_refinementPass)
  {
    iter = 2;
  }

  if (phase & SecondPass)
  {
    if (m_refinementPass)
      secondTetgenPass();
    generateLayer(iter, symmetry, y0);

    writeFinal();
  }
}

void FrontEnd::generateBoundaries(const std::string &fname, bool symmetry, Real y0)
{
  Wallclock c;

  // check if format was specified in config file
  FileFormat frm = UnknownFormat;
  if (m_cfg.hasKey("InputFormat"))
  {
    string fmkey = toLower(m_cfg["InputFormat"]);
    if (fmkey == "msh")
      frm = MSH;
    else if (fmkey == "stl")
      frm = STL;
    else if (fmkey == "cgns")
      frm = CGNS;
    else if (fmkey == "zml")
      frm = ZML;
  }
  else
  {
    string sfx = filename_suffix(fname);
    if (sfx == "msh")
      frm = MSH;
    else if (sfx == "stl")
      frm = STL;
    else if (sfx == "cgns")
      frm = CGNS;
    else
      frm = ZML;
  }

  // read wall mesh
  TriMeshPtr pwall = boost::make_shared<TriMesh>();
  if (frm == STL)
  {
    pwall->readSTL(fname);
    pwall->cleanup();
  }
  else if (frm == CGNS or
           (frm == UnknownFormat and CgnsFile::isCgns(fname)))
  {
    pwall->readCgns(fname);
  }
  else if (frm == MSH)
  {
    XmlElement xe;
    xe.read(fname);
    if (xe.name() == "Triangulation")
    {
      pwall->fromXml(xe);
    }
    else
    {
      XmlElement::const_iterator ite;
      ite = xe.findChild("Triangulation");
      if (ite != xe.end())
        pwall->fromXml(*ite);
      else
        throw Error("No triangular wall mesh found in " + fname);
    }
  }
  else
  {
    MxMesh mx;
    mx.loadAny(fname);
    cout << "[i] Read MxMesh with " << mx.nelements() << " elements." << endl;
    pwall = mx.toTriMesh();
    pwall->cleanup(gmepsilon);
  }

  TriMesh &wall(*pwall);
  cout << "[i] Imported wall mesh with "
       << wall.nfaces() << " triangles." << endl;

  if (!symmetry)
  {
    if (not wall.isClosedManifold())
      throw Error("Wall mesh is not watertight.");
  }
  else
  {
    //cout << "There are " << wall.nvertices() << " vertices." << endl;
    uint tag, vertices[3];
    std::map<int, int> tag_sym_vertex;
    Vct3 symmetric_vertex;
    TriMesh duplicatewall(wall);
    for (uint i = 0; i < wall.nvertices(); i++)
    {
      if (wall.vertex(i)[1] > y0 + 0.0001)
      {
        symmetric_vertex = Vct3(wall.vertex(i)[0], -wall.vertex(i)[1], wall.vertex(i)[2]);
        tag = duplicatewall.addVertex(symmetric_vertex);
        tag_sym_vertex[i] = tag;
        if (i < 10)
        {
          cout << "Vtx " << i << " with coords " << wall.vertex(i) << " and new tag : " << tag << " and symmetric vertex is " << symmetric_vertex << endl;
        }
      }
      else
      {
        if (i < 10)
          cout << "Vtx " << i << " with coords " << wall.vertex(i) << " and in the middle " << endl;
        tag_sym_vertex[i] = i;
      }
    }
    for (uint i = 0; i < 10; i++)
    {
      cout << "Vtx that was added (normally) :" << duplicatewall.vertex(wall.nvertices() + i) << " tag is " << wall.nvertices() + i << " and corresponding tag in the map " << tag_sym_vertex[i] << endl;
    }
    for (uint i = 0; i < wall.nfaces(); i++)
    {
      if (i % 100000 == 0)
        cout << "Face " << i;
      TriFace &face(wall.face(i));
      face.getVertices(vertices);
      if (i % 100000 == 0)
        cout << " with vtces " << vertices << " (and nbs to test : " << vertices[0] << ", " << vertices[1] << ", " << vertices[2] << ")" << endl;
      duplicatewall.addFace(tag_sym_vertex[vertices[0]], tag_sym_vertex[vertices[2]], tag_sym_vertex[vertices[1]]);
    }
    cout << "Finished creating duplicate wall" << endl;
    duplicatewall.writeSTL("duplicated_mesh.stl");
    cout << "Done writing stl" << endl;
    // if (not duplicatewall.isClosedManifold())
    //   throw Error("Half-wall mesh is not watertight.");
  }
  uint hiter = m_cfg.getFloat("HeightIterations", 5);
  uint niter = m_cfg.getFloat("NormalIterations", 50);
  uint ncrititer = m_cfg.getFloat("MaxCritIterations", 99);
  uint laplaceiter = m_cfg.getFloat("LaplaceIterations", 5);

  m_pg = PentaGrow(wall);
  m_pg.configure(m_cfg);

  // erase original wall mesh here to reclaim memory
  wall = TriMesh();

  c.start("Generating shell... ");
  m_pg.generateShell(hiter, niter, ncrititer, laplaceiter, symmetry, y0);
  c.stop(" done. ");

#ifdef HAVE_NLOPT
  m_pg.optimizeEnvelope();
#endif

  m_pg.writeShell("outermost.zml");
}

void FrontEnd::firstTetgenPass(bool symmetry, Real y0)
{
  Wallclock c;

  Real farfieldRadius = m_cfg.getFloat("FarfieldRadius", 100.0);
  int farfieldRefinement = m_cfg.getInt("FarfieldSubdivision", 3);
  Real refinedRegionEdge = m_cfg.getFloat("NearfieldEdgeLength", 0.0);
  Real maxGlobalLength = m_cfg.getFloat("MaxGlobalEdgeLength", 0.0);
  string tgOptions = m_cfg.value("TetgenOptions", m_tgoDefault);

  if (maxGlobalLength > 0.0 and tgOptions.find('a') == string::npos)
  {
    Real mvol = 0.1 * cb(maxGlobalLength);
    stringstream ss;
    ss << "a" << fixed << mvol;
    tgOptions += ss.str();
  }

  uint maxSteinerPoints = m_cfg.getInt("MaxSteinerPoints", 0);
  if (maxSteinerPoints > 0)
    tgOptions += "S" + str(maxSteinerPoints);

  Vct3 holePos, farfCenter;
  PointList<3> holeList;
  if (m_cfg.hasKey("HolePosition"))
  {
    stringstream ss;
    ss << m_cfg["HolePosition"];
    Vct3 p;
    while (ss >> p)
      holeList.push_back(p);
    holePos = holeList.front();
  }
  farfCenter = m_cfg.getVct3("FarfieldCenter", holePos);

  // TODO: Use more advanced procedure to identify hole
  if (holeList.size() < 2)
    cout << "Using internal volume marker point: " << holePos << endl;
  else
    for (size_t i = 0; i < holeList.size(); ++i)
      cout << "Using internal volume marker point: " << holeList[i] << endl;

  // create farfield for tetgen call
  TriMesh farf;
  if (symmetry)
  {
    farf.semisphere(farfCenter, farfieldRadius, farfieldRefinement);
    farf.faceTag(PentaGrow::maximumTagValue());
    farf.reverse();
    farf.addyplane(m_pg.getouterlayeryplane_ordered(y0), y0);
    // farf.addyplane(m_pg.getouterlayer(), y0);
    farf.writeSTL("test_semisphere_with_yplane_andnormals.stl");
  }
  else
  {
    farf.sphere(farfCenter, farfieldRadius, farfieldRefinement);
    farf.faceTag(PentaGrow::maximumTagValue());
    farf.reverse();
    farf.writeSTL("test_sphere.stl");
  }

  // create refinement region boundary
  TriMesh nearf;
  if (refinedRegionEdge > 0.0)
    create_nearfield(m_cfg, m_pg, nearf);

  c.start("Writing .smesh file for tetgen... ");
  if (refinedRegionEdge > 0.0)
    m_pg.writeTetgen("boundaries.smesh", farf, holeList,
                     nearf, refinedRegionEdge);
  else
    m_pg.writeTetgen("boundaries.smesh", farf, holeList, nearf, 0, symmetry);
  c.stop(" done. ");

  if (refinedRegionEdge > 0.0 and tgOptions.find('a') == string::npos)
    cout << "Warning: Tetgen will not refine nearfield, add 'a' to call." << endl;

  string cmd = "tetgen";
  if (m_cfg.hasKey("TetgenPath"))
    cmd = m_cfg["TetgenPath"];

  string tgCall = cmd + ' ' + tgOptions + " boundaries.smesh";
  c.start("Calling: " + tgCall + "\n");
  int stat = system(tgCall.c_str());
  if (stat != 0)
    throw Error("Call to tetgen failed.");
  c.stop(" done. ");
}

int FrontEnd::generateMetric(int iter)
{
  Wallclock c;
  Real edgeGrowthFactor = m_cfg.getFloat("TetGrowthFactor", 0.0);
  // optional tetgen refinement pass
  string tgOutBasename("boundaries");
  string tgInfile = tgOutBasename + '.' + str(iter) + '.';
  // string tgOutfile = tgOutBasename + '.' + str(iter+1) + '.';
  string mtrfile = append_suffix(tgInfile, ".mtr");

  // make sure to delete metric file in any case
  remove(mtrfile.c_str());

  if (edgeGrowthFactor > 1.0)
  {
    if (edgeGrowthFactor < 1.21)
      cout << "[w] Tet growth factor very small." << endl;
    else if (edgeGrowthFactor > 1.6)
      cout << "[w] Tet growth factor very large." << endl;

    c.start("[t] Reading 1st pass tetgen files... ");
    MxMesh tmsh;
    DVector<uint> ftags;
    tmsh.readTetgen(tgInfile, &ftags);
    c.stop("[t] done: ");

    c.start("[t] Computing desired edge lengths...");
    TgRefiner tgr;
    tgr.configure(m_cfg);
    const Vector &tel = tgr.edgeLengths(tmsh);

    // debug
    tmsh.appendField("TargetEdgeLengths", tel);
    tmsh.writeAs("firstpass.zml", Mx::NativeFormat, 1);

    tgr.writeMetricFile(mtrfile);
    c.stop("[t] done: ");

    return iter + 1;
  }
  else
  {
    return iter;
  }
}

void FrontEnd::secondTetgenPass(int iter)
{
  Wallclock c;
  string tgOutBasename("boundaries");
  string rpOptions = " -rqmY";
  string tgOptions = m_cfg.value("TetgenOptions", m_tgoDefault);
  if (tgOptions.find("V") != string::npos)
    rpOptions += "V";

  uint maxSteinerPoints = m_cfg.getInt("MaxSteinerPoints", 0);
  if (maxSteinerPoints > 0)
    rpOptions += "S" + str(maxSteinerPoints);

  string cmd = "tetgen";
  if (m_cfg.hasKey("TetgenPath"))
    cmd = m_cfg["TetgenPath"];
  string tgCall = cmd + rpOptions + ' ' + tgOutBasename + '.' + str(iter);
  c.start("Calling: " + tgCall + "\n");
  int stat = system(tgCall.c_str());
  if (stat != 0)
    throw Error("Call to tetgen failed.");
  c.stop(" done. ");
}

void FrontEnd::generateLayer(int iter, bool symmetry, Real y0)
{
  Wallclock c;
  bool spline = m_cfg.getBool("SplineNormals", false);

  string tgOutBasename("boundaries");
  tgOutBasename += '.' + str(iter) + '.';

  // reread tet mesh from tetgen results file
  c.start("Reading tet mesh and adapting wall...");
  m_pg.clear();
  m_pg.readTets(tgOutBasename);
  c.stop(" done. ");
  c.start("Extrusion... ");
  uint prismSection = m_pg.extrude(spline, symmetry, y0);
  c.stop(" done. ");

  // write prism quality to file
  m_pg.prismQualitySumCos("sumcos.txt", prismSection, 15);

  // reduce memory footprint - do not call anything from PentaGrow interface
  // after this point (only inherited MxMesh member functions).
  m_pg.shrink();

  c.start("Merging nodes... ");
  int ndp = m_pg.mergeNodes(gmepsilon);
  c.stop(" done.");

  cout << "Merged " << ndp << " duplicate nodes." << endl;
  cout << "Final mesh has " << m_pg.nnodes() << " nodes." << endl;

  c.start("Performing mesh diagnosis... ");
  string diagFile("diagnose.txt");
  ofstream diag(diagFile.c_str());
  size_t nneg = m_pg.countNegativeVolumes(diag);
  if (nneg > 0)
  {
    if (nneg >= 4096)
      cout << "[!] Extremely many tangled volume elements detected. List in "
           << diagFile << endl;
    else
      cout << "[!] " << nneg << " tangled volume elements detected. List in "
           << diagFile << endl;
    if (spline)
      cout << "[!] Consider disable bent normals (SplineNormals = false) "
              "to avoid tangled elements."
           << endl;
  }
  c.stop(" diagnosis finished.");
}

void FrontEnd::writeFinal()
{
  // check requested output formats
  int outFormat = 0;
  if (m_cfg.hasKey("OutputFormat"))
  {
    string of = toLower(m_cfg["OutputFormat"]);
    if (of.find("edge") != string::npos)
      outFormat |= EDGE;
    if (of.find("bmsh") != string::npos)
      outFormat |= EDGE;
    if (of.find("zml") != string::npos)
      outFormat |= ZML;
    if (of.find("native") != string::npos)
      outFormat |= ZML;
    if (of.find("cgns") != string::npos)
      outFormat |= CGNS;
    if (of.find("tau") != string::npos)
      outFormat |= TAU;
    if (of.find("su2") != string::npos)
      outFormat |= SU2;
  }
  else
  {
    outFormat = EDGE | ZML;
  }

  Wallclock c;
  string outbase("hybrid");

  if (outFormat & ZML)
  {
    c.start("Writing final mesh... ");
    m_pg.writeAs(outbase, Mx::NativeFormat, 1);
    c.stop(" done. ");
  }

  if (outFormat & EDGE)
  {
    c.start("Writing final ffa mesh... ");
    m_pg.writeAs(outbase, Mx::FfaFormat, 0);
    c.stop(" done. ");
  }

  if (outFormat & CGNS)
  {
    c.start("Writing final cgns mesh... ");
    m_pg.writeAs(outbase, Mx::StdCgnsFormat, 0);
    c.stop(" done. ");
  }

  if (outFormat & TAU)
  {
    c.start("Writing final TAU mesh... ");
    m_pg.writeAs(outbase, Mx::TauFormat, 0);
    c.stop(" done. ");
  }

  if (outFormat & SU2)
  {
    c.start("Writing final SU2 mesh... ");
    m_pg.writeAs(outbase, Mx::Su2Format, 0);
    c.stop(" done. ");
  }
}
