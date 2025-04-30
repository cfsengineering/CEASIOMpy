
// test MxFieldBuffer

#include <iostream>
#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <genua/timing.h>
#include <genua/mxfieldbuffer.h>
#include <cstdlib>

using namespace std;

int main(int argc, char *argv[])
{
  Wallclock clk;

  try {

    const int np = 300;
    PointList<3> pts(np);
    for (int i=0; i<np; ++i)
      pts[i] = Vct3( M_PI*i+1, 10.0*i+2, 10.0*i+3 );
    const Real pabs = norm(pts.back());

    cout << "32-bit Buffer with LDA=3: " << endl;
    const string file1("pointlist3float.xml");
    {
      MxFieldBuffer fbo;
      fbo.assign( TypeCode::Float32, np, pts.pointer(), 3 ); // types diff, cannot share
      fbo.toXml(true).write(file1);
    }

    {
      XmlElement xe;
      xe.read(file1);

      MxFieldBuffer fb;
      fb.fromXml(xe);

      Vct3 p;
      for (int i=0; i<20; ++i) {
        int idx = rand() % 300;
        fb.extract(idx, p);
        Real err = norm(p - pts[idx])/pabs;
        if (err > 1e-6) {
          cout << "*** Error:" << err << " too large." << endl;
          return -1;
        }
        cout << idx << " Distance: " << err*pabs << endl;
      }
    }

    cout << "16-bit quantized buffer: " << endl;
    string file2("quantbuffer.xml");
    {
      MxFieldBuffer fb(true);
      fb.assign(TypeCode::Float64, np, pts.pointer(), 3, false);
      cout << "Offset: " << fb.quantOffset()
           << " Scale: " << fb.quantScale() << endl;
      cout << "QuInt range: " << std::numeric_limits<MxFieldBuffer::QuInt>::max() << endl;
      fb.toXml(true).write(file2);
    }
    {
      XmlElement xe;
      xe.read(file2);

      MxFieldBuffer fb;
      fb.fromXml(xe);
      cout << "Offset: " << fb.quantOffset()
           << " Scale: " << fb.quantScale() << endl;

      Vct3 p;
      for (int i=0; i<20; ++i) {
        int idx = rand() % 300;
        fb.extract(idx, p);
        cout << idx << " Distance: " << norm(p - pts[idx]) << endl;
      }
    }

    const int outer = 2048;
    DVector<double> x(np);
    Indices idx(np);
    for (int i=0; i<np; ++i) {
      x[i] = 34.5*rand() / RAND_MAX;
      idx[i] = 3*i;
    }

    string file3("sparsebuffer.xml");
    {
      MxFieldBuffer fb;
      fb.assign( TypeCode::Float32, np, &idx[0], x.pointer(), 1, false );
      fb.toXml(true).write(file3);
    }

    {
      XmlElement xe;
      xe.read(file3);

      MxFieldBuffer fb;
      fb.fromXml(xe);

      DVector<double> xfull(outer);
      fb.extract(xfull.pointer());
      for (int i=0; i<np; ++i) {
        double delta = fabs(xfull[idx[i]]-x[i]);
        cout << "Error at " << i << ", " << idx[i] << " : "<< delta << endl;
        assert(delta <= 1e-6*x[i]);
      }
      fb.toXml(true).write("sparsebuffer.xml");
    }


  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
