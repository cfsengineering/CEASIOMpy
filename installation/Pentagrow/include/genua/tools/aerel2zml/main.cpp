
#include <genua/point.h>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <genua/mxsolutiontree.h>
#include <iostream>
#include <fstream>
#include <sstream>

using namespace std;

void plocka5(const std::string &line, std::vector<double> &val)
{
  stringstream mode_p1(line);
  for (int k=0; k<5; ++k) {
    double u;
    mode_p1 >> u;
    for(int uu=0; uu<4; ++uu)
      val.push_back(u);
  }
}

void plocka5(const std::string &line, DVector<double> &val)
{
  stringstream mode_p1(line);
  for (int k=0; k<5; ++k) {
    double u;
    mode_p1 >> u;
    for(int uu=0; uu<4; ++uu)
      val.push_back(u);
  }
}

bool is_this_empty(const std::string &s)
{
  if (s.empty())
    return true;

  for (size_t i=0; i<s.size(); ++i){
    if ( !isspace( s[i] ) ) {
      return false;
    }
  }

  return true;
}

bool is_this_mode(const std::string &s)
{
  if (s.empty())
    return false;

  if (s.find("Mode") != string::npos ){
    return true;
  }

  return false;
}

int main(int argc, char *argv[])
{

  if (argc < 3) {
    cerr << "Usage: " << argv[0] << " aerel_plot.dat scope_file.zml" << endl;
    return EXIT_FAILURE;
  }

  // test integration
  try {
    MxMesh mx;
    mx.readAerel(argv[1]);
    // mx.loadAny(argv[1]);
    BinFileNodePtr bfp = mx.toXml(true).toGbf(true);
    bfp->write(argv[2], BinFileNode::CompressedLZ4);
    cout << "Finished!" << endl;
  } catch (Error &xcp) {
    cerr << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  /*

  int modenum=0; // mode number
  DVector<double> xyz_modes;
  PointList<3> mode;
  double mnm=0; // mode number for mode (displacement)

  try {

    // the mesh for scope
    MxMesh mx;
    MxSolutionTreePtr root = boost::make_shared<MxSolutionTree>("Subcases");
    MxSolutionTreePtr subcase;
    MxSolutionTreePtr subcase_modes;

    int npanels, nmodes;

    // vertices of quad element
    Vct3 pts[4];

    // all quad indices
    Indices quads;
    PointList<3> modes;

    DVector<double> rcp_values;
    DVector<double> icp_values;

    vector< PointList<3> > k_modes;
    vector< DVector<double> > k_rcp;
    vector< DVector<double> > k_icp;

    // read AEREL plot file line by line
    string line;
    ifstream in(argv[1]);
    if(!in) { // file could not be opened
      cout << "Error: file could not be opened" << endl;
      exit(1);
    }

    while (getline(in, line)) {

      if (line.find("Number of panels, and number of modes") != string::npos) {
        getline(in, line);
        stringstream ss(line);
        ss >> npanels >> nmodes;
      } // end: (line.find("Number of panels, and number of modes") != string::npos)

      // read points for one element

      if (line.find("Element") != string::npos) {

        for (int k=0; k<3; ++k) {
          getline(in, line);
          stringstream coord(line);
          coord >> pts[0][k] >> pts[1][k] >> pts[2][k] >> pts[3][k];
        }

        // assume we have all 4 here; add nodes to mesh and remember indices
        for (int k=0; k<4; ++k){
          quads.push_back( mx.appendNode(pts[k]) );
        }

      }  // end: (line.find("Element") != string::npos)

      // ///////////////////////////////////////

      // read modeshapes ...

      vector<double> u_points; // for panel 1

      int pn=0;
      for(int ii=0; ii<(npanels); ++ii){
        ++pn;
        std::stringstream ss;
        ss << "on panel  " << pn;
        string s = ss.str();
        if (line.find(s) != string::npos) {
          //cout << s << endl;
          ++mnm;
          getline(in, line);
          while(!is_this_mode(line) and !is_this_empty(line)){
            plocka5(line, u_points);
            getline(in, line);
          } // (!is_this_empty(line))

        } // (line.find(s) != string::npos)
      }

      if(!u_points.empty()){
        ++modenum;
        int ndz;
        ndz=u_points.size();

        double dx=0.0, dy=0.0, dz;
        mode.clear();

        for(int nn=0; nn<ndz; ++nn){
          dz=u_points[nn];
          mode.push_back( Vct3(dx, dy, dz));
        }

        k_modes.push_back(mode);
      } // (!u_points.empty()

      // ///////////////////////////////////////

      // Real and imaginary parts for panels follow eachother in the input file

      int panelnr;
      int modenr;
      double machnr;
      double freq;
      subcase = boost::make_shared<MxSolutionTree>("Reduced freq. "+str(freq));

      // Panels
      if (line.find("Real DCP") != string::npos) {

        getline(in, line);
        stringstream rcp_info(line);
        rcp_info >> panelnr >> modenr >> machnr >> freq;

        if(panelnr<2){
          rcp_values.clear();
          icp_values.clear();
        }

        getline(in, line);

        while(!is_this_empty(line)){ // until an empty line is reached
          plocka5(line, rcp_values);
          getline(in, line);
        } // (!is_this_empty(line))

        if(panelnr>(npanels-1)){
          k_rcp.push_back(rcp_values);
          //
        }

      } // (line.find("Real DCP") != string::npos)

      // :::::::::::::::::::::::::::::::::::::::::::::

      if(line.find("Imag DCP") != string::npos){
        getline(in, line);
        getline(in, line);

        while(!is_this_empty(line)){
          plocka5(line, icp_values);
          getline(in, line);
        } // (!is_this_empty(line))

        if(panelnr>(npanels-1)){
          k_icp.push_back(icp_values);
        }

        if(panelnr>(npanels-1) and modenr>(nmodes-1)){
          assert(subcase != nullptr);
          root->append(subcase);
          for(int ii=0; ii<nmodes; ++ii){
            std::stringstream ss;
            ss << "Mode nr: " << ii+1 << " , k = " << freq;
            string s = ss.str();
            uint ire = mx.appendField("ReDCp: "+s, k_rcp[ii]);
            subcase->appendField(ire);
            uint iim = mx.appendField("ImDCp: "+s, k_icp[ii]);
            subcase->appendField(iim);
          }
          k_icp.clear();
          k_rcp.clear();
        }

      } // (line.find("Imag DCP") != string::npos)

    } // (getline(in, line))

    // gathered all elements ? create a mesh section
    uint isec = mx.appendSection(Mx::Quad4, quads);
    mx.section(isec).rename("AerelElements");

    // modes
    //        int mode_nr_now;
    subcase_modes = boost::make_shared<MxSolutionTree>("Modes");
    root->append(subcase_modes);
    for(int ii=0; ii<nmodes; ++ii){
      uint imodes =mx.appendField("Mode "+str(ii+1), k_modes[ii]);
      subcase_modes->appendField(imodes);
    }

    // in the end, write mx to file

    mx.solutionTree(root);
    BinFileNodePtr bfp = mx.toXml(true).toGbf(true);
    bfp->write(argv[2], BinFileNode::CompressedLZ4);

    cout << "Finished!" << endl;

  } catch (Error &xcp) {

    cerr << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  */
  return EXIT_SUCCESS;
}

