
/* ------------------------------------------------------------------------
 * file:       componentlibrary.cpp
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Provide access to stored components
 * ------------------------------------------------------------------------ */

#include <sstream>

#include <QFile>
#include <QString>
#include <QStringList>

#include <genua/xmlelement.h>
#include "componentlibrary.h"

ComponentLibrary SumoComponentLib;

using namespace std;

void ComponentLibrary::loadPredefined()
{
  // read airfoil collections
  QStringList afcollections;
  afcollections << ":/airfoils/ceasiom.gbf";
  afcollections << ":/airfoils/historical.gbf";
  afcollections << ":/airfoils/nlf.gbf";
  afcollections << ":/airfoils/research.gbf";
  afcollections << ":/airfoils/eppler.gbf";
  afcollections << ":/airfoils/selig.gbf";
  afcollections << ":/airfoils/fxwortmann.gbf";
  afcollections << ":/airfoils/lowreynolds.gbf";
  afcollections << ":/airfoils/althaus.gbf";
 
  aflib.clear();
  for (int i=0; i<afcollections.size(); ++i) {
    AirfoilCollectionPtr afp(new AirfoilCollection);
    afp->fromBinary( readGbf(afcollections.at(i)) );
    aflib.addCollection(afp);
  }
  
  // read assembly templates 
  QStringList ast, asn;
  
  ast << ":/smxtemplates/bjet.smx";
  asn << tr("Light executive jet");
      
  ast << ":/smxtemplates/ultralight.smx";
  asn <<  tr("Single-engine ultralight");
  
  ast << ":/smxtemplates/utility.smx";
  asn << tr("Twin-engine utility aircraft");
  
  ast << ":/smxtemplates/twinglider.smx";
  asn << tr("Two-seat sailplane");
  
  ast << ":/smxtemplates/widebody.smx";
  asn << tr("Four-engine widebody");
  
  ast << ":/smxtemplates/delta.smx";
  asn << tr("Small delta interceptor");
  
  asylib.clear();
  for (int i=0; i<ast.size(); ++i) {
    XmlTemplate xt;
    xt.id = asn.at(i);
    readXml(ast.at(i), xt.xe);
    asylib.push_back(xt);
  }
  
  // read component templates
  QStringList cmt, cmn;
  
  cmt << ":/smxcomponents/ceasiomboom.smx";
  cmn << tr("Tail boom (CEASIOM)");

  cmt << ":/smxcomponents/ceasiomfairing.smx";
  cmn << tr("Wing-body fairing (CEASIOM)");
  
  cmt << ":/smxcomponents/ceasiomnacelle.smx";
  cmn << tr("Engine nacelle (CEASIOM)");
  
  cmt << ":/smxcomponents/underwingnacelle.smx";
  cmn << tr("Engine nacelle (wing pod)");
  
  cmt << ":/smxcomponents/underwingpylon.smx";
  cmn << tr("Nacelle pylon (wing pod)");
  
  cmplib.clear();
  for (int i=0; i<cmt.size(); ++i) {
    XmlTemplate xt;
    xt.id = cmn.at(i);
    readXml(cmt.at(i), xt.xe);
    cmplib.push_back(xt);
  }
}

AssemblyPtr ComponentLibrary::assembly(uint i) const
{
  assert(i < asylib.size());
  
  AssemblyPtr asy(new Assembly);
  asy->clear();
  asy->fromXml(asylib[i].xe);
  return asy;
}

void ComponentLibrary::readXml(const QString & path, XmlElement & xe)
{
  QFile f(path);
  f.open(QIODevice::ReadOnly);
  QByteArray bytes = f.readAll();
  f.close();
  
  stringstream ss;
  ss << bytes.data();
      
  try {
    xe.read(ss, XmlElement::PlainText);
  } catch (Error & xcp) {
    clog << "Loading resource " << path.toStdString() << endl
         << " failed with error: " << xcp.what() << endl;
  }
}

BinFileNodePtr ComponentLibrary::readGbf(const QString & path)
{
  QFile f(path);
  f.open(QIODevice::ReadOnly);
  QByteArray bytes = f.readAll();
  f.close();
  
  stringstream ss;
  ss.write(bytes.data(), bytes.size());
  
  BinFileNodePtr bfn = BinFileNode::create();
  bfn->readPlain(ss);
  return bfn;
}
