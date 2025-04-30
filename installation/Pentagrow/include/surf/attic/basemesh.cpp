
/* ------------------------------------------------------------------------
 * project:    Surf
 * file:       basemesh.cpp
 * begin:      Feb 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * refactored interface to Shewchuk's triangle.c
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */

#include <string>
#include <sstream>

#include "triangle.h"
#include "triquality.h"
#include "basemesh.h"

using namespace std;

void BaseMesh::addConstraint(const PointList<2> & c)
{
  uint first = ppt.size();
  if (norm(c.front()-c.back()) < gmepsilon) {
    for (uint i=0; i<c.size()-1; ++i)
      ppt.push_back(c[i]);
    for (uint i=0; i<c.size()-2; ++i)
      con.push_back(BmEdge(first+i, first+i+1));
    uint last = ppt.size() - 1;
    con.push_back(BmEdge(last,first));
  }
  else {
    for (uint i=0; i<c.size(); ++i)
      ppt.push_back(c[i]);
    for (uint i=0; i<c.size()-1; ++i)
      con.push_back(BmEdge(first+i, first+i+1));
  }
}

void BaseMesh::addHoleMarker(const Vct2 & hp)
{
  holes.push_back(hp);
}

void BaseMesh::clear()
{
  ppt.clear();
  faces.clear();
  con.clear();
  holes.clear();
}

void BaseMesh::writeOogl(ostream & os) const
{
  os << "{ OFF" << endl;
  os << ppt.size() << " " << faces.size() << " 1" << endl;
  for (uint i=0; i<ppt.size(); ++i)
    os << ppt[i] << " 0" << endl;
  for (uint i=0; i<faces.size(); ++i)
    os << "3 " << faces[i].v[0] << " "
       << faces[i].v[1] << " " << faces[i].v[2] << endl;
  os << "}" << endl;
}

uint BaseMesh::generate(Real maxarea, Real minangle)
{
  // arrays passed to triangulate()
  std::vector<double> points, hlpoints;
  std::vector<int> conseg;

  // fill buffers
  points.reserve(2*ppt.size());
  for (uint i=0; i<ppt.size(); ++i) {
    points.push_back(ppt[i][0]);
    points.push_back(ppt[i][1]);
  }
  hlpoints.reserve(holes.size());
  for (uint i=0; i<holes.size(); ++i) {
    hlpoints.push_back(holes[i][0]);
    hlpoints.push_back(holes[i][1]);
  }
  conseg.reserve(2*con.size());
  for (uint i=0; i<con.size(); ++i) {
    conseg.push_back((int) con[i].src);
    conseg.push_back((int) con[i].trg);
  }

  // construct flags
  stringstream sst;
  sst.precision(18);
  sst.setf(ios_base::fixed);
	sst << "pzq" << minangle;
  #ifdef NDEBUG
  sst << "YYQ";
  #endif
	sst << "a" << maxarea;
  string tflag(sst.str());

  // debug
  cout << "Triangle flags: " << tflag << endl;

  // lengthy initialization
  struct triangulateio in, out;
  in.pointlist = &(points[0]);
  in.pointattributelist = 0;
  in.pointmarkerlist = 0;
  in.numberofpoints = ppt.size();
  in.numberofpointattributes = 0;
  in.trianglelist = 0;
  in.triangleattributelist = 0;
  in.trianglearealist = 0;
  in.neighborlist = 0;
  in.numberoftriangles = 0;
  in.numberofcorners = 3;
  in.numberoftriangleattributes = 0;
  in.segmentlist = &(conseg[0]);
  in.segmentmarkerlist = 0;
  in.numberofsegments = con.size();
  if (!holes.empty())
    in.holelist = &(hlpoints[0]);
  else
    in.holelist = 0;

  in.numberofholes = holes.size();
  in.regionlist = 0;
  in.numberofregions = 0;
  in.edgelist = 0;
  in.edgemarkerlist = 0;
  in.normlist = 0;
  in.numberofedges = 0;

  out.pointlist = 0;
  out.pointattributelist = 0;
  out.pointmarkerlist = 0;
  out.numberofpoints = 0;
  out.numberofpointattributes = 0;
  out.trianglelist = 0;
  out.triangleattributelist = 0;
  out.trianglearealist = 0;
  out.neighborlist = 0;
  out.numberoftriangles = 0;
  out.numberofcorners = 0;
  out.numberoftriangleattributes = 0;
  out.segmentlist = 0;
  out.segmentmarkerlist = 0;
  out.numberofsegments = 0;
  out.holelist = 0;
  out.numberofholes = 0;
  out.regionlist = 0;
  out.numberofregions = 0;
  out.edgelist = 0;
  out.edgemarkerlist = 0;
  out.normlist = 0;
  out.numberofedges = 0;

  ::triangulate(tflag.c_str(), &in, &out, 0);

  // interpret output
  clear();
  ppt.resize(out.numberofpoints);
  for (uint i=0; i<ppt.size(); i++) {
    ppt[i][0] = out.pointlist[2*i];
    ppt[i][1] = out.pointlist[2*i+1];
  }

  uint red, green, blue;
  for (uint i=0; i<uint(out.numberoftriangles); i++) {
    red = out.trianglelist[3*i];
    green = out.trianglelist[3*i+1];
    blue = out.trianglelist[3*i+2];
    faces.push_back(BmFace(red, green, blue));
  }

  free(out.pointlist);
  free(out.trianglelist);
  free(out.segmentlist);

  return faces.size();
}

uint BaseMesh::generate(TriQuality & f, Real maxarea, Real minangle)
{
  // set pointer to quality acceptance functor
	assert(triq::tq == 0);
	triq::tq = &f;

  // arrays passed to triangulate()
  std::vector<double> points, hlpoints;
  std::vector<int> conseg;

  // fill buffers
  points.reserve(2*ppt.size());
  for (uint i=0; i<ppt.size(); ++i) {
    points.push_back(ppt[i][0]);
    points.push_back(ppt[i][1]);
  }
  hlpoints.reserve(holes.size());
  for (uint i=0; i<holes.size(); ++i) {
    hlpoints.push_back(holes[i][0]);
    hlpoints.push_back(holes[i][1]);
  }
  conseg.reserve(2*con.size());
  for (uint i=0; i<con.size(); ++i) {
    conseg.push_back((int) con[i].src);
    conseg.push_back((int) con[i].trg);
  }

  // construct flags
  stringstream sst;
	sst.precision(18);
  sst.setf(ios_base::fixed);
	sst << "pzuq" << minangle << "a" << maxarea << endl;
  #ifdef NDEBUG
  sst << "YYQ";
  #endif
  string tflag(sst.str());

  // debug
  cout << "Triangle flags: " << tflag << endl;

  // lengthy initialization
  struct triangulateio in, out;
  in.pointlist = &(points[0]);
  in.pointattributelist = 0;
  in.pointmarkerlist = 0;
  in.numberofpoints = ppt.size();
  in.numberofpointattributes = 0;
  in.trianglelist = 0;
  in.triangleattributelist = 0;
  in.trianglearealist = 0;
  in.neighborlist = 0;
  in.numberoftriangles = 0;
  in.numberofcorners = 3;
  in.numberoftriangleattributes = 0;
  in.segmentlist = &(conseg[0]);
  in.segmentmarkerlist = 0;
  in.numberofsegments = con.size();
  if (!holes.empty())
    in.holelist = &(hlpoints[0]);
  else
    in.holelist = 0;

  in.numberofholes = holes.size();
  in.regionlist = 0;
  in.numberofregions = 0;
  in.edgelist = 0;
  in.edgemarkerlist = 0;
  in.normlist = 0;
  in.numberofedges = 0;

  out.pointlist = 0;
  out.pointattributelist = 0;
  out.pointmarkerlist = 0;
  out.numberofpoints = 0;
  out.numberofpointattributes = 0;
  out.trianglelist = 0;
  out.triangleattributelist = 0;
  out.trianglearealist = 0;
  out.neighborlist = 0;
  out.numberoftriangles = 0;
  out.numberofcorners = 0;
  out.numberoftriangleattributes = 0;
  out.segmentlist = 0;
  out.segmentmarkerlist = 0;
  out.numberofsegments = 0;
  out.holelist = 0;
  out.numberofholes = 0;
  out.regionlist = 0;
  out.numberofregions = 0;
  out.edgelist = 0;
  out.edgemarkerlist = 0;
  out.normlist = 0;
  out.numberofedges = 0;

  ::triangulate(tflag.c_str(), &in, &out, 0);

  // interpret output
  clear();
  ppt.resize(out.numberofpoints);
  for (uint i=0; i<ppt.size(); i++) {
    ppt[i][0] = out.pointlist[2*i];
    ppt[i][1] = out.pointlist[2*i+1];
  }

  uint red, green, blue;
  for (uint i=0; i<uint(out.numberoftriangles); i++) {
    red = out.trianglelist[3*i];
    green = out.trianglelist[3*i+1];
    blue = out.trianglelist[3*i+2];
    faces.push_back(BmFace(red, green, blue));
  }

  free(out.pointlist);
  free(out.trianglelist);
  free(out.segmentlist);
	triq::tq = 0;

  return faces.size();
}

