
#include <surf/fsimesh.h>
#include <surf/loadipol.h>
#include <surf/nstmesh.h>
#include <genua/xcept.h>
#include <genua/configparser.h>
#include <genua/transformation.h>
#include <iostream>
#include <fstream>

using namespace std;

// Perform a simple sweep in alpha and beta and generate nastran loads
// for a beam model - for testing whether nastran i/o works correctly
int test_rbcase(const ConfigParser & cfg);

// use stored state history and construct aerodynamic loads using quasi-steady
// model, then generate nastran subcases for each time step; this function is
// specialized for the nj-gla model
int test_history(const ConfigParser & cfg);

// load nastran deformation history y(t) from subcases and postprocess to
// obtain actual displacements u(t)
// int test_postproc(const ConfigParser & cfg);

// generate time-dependent loads for direct transient analysis
int test_tload(const ConfigParser & cfg);

int main(int argc, char *argv[])
{

  try {

    if (argc < 2) {
      cerr << "Usage: " << argv[0] << " config.cfg" << endl;
      return -1;
    }

    // configuration
    ConfigParser cfg(argv[1]);

    string mode = toLower(cfg["Mode"]);
    if (mode == "rbcase")
      test_rbcase(cfg);
    else if (mode == "genloads")
      test_history(cfg);
    else if (mode == "transient")
      test_tload(cfg);
    //    else if (mode == "postprocess")
    //      test_postproc(cfg);
    else
      throw Error("Don't recognize mode: "+mode);

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }

  return 0;
}

int test_tload(const ConfigParser & cfg)
{
  // load reference solution
  LoadIpol lip;
  {
    XmlElement xe;
    xe.read(cfg["Reference"]);
    lip.fromXml(xe);
  }

  // define states
  uint iMach = lip.newState("mach", 0.0, 1.0);
  uint iAlpha = lip.newState("alpha", -rad(20.), rad(20.));
  uint iBeta = lip.newState("beta", -rad(20.), rad(20.));
  uint iRollRate = lip.newState("rollrate", -rad(90.), rad(90.));
  uint iPitchRate = lip.newState("pitchrate", -rad(20.), rad(20.));
  uint iYawRate = lip.newState("yawrate", -rad(20.), rad(20.));

  // 0    1     2    3 4 5
  // Mach alpha beta p q r
  const int nx = 6;
  Vector xref(nx);  // reference state : all zero
  lip.markReference(lip.findField("Reference - pressure coefficient"), xref);
  lip.markDerivative(lip.findField("Alpha - pressure difference"), iAlpha);
  lip.markDerivative(lip.findField("Beta - pressure difference"), iBeta);
  lip.markDerivative(lip.findField("Roll rate - pressure difference"), iRollRate);
  lip.markDerivative(lip.findField("Pitch rate - pressure difference"), iPitchRate);
  lip.markDerivative(lip.findField("Yaw rate - pressure difference"), iYawRate);

  PointList<6> fnref;
  Real qoo = cfg.getFloat("DynamicPressure");

  // generate cp at alpha, beta
  Vector xp(nx), pref;
  xp[iAlpha] = rad(1.5);
  xp[iBeta] = rad(0.);
  lip.eval(xp, pref);

  // cp to pressure
  pref *= qoo;

  // beam model in bmx is in the same coordinate system (and SI units)
  MxMeshPtr amx(&lip, null_deleter());
  MxMeshPtr bmx(new MxMesh);
  {
    XmlElement xe;
    xe.read( cfg["BeamModel"] );
    bmx->fromXml(xe);
  }

  // generate nodal forces for steady reference case
  {
    FsiMesh fsi;
    fsi.mergeBeams(bmx);
    fsi.mergeFluid(amx);
    fsi.buildInterpolator();
    fsi.agglomerate(pref, fnref);
  }

  // load another interpolator for loads due to elastic motion
  LoadIpol elp;
  {
    XmlElement xe;
    xe.read(cfg["ElasticAero"]);
    elp.fromXml(xe);
  }

  const int nmodes = 20;
  uint iState[nmodes];
  for (int i=0; i<20; ++i) {
    iState[i] = elp.newState("State "+str(i));
  }

  for (int i=0; i<20; ++i) {
    string fieldname = string("Re(cp) mode "+str(6+i)+" k = 0 shat = 0");
    elp.markDerivative(elp.findField(fieldname), iState[i]);
  }

  // mesh file which contains motion history and eigenmode shapes
  // for the nj-gla case, these are 8 pseudo-modes and 12 eigenmodes
  // z, theta, delta1 ... delta6, xi1 ... xi12
  MxMeshPtr mmx(new MxMesh);
  {
    XmlElement xe;
    xe.read(cfg["ModalPath"]);
    mmx->fromXml(xe);
  }

  FsiMesh gsi;
  gsi.mergeBeams(bmx);
  gsi.mergeFluid(mmx);
  gsi.buildInterpolator();

  // original nastran mesh is in mm and rotated 180deg
  Trafo3d rt180;
  rt180.rotate(PI, 0.0, 0.0);

  const int npath = mmx->ndeform();
  for (int ipath=0; ipath<npath; ++ipath) {

    MxMeshDeform & path( mmx->deform(ipath) );
    path.buildSpline();
    cout << "Path name: " << path.name()
        << " duration: " << path.duration() << endl;

    // number of steps to sample from spline
    const int nstep = cfg.getInt("TimeSteps", 500);
    const Real dt = path.duration() / (nstep - 1);
    const int nskip = cfg.getInt("SkipFactor", 1);
    cout << "Steps: " << nstep << " dt: " << dt
        << " Output: " << nstep/nskip << endl;

    string outfname("tload_" + path.name() + ".blk");
    ofstream tos(outfname.c_str());
    tos << "TSTEP, 1, " << nstep << ", " << nstr(dt) << ", " << nskip << endl;
    tos << "DLOAD, 10, 1.0, 1.0, 101, 1.0, 102, 1.0, 103," << endl;
    for (int i=3; i<nmodes; ++i) {
      if ( (i-3)%4 == 0 )
        tos << ", ";
      tos << "1.0, " << 101+i << ", ";
      if ( (i-3)%4 == 3 or i == nmodes-1)
        tos << endl;
    }

    // write out DAREA cards which describe the spatial load distribution
    // and the time history of the corresponding modal coordinate
    Vector pi(elp.nnodes());
    PointList<6> fni;
    for (int i=0; i<nmodes; ++i) {
      tos << "TLOAD1, " << 101+i       // TLOAD SID
          << ", " << 201+i             // EXCITEID -> DAREA SID
          << ", 0, LOAD, " << 301+i    // TABLE1D SID
          << endl;
      Vector xi(nmodes);
      xi[i] = 1;
      elp.eval(xi, pi);
      pi *= qoo;
      gsi.agglomerate(pi, fni);
      rt180.transformList6D( fni );
      gsi.exportDarea(201+i, fni, tos, 1.0, 1000.0);
      path.writeTable(301+i, nstep, 12+i, tos);
    }

  } // path loop

  return 0;
}

//int test_postproc(const ConfigParser & cfg)
//{
//  // fetch nastan subcase solution for y(t)
//  MxMesh subc;
//  {
//    NstMesh nstsub;
//    nstsub.nstread(cfg["NastranSubcases"]);
//    nstsub.toMx(subc);
//  }

//  // locate displacement solution
//  Indices idisp;
//  for (uint i=0; i<subc.nfields(); ++i) {
//    const MxMeshField & fld( subc.field(i) );
//    if (fld.valueClass() != MxMeshField::Displacement)
//      continue;
//    if (fld.name().find("Displacement") == string::npos)
//      continue;
//    idisp.push_back(i);
//  }

//  // debug
//  cout << "Found " << idisp.size() << " y displacement fields." << endl;
//  const int nstep = idisp.size();

//  // read stored path, file contains eigenmodes as well
//  MxMesh mpath;
//  {
//    XmlElement xe;
//    xe.read(cfg["ModalPath"]);
//    mpath.fromXml( xe );
//  }
//  uint ipath = cfg.getInt("PathIndex", 0);
//  if (mpath.ndeform() <= ipath)
//    throw Error("Not enough trajectories in path file.");

//  MxMeshDeform & path( mpath.deform(ipath) );
//  path.buildSpline();
//  const int nx = path.nmodes();

//  // locate eigenmodes
//  Indices imodes;
//  for (uint i=0; i<subc.nfields(); ++i) {
//    const MxMeshField & fld( mpath.field(i) );
//    if (fld.valueClass() != MxMeshField::Eigenmode)
//      continue;
//    if (fld.ndimension() != 3)
//      continue;
//    imodes.push_back(i);
//  }

//  // inverse of omega^2
//  Vector iomg(nx);

//  // process timesteps
//  Vector x(nx), xd(nx), xdd(nx), iwxdd(nx);
//  const int nn = subc.nnodes();
//  PointList<3> u(nn);
//  const Real dt = path.duration() / nstep;
//  for (int istep=0; istep<nstep; ++istep) {
//    const MxMeshField & yfield( subc.field(idisp[istep]) );
//    path.interpolateSubspace(istep*dt, x, xd, xdd);
//    for (int i=0; i<nn; ++i) {
//      yfield.value(i, u[i]);          // u[i] <- y(t)
//      for (int j=0; j<nm; ++j) {
//        Vct3 pz;
//        mpath.field(imodes[j]).value(i, pz);
//        u[i] -= xdd[j] * iomg[j] * pz;
//      }
//    }

//    // store u(t_i)

//  }


//}

int test_history(const ConfigParser & cfg)
{
  // load reference solution
  LoadIpol lip;
  {
    XmlElement xe;
    xe.read(cfg["Reference"]);
    lip.fromXml(xe);
  }

  // define states
  uint iMach = lip.newState("mach", 0.0, 1.0);
  uint iAlpha = lip.newState("alpha", -rad(20.), rad(20.));
  uint iBeta = lip.newState("beta", -rad(20.), rad(20.));
  uint iRollRate = lip.newState("rollrate", -rad(90.), rad(90.));
  uint iPitchRate = lip.newState("pitchrate", -rad(20.), rad(20.));
  uint iYawRate = lip.newState("yawrate", -rad(20.), rad(20.));

  // 0    1     2    3 4 5
  // Mach alpha beta p q r
  const int nx = 6;
  Vector xref(nx);  // reference state : all zero
  lip.markReference(lip.findField("Reference - pressure coefficient"), xref);
  lip.markDerivative(lip.findField("Alpha - pressure difference"), iAlpha);
  lip.markDerivative(lip.findField("Beta - pressure difference"), iBeta);
  lip.markDerivative(lip.findField("Roll rate - pressure difference"), iRollRate);
  lip.markDerivative(lip.findField("Pitch rate - pressure difference"), iPitchRate);
  lip.markDerivative(lip.findField("Yaw rate - pressure difference"), iYawRate);

  PointList<6> fnref;
  Real qoo = cfg.getFloat("DynamicPressure");

  // generate cp at alpha, beta
  Vector xp(nx), pref;
  xp[iAlpha] = rad(1.5);
  xp[iBeta] = rad(0.);
  lip.eval(xp, pref);

  // cp to pressure
  pref *= qoo;

  // beam model in bmx is in the same coordinate system (and SI units)
  MxMeshPtr amx(&lip, null_deleter());
  MxMeshPtr bmx(new MxMesh);
  {
    XmlElement xe;
    xe.read( cfg["BeamModel"] );
    bmx->fromXml(xe);
  }

  // generate nodal forces for steady reference case
  {
    FsiMesh fsi;
    fsi.mergeBeams(bmx);
    fsi.mergeFluid(amx);
    fsi.buildInterpolator();
    fsi.agglomerate(pref, fnref);
  }

  // load another interpolator for loads due to elastic motion
  LoadIpol elp;
  {
    XmlElement xe;
    xe.read(cfg["ElasticAero"]);
    elp.fromXml(xe);
  }

  const int nmodes = 20;
  uint iState[nmodes];
  for (int i=0; i<20; ++i) {
    iState[i] = elp.newState("State "+str(i));
  }

  for (int i=0; i<20; ++i) {
    string fieldname = string("Re(cp) mode "+str(6+i)+" k = 0 shat = 0");
    elp.markDerivative(elp.findField(fieldname), iState[i]);
  }

  // mesh file which contains motion history and eigenmode shapes
  // for the nj-gla case, these are 8 pseudo-modes and 12 eigenmodes
  // z, theta, delta1 ... delta6, xi1 ... xi12
  MxMeshPtr mmx(new MxMesh);
  {
    XmlElement xe;
    xe.read(cfg["ModalPath"]);
    mmx->fromXml(xe);
  }

  FsiMesh gsi;
  gsi.mergeBeams(bmx);
  gsi.mergeFluid(mmx);
  gsi.buildInterpolator();

  // we assume that there is a single stored path
  if ( mmx->ndeform() != 1 )
    throw Error("ModalPath file does not contain exactly 1 path.");

  MxMeshDeform & path( mmx->deform(0) );
  path.buildSpline();
  ofstream bout("pathloads.blk"), caseout("subcase.txt");

  // number of steps to evaluate (5000 in sim)
  const int nstep = 201;
  const Real dt = path.duration() / (nstep - 1);

  // can scale elastic motion to achieve larger changes
  Real modeScale = cfg.getFloat("ModeScale", 1.0);

  // original nastran mesh is in mm and rotated 180deg
  Trafo3d rt180;
  rt180.rotate(PI, 0.0, 0.0);

  Vector pt;
  PointList<6> fnt;
  Vector xpath( path.nmodes() ), xem( nmodes );
  for (int i=0; i<nstep; ++i) {
    path.interpolateSubspace(path.time(0) + i*dt, xpath);

    // [z theta delta1 ... delta6]
    for (int j=0; j<8; ++j)
      xem[j] = xpath[12+j];

    // elastic modes
    for (int j=8; j<nmodes; ++j)
      xem[j] = xpath[12+j] * modeScale;

    elp.eval(xem, pt);
    pt *= qoo;
    gsi.agglomerate(pt, fnt);
    // fnt += fnref;

    // transform nodal forces
    rt180.transformList6D( fnt );
    gsi.exportForces(fnt, bout, i+1, 1.0, 1000.0);

    // case control section
    caseout << "SUBCASE = " << i+1 << endl;
    caseout << "LOAD = " << i+1 << endl;
  }

  bout.close();

  return 0;

}

int test_rbcase(const ConfigParser & cfg)
{
  // load reference solution
  LoadIpol lip;
  {
    XmlElement xe;
    xe.read(cfg["Reference"]);
    lip.fromXml(xe);
  }

  // define states
  uint iMach = lip.newState("mach", 0.0, 1.0);
  uint iAlpha = lip.newState("alpha", -rad(20.), rad(20.));
  uint iBeta = lip.newState("beta", -rad(20.), rad(20.));
  uint iRollRate = lip.newState("rollrate", -rad(90.), rad(90.));
  uint iPitchRate = lip.newState("pitchrate", -rad(20.), rad(20.));
  uint iYawRate = lip.newState("yawrate", -rad(20.), rad(20.));

  // 0    1     2    3 4 5
  // Mach alpha beta p q r
  const int nx = 6;
  Vector xref(nx);  // reference state : all zero
  lip.markReference(lip.findField("Reference - pressure coefficient"), xref);
  lip.markDerivative(lip.findField("Alpha - pressure difference"), iAlpha);
  lip.markDerivative(lip.findField("Beta - pressure difference"), iBeta);
  lip.markDerivative(lip.findField("Roll rate - pressure difference"), iRollRate);
  lip.markDerivative(lip.findField("Pitch rate - pressure difference"), iPitchRate);
  lip.markDerivative(lip.findField("Yaw rate - pressure difference"), iYawRate);

  // write in text form for debugging
  lip.createNote();
  lip.note().write("note.xml");

  // generate cp at alpha, beta
  Vector xp(nx), cp;
  xp[iAlpha] = rad(8.);
  xp[iBeta] = rad(-6.);
  lip.eval(xp, cp);

  lip.appendField("Cp a+8 b-6", cp);
  lip.toXml(true).zwrite("testcase.zml");

  // test generation of nastran loads for interpolated case
  if (not cfg.hasKey("BeamModel"))
    return 0;

  // assume beam model is in the same coordinate system (and SI units)
  MxMeshPtr amx(&lip, null_deleter());
  MxMeshPtr bmx(new MxMesh);
  {
    XmlElement xe;
    xe.read( cfg["BeamModel"] );
    bmx->fromXml(xe);
  }

  Real qoo = cfg.getFloat("DynamicPressure");

  FsiMesh fsi;
  fsi.mergeBeams(bmx);
  fsi.mergeFluid(amx);
  fsi.buildInterpolator();

  ofstream bout("beamloads.blk");

  // original nastran mesh is in mm and rotated 180deg
  Trafo3d rt180;
  rt180.rotate(PI, 0.0, 0.0);

  // loads for a few state vectors to test nastran interfacing
  PointList<6> fnodal;
  const int nstep = 16;
  for (int i=0; i<nstep; ++i) {
    xp[iAlpha] = rad(14.0)* sin(PI*i/(nstep-1));
    xp[iBeta] = rad(8.0) * sin(0.5*PI*i/(nstep-1));
    cout << "Subcase " << i+1
        << " alpha " << deg(xp[iAlpha])
        << " beta " << deg(xp[iBeta]) << endl;
    lip.eval(xp, cp);

    amx->appendField("Cp Subcase "+str(i+1), cp);

    fsi.agglomerate(qoo*cp, fnodal);
    fsi.appendSifField(fnodal);

    Vct6 fsum = fsi.sum(vct(8.3, 0.0, 0.0), fnodal);
    cout << "Fz " << fsum[2] << " Fy " << fsum[1] << endl;

    // transform to nastran model space
    const int np = fnodal.size();
    for (int j=0; j<np; ++j) {
      Vct3 f, m;
      split_vct(fnodal[j], f, m);
      rt180.transformPoint(f);
      rt180.transformPoint(m);
      join_vct(f, m, fnodal[j]);
    }

    fsi.exportForces(fnodal, bout, 1+i, 1.0, 1000.0);
  }

  // debugging output
  bmx->toXml(true).zwrite("loaded.zml");
  amx->toXml(true).zwrite("cpsubcases.zml");

  return 0;
}
