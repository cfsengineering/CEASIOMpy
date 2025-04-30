
#include "lpstransform.h"
#include <genua/xcept.h>
#include <genua/ffanode.h>
#include <genua/timing.h>
#include <genua/mxmesh.h>
#include <genua/binfilenode.h>
#include <genua/configparser.h>
#include <genua/ioglue.h>
#include <iostream>

using namespace std;

static void transform_files(const StringArray &romfiles,
                            const StringArray &outfiles,
                            ModalStepImporter &lps,
                            MxMesh &mx)
{
  assert(romfiles.size() == outfiles.size());

  Wallclock clk;
  FFANodePtr pfile = boost::make_shared<FFANode>();
  const size_t n = romfiles.size();
  for (size_t i=0; i<n; ++i) {

    // read .brom file for parameter data
    pfile->read( romfiles[i] );
    lps.loadRomParameter(pfile);

    // read big sampling data file
    clk.start("[i] Reading FFA file: "+outfiles[i]);
    pfile->read( outfiles[i] );
    clk.stop("[t] Completed: ");

    clk.start("[i] Importing pressure data...");
    lps.loadSampling(pfile, "pressure");
    clk.stop("[t] Completed: ");

    lps.transform();
    lps.appendFields(mx);
  }
}

static void debug_transform(uint ntime, uint ny,
                            const std::string &filename,
                            Real df, Real fmax)
{
  // read time, x(t) and y(t) columns from text file
  Vector time(ntime), xt(ntime);
  Matrix yt(ntime, ny);

  ifstream in(filename.c_str());
  for (size_t i=0; i<ntime; ++i) {
    in >> time[i] >> xt[i];
    for (size_t j=0; j<ny; ++j)
      in >> yt(i,j);
  }

  StepTransform trafo;
  trafo.transform(time[1]-time[0], df, fmax, xt, yt);
  const CpxMatrix & ys( trafo.result() );

  const size_t nf = ys.nrows();
  ofstream os( ("out_" + filename).c_str() );
  for (size_t i=0; i<nf; ++i) {
    os << trafo.laplaceVariable(i).imag() << ' ';
    for (size_t j=0; j<ny; ++j)
      os << ys(i,j).real() << ' ' << ys(i,j).imag() << ' ';
    os << endl;
  }
}

int main(int argc, char *argv[])
{
  try {

    if (argc < 2 or argc > 3) {
      cerr << "Usage: " << argv[0] << " config.txt [meshfile] " << endl;
      return EXIT_FAILURE;
    }

    ConfigParser cfg(argv[1]);
    if (cfg.hasKey("ValidationInput")) {
      Real df = cfg.getFloat("FrequencyStep");
      Real fmax = cfg.getFloat("MaxOutFrequency");
      uint ntime = cfg.getInt("SampleCount");
      uint ny = cfg.getInt("ChannelCount");
      debug_transform(ntime, ny,
                      cfg["ValidationInput"], df, fmax);
      return EXIT_SUCCESS;
    }

    string meshfile;
    if (argc > 2)
      meshfile = argv[2];
    else
      meshfile = cfg["MeshFile"];

    MxMesh mx;
    mx.loadAny(meshfile);

    ModalStepImporter lps;
    lps.configure(cfg);

    StringArray romfiles, outfiles;

    if (cfg.hasKey("OutFiles")) {

      // fetch explicitly listed files
      string romfile, outfile;
      stringstream bromlist, boutlist;
      bromlist << cfg["RomFiles"];
      boutlist << cfg["OutFiles"];
      do {
        romfile.clear();
        outfile.clear();
        bromlist >> romfile;
        boutlist >> outfile;
        if (romfile.empty() or outfile.empty())
          break;
        romfiles.push_back(romfile);
        outfiles.push_back(outfile);
      } while (bromlist and boutlist);
    } else {

      // construct filenames from templates
      Indices modeid;
      string basename = cfg["EdgeOutputBase"];
      cfg.getRange("ModeId", modeid);
      for (size_t i=0; i<modeid.size(); ++i) {
        string mstr = str(modeid[i]);
        romfiles.push_back( basename + mstr + ".brom" );
        outfiles.push_back( basename + mstr + ".bout" );
      }
    }

    transform_files(romfiles, outfiles, lps, mx);

    // create structured subcases
    lps.groupFields(mx);

    string resultname = cfg.value("Case", "transformed");
    resultname = append_suffix(resultname, ".zml");

    BinFileNodePtr bfp = mx.toXml(true).toGbf(true);
    bfp->write(resultname, BinFileNode::CompressedLZ4);

  } catch (Error & xcp) {
    cout << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
