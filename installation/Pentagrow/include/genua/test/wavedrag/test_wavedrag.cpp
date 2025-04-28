
#include <genua/mxmesh.h>
#include <genua/trimesh.h>
#include <genua/timing.h>
#include <genua/xcept.h>
#include <genua/volwavedrag.h>

#include <iostream>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{
  if (argc < 3 or argc > 4) {
    cerr << "Usage: " << argv[0] << " areaDistribution.txt Sref" << endl;
    cerr << "Usage: " << argv[0] << " surfaceMesh.xml Sref [Mach]" << endl;
    return -1;
  }

  try {

    Real Sref(1.0);
    fromString(argv[2], Sref);

    Real Mach(1.0);
    if (argc > 3)
      fromString(argv[3], Mach);

    Wallclock clk;

    string fname(argv[1]);
    if (fname.find(".xml") != string::npos) {

      XmlElement xe;
      xe.read(fname);

      TriMesh tm;
      tm.fromXml(xe);

      Vector x, S;

      clk.start();
      VolWaveDrag vwd(tm);
      clk.stop();
      cout << "Initialization: " << clk.elapsed() << endl;

      clk.start();
      Vct3 pn(1.0, 0.0, 0.0);
      // vwd.areaDistribution(pn, 100, x, S);
      vwd.meanAreaDistribution(pn, Mach, 100, 32, x, S);
      clk.stop();
      cout << "Area distribution: " << clk.elapsed() << endl;

      clk.start();
      Real cdw = VolWaveDrag::dragCoefficient(Sref, x, S);
      cout << "Sref = " << Sref << " CDw = " << cdw << endl;
      clk.stop();
      cout << "Coefficient integration: " << clk.elapsed() << endl;

      ofstream os("areaDistribution.txt");
      const int n = x.size();
      for (int i=0; i<n; ++i)
        os << x[i] << " " << S[i] << endl;

    } else {

      ifstream in(argv[1]);
      Real x, s;
      Vector xx, ss;
      while (in >> x >> s) {
        xx.push_back(x);
        ss.push_back(s);
      }

      Real cdw = VolWaveDrag::dragCoefficient(Sref, xx, ss);
      cout << "Sref = " << Sref << " CDw = " << cdw << endl;

    }

  } catch (Error & xcp) {
    cerr << xcp.what();
    return -1;
  }

  return 0;
}
