
#ifdef SINGLE
#define REAL float
#else /* not SINGLE */
#define REAL double
#endif /* not SINGLE */

#include "jrstrianglewrapper.h"
#include "triangle.h"
#include <genua/xcept.h>
#include <cstdlib>
#include <sstream>
#include <fstream>
#include <iostream>

using namespace std;

JrsTriangleWrapper::JrsTriangleWrapper() {}

JrsTriangleWrapper::~JrsTriangleWrapper()
{
  deallocate();
}

void JrsTriangleWrapper::allocate(const PointList2d &pts,
                                  const Indices &segments,
                                  const Indices &segmark,
                                  const PointList2d &holes)
{
  deallocate();

  m_in = new triangulateio;
  memset(m_in, 0, sizeof(triangulateio));

  m_in->numberofpoints = pts.size();
  m_in->pointlist = (double *) malloc(pts.size()*sizeof(Vct2));
  memcpy(m_in->pointlist, pts.pointer(), pts.size()*sizeof(Vct2));

  m_in->numberofsegments = segments.size() / 2;
  if (not segments.empty()) {
    m_in->segmentlist = (int *) malloc(segments.size()*sizeof(uint));
    memcpy(m_in->segmentlist, &segments[0], segments.size()*sizeof(uint));
    if (not segmark.empty()) {
      m_in->segmentmarkerlist = (int *) malloc(segmark.size()*sizeof(uint));
      memcpy(m_in->segmentmarkerlist, &segmark[0], segmark.size()*sizeof(uint));
    }
  }

  m_in->numberofholes = holes.size();
  if (not holes.empty()) {
    m_in->holelist = (double *) malloc(holes.size()*sizeof(Vct2));
    memcpy(m_in->holelist, holes.pointer(), holes.size()*sizeof(Vct2));
  }

  m_out = new triangulateio;
  memset(m_out, 0, sizeof(triangulateio));
}

void JrsTriangleWrapper::allocate(const PointList2d &pts,
                                  const Indices &segments,
                                  const Indices &segmark,
                                  const PointList2d &holes,
                                  const Indices &tri, const Vector &area)
{
  this->allocate(pts, segments, segmark, holes);

  m_in->numberoftriangles = tri.size() / 3;
  m_in->numberofcorners = 3;
  if (not tri.empty()) {
    m_in->trianglelist =  (int *) malloc(tri.size()*sizeof(uint));
    memcpy(m_in->trianglelist, &tri[0], tri.size()*sizeof(uint));
  }

  if (not area.empty()) {
    assert(area.size()*3 == tri.size());
    m_in->trianglearealist = (double *) malloc(area.size()*sizeof(double));
    memcpy(m_in->trianglearealist, area.pointer(), area.size()*sizeof(double));
  }
}

void JrsTriangleWrapper::deallocate()
{
  // these will be copied from m_in to m_out, hence only freed in m_in
  if (m_in != nullptr) {
    free(m_in->regionlist);
    free(m_in->holelist);
  }

  deallocate(m_in);
  m_in = nullptr;

  deallocate(m_out);
  m_out = nullptr;
}

int JrsTriangleWrapper::generate(const std::string &options)
{
  if (m_in == nullptr or m_out == nullptr)
    throw Error("Must initialize before calling generate().");
  if (options.find('v') != std::string::npos)
    throw Error("Voronoi diagram output not supported yet.");

  std::clog << "[i] Calling triangle: " << options << std::endl;
  triangulate(options.c_str(), m_in, m_out, 0);
  return m_out->numberoftriangles;
}

int JrsTriangleWrapper::generate(double minAngle, double maxArea,
                                 bool splitBoundaries, int maxSteinerPoints)
{
  std::stringstream ss;
  ss.precision(15);
  ss << std::fixed;
  ss << "p";
  if (minAngle > 0)
    ss << "q" << deg(minAngle);
  if (maxArea > 0)
    ss << "a" << maxArea;
  if (not splitBoundaries)
    ss << "YY";
  if (maxSteinerPoints > 0)
    ss << "S" << maxSteinerPoints;
  ss << "z";

  return generate(ss.str());
}

int JrsTriangleWrapper::refine(double minAngle, bool splitBoundaries,
                               int maxSteinerPoints)
{
  std::stringstream ss;
  ss.precision(15);
  ss << std::fixed;
  ss << "r";
  if (minAngle > 0)
    ss << "q" << deg(minAngle);
  ss << "a";
  if (not splitBoundaries)
    ss << "YY";
  if (maxSteinerPoints > 0)
    ss << "S" << maxSteinerPoints;
  ss << "z";

  return generate(ss.str());
}

void JrsTriangleWrapper::extract(PointList2d &pts, Indices &tri,
                                 Indices &segm, Indices &smark) const
{
  pts.clear();
  tri.clear();
  if (m_out == nullptr)
    return;

  pts.resize( m_out->numberofpoints );
  memcpy(pts.pointer(), m_out->pointlist, pts.size()*sizeof(Vct2));
  tri.resize(3*m_out->numberoftriangles);
  memcpy(&tri[0], m_out->trianglelist, tri.size()*sizeof(int));

  if (m_out->numberofsegments > 0 and m_out->segmentlist != nullptr) {
    segm.resize(2*m_out->numberofsegments);
    memcpy(&segm[0], m_out->segmentlist, segm.size()*sizeof(int));
    if ( m_out->segmentmarkerlist != nullptr ) {
      smark.resize(m_out->numberofsegments);
      memcpy(&smark[0], m_out->segmentmarkerlist, smark.size()*sizeof(int));
    }
  }
}

//void JrsTriangleWrapper::readBinary(const std::string &fname)
//{
//  ifstream in(fname);

//  uint64_t npoints(0), nsegments(0), ntriangles(0);
//  PointList2d pts;
//  Indices segments, tri;
//  Vector area;

//  in.read((char *) &npoints, 8);
//  if (in.good() and npoints > 0) {
//    pts.resize(npoints);
//    in.read((char *)pts.pointer(), npoints*sizeof(Vct2));
//  }

//  in.read((char *) &nsegments, 8);
//  if (in.good() and nsegments > 0) {
//    segments.resize(2*nsegments);
//    in.read((char *) &segments[0], 2*nsegments*sizeof(uint));
//  }

//  in.read((char *) &ntriangles, 8);
//  if (in.good() and ntriangles > 0) {
//    tri.resize(3*ntriangles);
//    in.read((char *) &tri[0], 3*ntriangles*sizeof(uint));
//    area.resize(ntriangles);
//    in.read((char *) area.pointer(), area.size()*sizeof(double));
//  } else {
//    allocate(pts, segments);
//    return;
//  }

//  PointList2d holes;
//  allocate(pts,segments, holes, tri, area);
//}

//void JrsTriangleWrapper::writeBinary(const string &fname)
//{
//  ofstream os(fname);

//  uint64_t npoints = m_out->numberofpoints;
//  uint64_t ntriangles = m_out->numberoftriangles;

//  os.write((const char *) &npoints, 8);
//  os.write((const char *) m_out->pointlist, 2*npoints*sizeof(double));
//  os.write((const char *) &ntriangles, 8);
//  os.write((const char *) m_out->trianglelist, 3*ntriangles*sizeof(int));
//}

void JrsTriangleWrapper::deallocate(triangulateio *io) const
{
  if (io == nullptr)
    return;

  // we rely on io being initialized to zero with memset
  free(io->pointlist);
  free(io->pointattributelist);
  free(io->pointmarkerlist);
  free(io->trianglelist);
  free(io->triangleattributelist);
  free(io->trianglearealist);
  free(io->neighborlist);
  free(io->segmentlist);
  free(io->segmentmarkerlist);
  free(io->edgelist);
  free(io->edgemarkerlist);
  free(io->normlist);
  delete io;
}
