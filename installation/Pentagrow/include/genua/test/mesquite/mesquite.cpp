
// test mesquite interface

#include "Mesquite_all_headers.hpp"

#include <iostream>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <genua/timing.h>
#include <genua/mxmsqadapter.h>
#include <cstdlib>

using namespace std;
using namespace Mesquite;

void vtk_improve(const std::string &fname)
{
  // directly from mesquite tutorial
  MsqError err;
  Mesquite::MeshImpl my_mesh;
  my_mesh.read_vtk(fname.c_str(), err);
  if (err) {
    std::cout << err << std::endl;
    exit( EXIT_FAILURE );
  }

  // my_mesh.write_vtk("original_mesh.vtk",err);

  Mesquite::ShapeImprover mesh_quality_algorithm;
  mesh_quality_algorithm.run_instructions(&my_mesh, err);
  if (err) {
    std::cout << err << std::endl;
    exit( EXIT_FAILURE );
  }

  my_mesh.write_vtk("smoothed_mesh.vtk",err);
}

void improve_section(MxMeshPtr pmx, uint isec)
{
  Wallclock clk;
  clk.start();
  MxMsqSectionAdapter sadp(pmx, isec);
  clk.stop();
  cout << "Created adapter: " << clk.elapsed() << endl;

  MsqError err;
  ShapeImprover mqa;
  // UntangleWrapper mqa;
  mqa.set_cpu_time_limit(300.0);
  mqa.set_parallel_iterations(100);
  mqa.set_vertex_movement_limit_factor(0.0001);
  //mqa.set_iteration_limit(8);
  // mqa.set_vertex_movement_limit_factor(0.25);
  mqa.run_instructions(&sadp, err);

  if (err) {
    std::cout << err << std::endl;
    exit(EXIT_FAILURE);
  }
}

int main(int argc, char *argv[])
{
  Wallclock clk;

  try {

    if (argc != 2) {
      cerr << "Usage: " << argv[0] << " mesh.[zml|cgns|bmsh]" << endl;
      return EXIT_FAILURE;
    }

    if (strstr(argv[1], ".vtk") != 0) {
      vtk_improve(argv[1]);
      return EXIT_SUCCESS;
    }

    clk.start();
    cout << "Reading mesh from " << argv[1] << endl;
    MxMeshPtr pmx = boost::make_shared<MxMesh>();
    if (not pmx->loadAny(argv[1])) {
      cerr << "Cannot load mesh, format not recognized." << endl;
      return EXIT_FAILURE;
    }
    clk.stop();
    cout << "Mesh read time: " << clk.elapsed() << endl;

    for (uint i=0; i<pmx->nsections(); ++i) {
      if (pmx->section(i).elementType() == Mx::Tet4)
        improve_section(pmx, i);
    }

    /*

    clk.start();
    MxMsqAdapter adp;
    adp.assign(pmx);
    clk.stop();
    cout << "Created adapter: " << clk.elapsed() << endl;

    MsqError err;

//    QualityAssessor qa;
//    IdealWeightInverseMeanRatio metric;
//    // qa.tag_inverted_elements("InvertedElements");
//    qa.add_quality_assessment(&metric, 0, 0.0, "InverseMeanRatio", "InverseMeanRatio");

//    InstructionQueue iq;
//    iq.add_quality_assessor(&qa, err);
//    iq.run_instructions(&adp, err);

    ShapeImprover mqa;
    // UntangleWrapper mqa;
    mqa.set_cpu_time_limit(300.0);
    mqa.set_parallel_iterations(100);
    mqa.set_vertex_movement_limit_factor(0.0001);
    //mqa.set_iteration_limit(8);
    // mqa.set_vertex_movement_limit_factor(0.25);
    mqa.run_instructions(&adp, err);

    if (err) {
      std::cout << err << std::endl;
      return EXIT_FAILURE;
    }

    // ???
    // tag not found error reported

//    // find tag for quality metric
//    TagHandle tag = adp.tag_get("InverseMeanRatio", err);
//    if (err)
//      cerr << err << endl;
//    if (tag != 0) {
//      std::vector<Mesh::ElementHandle> hdl;
//      adp.get_all_elements(hdl, err);
//      Vector eq( hdl.size() );
//      adp.tag_get_element_data(tag, hdl.size(), &hdl[0], eq.pointer(), err);
//      if (err)
//        cerr << err << endl;
//    } else {
//      cerr << "Element quality tag not found." << endl;
//    }

    */

    BinFileNodePtr bfp;
    bfp = pmx->toXml(true).toGbf(true);
    bfp->write("improved.zml", BinFileNode::CompressedLZ4);

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return EXIT_SUCCESS;
}
