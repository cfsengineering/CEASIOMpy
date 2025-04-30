#include "lpstransform.h"
#include <genua/ffanode.h>
#include <genua/svector.h>
#include <genua/xcept.h>
#include <genua/timing.h>
#include <genua/parallel_loop.h>
#include <genua/ndpointtree.h>
#include <genua/mxmesh.h>
#include <genua/ioglue.h>
#include <boost/bind.hpp>
#include <genua/mxsolutiontree.h>
#include <genua/configparser.h>

using namespace std;

// 14331 N    ---         0 x 0       3/    time
// 14332 I    ---         1 x 1               iteration_number  =   2048
// 14333 D    ---         1 x 1               TTIME             =   1.356208e-01
// 14334 N    ---         0 x 0       1/      region
// 14335 N    ---         0 x 0       2/        boundary
// 14336 L    ---         1 x 1                   boundary_name     = "MainWing"
// 14337 DF   ---     94065 x 1                   pressure

// 5378 N    ---         0 x 0       1/    node_coord_info
// 5379 N    ---         0 x 0       1/      region
// 5380 N    ---         0 x 0       4/        boundary
// 5381 L    ---         1 x 1                   boundary_name     = "MainWing"
// 5382 DF   ---     94065 x 3                   coordinates       =
// 5383 DF   ---     94065 x 3                   b_surfaces        =
// 5384 IF   ---     94065 x 1                   b_nodes           =   2767

void ModalStepImporter::configure(const ConfigParser &cfg)
{
  m_nlength = cfg.getFloat("StepMultiples", 10.0);
  m_poo = cfg.getFloat("FreestreamPressure", 101325.0);
  m_maxrelfreq = cfg.getFloat("MaxRelativeFrequency", m_maxrelfreq);

  // output desired at reduced frequencies
  cfg.getRange("ReducedFrequency", m_krequested);

  // step of reduced frequency output data
  m_dredfreq = cfg.getFloat("ReducedFrequencyStep", 0.05);
}

template <typename Scalar>
static void ffa_fetch(FFANodePtr pfile, const char *field, Scalar &s)
{
  uint ipos(NotFound);
  ipos = pfile->findChild(field);
  if (ipos == NotFound)
    throw Error("Could not find entry '"+str(field)
                +"' in FFA node:"+pfile->name());

  pfile->child(ipos)->retrieve( s );
}

void ModalStepImporter::loadRomParameter(FFANodePtr pfile)
{
  ffa_fetch(pfile, "amplitude_factor", m_amplitude);
  ffa_fetch(pfile, "Mach", m_mach);
  ffa_fetch(pfile, "density", m_density);
  ffa_fetch(pfile, "ref_length", m_refchord);
  ffa_fetch(pfile, "ref_velocity", m_vref);
  ffa_fetch(pfile, "mode_identifier", m_modeid);

  // frequency step in Hz
  m_df = m_vref*m_dredfreq / (M_PI*m_refchord);
}

void ModalStepImporter::loadSampling(FFANodePtr pfile,
                                     const std::string &fieldName)
{
  m_xfield = fieldName;
  size_t nchild = pfile->nchildren();

  m_bndsize.clear();
  FFANodePtr pr = pfile->findPath("time/region");
  if (pr == nullptr)
    throw Error("No time/region path found in sampling file.");

  size_t np(0);
  for (size_t i=0; i<pr->nchildren(); ++i) {
    FFANodePtr pb = pr->child(i);
    if (pb->name() != "boundary")
      continue;
    for (size_t k=0; k<pb->nchildren(); ++k) {
      FFANodePtr pf = pb->child(k);
      if (pf->name() == fieldName) {
        size_t nfv = size_t(pf->nrows()) * pf->ncols();
        m_bndsize.push_back(nfv);
        np += nfv;
      }
    }
  }

  // import node coordinates and boundary names
  pr = pfile->findPath("node_coord_info/region");
  if (pr == nullptr)
    throw Error("No node_coord_info/region path found in sampling file.");

  m_bndpts.clear();
  m_bndnames.clear();
  for (size_t i=0; i<pr->nchildren(); ++i) {
    FFANodePtr pb = pr->child(i);
    assert(pb->name() == "boundary");
    uint icoo = pb->findChild("coordinates");
    assert(icoo != NotFound);
    size_t np = fetchNodeCoordinates(pb->child(icoo));
    uint ibn = pb->findChild("boundary_name");
    assert(ibn != NotFound);
    string bname;
    pb->child(ibn)->retrieve(bname);
    m_bndnames.push_back(bname);
    cout << "Using boundary " << bname << ", "
         << np << " nodes." << endl;
  }

  // count time steps
  size_t ntime(0);
  m_time.clear();
  for (size_t i=0; i<nchild; ++i) {
    FFANodePtr pt = pfile->child(i);
    if (pt->name() == "time") {
      ++ntime;
      uint itt = pt->findChild("TTIME");
      assert(itt != NotFound);
      m_time.push_back(0.0);
      pt->child(itt)->retrieve( m_time.back() );
    }
  }

  m_iramp = std::round(double(ntime) / double(m_nlength));
  m_tramp = m_time[m_iramp];

  log("[i]",ntime,"time steps, ",np," points.");
  log("[i]",m_iramp,"steps in ramp, T = ",m_tramp);

  m_yt.clear();
  m_yt.allocate(ntime, np);
  Vector tmp;
  size_t itime(0);
  for (size_t i=0; i<nchild; ++i) {
    FFANodePtr pt = pfile->child(i);
    if (pt->name() == "time") {
      uint ireg = pt->findChild("region");
      assert(ireg != NotFound);
      FFANodePtr pr = pt->child(ireg);
      size_t col = 0;
      for (size_t j=0; j<pr->nchildren(); ++j) {
        FFANodePtr pb = pr->child(j);
        if (pb->name() != "boundary")
          continue;
        for (size_t k=0; k<pb->nchildren(); ++k) {
          FFANodePtr pf = pb->child(k);
          if (pf->name() == fieldName) {
            size_t nfv = size_t(pf->nrows()) * pf->ncols();
            tmp.allocate(nfv);
            pf->retrieve( tmp.pointer() );
            for (size_t a=0; a<nfv; ++a)
              m_yt(itime, col+a) = tmp[a];
            col += nfv;
          }
        }
      }
      ++itime;
    }
  }

  if (m_xfield == "pressure") {
    log("[i] Normalizing pressure values to pressure coefficients.");
    normalize();
  }
}

void ModalStepImporter::transform()
{
  // constants
  const Real a = M_PI / m_tramp;
  const Real dt = m_time[1] - m_time[0];
  const Real fmax =  m_maxrelfreq / m_tramp;
  const size_t nt = m_time.size();

  // debug
  log("[i] Using time-step:", dt);
  log("[i] Maximum output frequency f:", fmax,
      "Hz, k:", M_PI*fmax*m_refchord/m_vref);

  // manufacture unit input step (could be extracted from .bres)
  // note that amplitude factor is accounted for in m_yt
  Vector xt(nt);
  for (size_t i=0; i<nt; ++i) {
    if (m_time[i] <= m_tramp)
      xt[i] = 0.5*(1.0 - std::cos(a*m_time[i]));
    else
      xt[i] = 1.0;
  }

  // FFT-based transformation
  StepTransform::transform(dt, m_df, fmax, xt, m_yt);

//  // determine frequencies from list of user-provided k
//  CpxVector s;
//  int nrk = m_krequested.size();
//  Real wmax = m_maxrelfreq * 2*M_PI / m_tramp;
//  Real kmax = 0.5 * wmax * m_refchord / m_vref;
//  for (int i=0; i<nrk; ++i) {
//    Real k = m_krequested[i];
//    if (k <= kmax)
//      s.push_back( Complex(0.0, 2.0 * k * m_vref / m_refchord) );
//    else
//      log("[w] Requested reduced frequency",k,"is above maximum",kmax);
//  }

//  StepTransform::transform(m_tramp, m_time, m_yt, s);
}

void ModalStepImporter::normalize()
{
  Real q = 0.5*m_density*sq(m_vref);
  const size_t nc = m_yt.ncols();
  const size_t nr = m_yt.nrows();
  m_cpo.allocate(nc);
  for (size_t j=0; j<nc; ++j) {
    Real yo = m_yt(0,j);
    m_cpo[j] = (yo - m_poo) / q;
    for (size_t i=0; i<nr; ++i) {
      Real dp = m_yt(i,j) - yo;
      m_yt(i,j) = dp / ( q* m_amplitude );
    }
  }
}

void ModalStepImporter::appendFields(MxMesh &mx)
{
  // build node search tree
  NDPointTree<3,float> ptree;
  ptree.allocate(m_bndpts, true);
  ptree.sort();

  const uint ns = m_gs.nrows();
  // Vector efield( mx.nnodes() );
  VectorArray realfields( ns ), imagfields( ns );
  for (uint i=0; i<ns; ++i) {
    realfields[i].resize( mx.nnodes() );
    imagfields[i].resize( mx.nnodes() );
  }

  const float maxdst( sq(1e-6f) );

  BEGIN_PARLOOP_CHUNK(0, int(mx.nnodes()), 512)
  //int a(0), b(mx.nnodes()), nfound(0);
  for (int i=a; i<b; ++i) {
    Vct3f pf( mx.node(i) );
    uint jn = ptree.nearest( pf );
    if ( sq(pf - ptree.point(jn)) > maxdst ) {
      continue;
    }
    // efield[i] = m_fitError[jn];
    for (uint k=0; k<ns; ++k) {
      Complex ys = m_gs(k, jn);
      realfields[k][i] = ys.real();
      imagfields[k][i] = ys.imag();
    }
    // ++nfound;
  }
  END_PARLOOP

  // string prefix = "M" + str(m_dcpFields.size()+1);
  m_dcpFields.push_back( Indices() );
  Indices & fix( m_dcpFields.back() );
  for (uint k=0; k<ns; ++k) {
    string suffix = cpFieldName( laplaceVariable(k) );
    fix.push_back( mx.appendField("ReDCp"+suffix, realfields[k]) );
    fix.push_back( mx.appendField("ImDCp"+suffix, imagfields[k]) );
  }
}

void ModalStepImporter::groupFields(MxMesh &mx) const
{
  MxSolutionTreePtr proot( mx.solutionTree() );
  if (proot == nullptr) {
    proot = boost::make_shared<MxSolutionTree>("Subcases");
    mx.solutionTree( proot );
  }

  // create a subcase for Mach number
  stringstream ss;
  ss.precision(3);
  ss << "Mach " << m_mach;
  MxSolutionTreePtr psub = boost::make_shared<MxSolutionTree>(ss.str());

  // annotate subcase with reference data
  {
    XmlElement xe("Reference");
    xe["Mach"] = str(m_mach);
    xe["Chord"] = str(m_refchord);
    xe["Velocity"] = str(m_vref);
    xe["Density"] = str(m_density);
    psub->annotate(xe);
  }

  // create one solution tree node per frequency
  int nf = m_svalue.size();
  for (int i=0; i<nf; ++i) {
    stringstream ss;
    ss.precision(3);
    ss << "k " << reduce(m_svalue[i]);
    MxSolutionTreePtr sp = boost::make_shared<MxSolutionTree>(ss.str());
    for (uint j=0; j<m_dcpFields.size(); ++j) {
      sp->appendField( m_dcpFields[j][2*i] );
      sp->appendField( m_dcpFields[j][2*i+1] );
    }
    psub->append(sp);
  }

  proot->append(psub);
}

size_t ModalStepImporter::fetchNodeCoordinates(FFANodePtr pnode)
{
  assert(pnode->name() == "coordinates");
  size_t np = pnode->nrows();
  size_t nc = pnode->ncols();
  assert(nc == 3);

  // as always coordinates are stored transposed/SoA-wise
  Matrix pt;
  pt.allocate(np, nc);
  pnode->retrieve(pt.pointer());

  PointList<3,float> tmp(np);
  for (size_t i=0; i<np; ++i)
    tmp[i] = Vct3f( pt(i,0), pt(i,1), pt(i,2) );

  m_bndpts.insert(m_bndpts.end(), tmp.begin(), tmp.end());
  return np;
}

string ModalStepImporter::cpFieldName(Complex s) const
{
  Real k = reduce(s);
  stringstream ss;
  ss.precision(3);
  ss << " Mode " << m_modeid << " k " << k;
  return ss.str();
}


