
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#include <sstream>
#include "airfoilcollection.h"

using namespace std;

// ------------------------- internal ----------------------------------------

// simplest possible, case-insensitive comparison
bool char_equal_nocase(char x, char y)
{
  return toupper(static_cast<unsigned char>(x)) ==
         toupper(static_cast<unsigned char>(y));
}

bool equal_nocase(const string & x, const string & y)
{
  if (x.size() != y.size())
    return false;
  return std::equal(x.begin(), x.end(), y.begin(), char_equal_nocase);
}

// ------------------------- AirfoilCollection --------------------------

void AirfoilCollection::AfcEntry::fromXml(const XmlElement & xe)
{
  fname = xe.attribute("filename");
  cname = xe.attribute("coordname");
  
  const int np = xe.attr2int("npoints", 0); 
  crd.resize(np);
  stringstream ss(xe.text());
  for (int i=0; i<np; ++i)
    ss >> crd[i][0] >> crd[i][1];
}
      
XmlElement AirfoilCollection::AfcEntry::toXml() const
{
  XmlElement xaf("AirfoilCollectionEntry");
  xaf["filename"] = fname;
  xaf["coordname"] = cname;
  const int np = crd.size();
  xaf["npoints"] = str(np);
  
  stringstream ss;
  ss.precision(15);
  ss << scientific;
  for (int j=0; j<np; ++j)
    ss << "    " << crd[j][0] << " " << crd[j][1] << endl;
  xaf.text(ss.str());
  
  return xaf;
}

BinFileNodePtr AirfoilCollection::AfcEntry::toBinary() const
{
  BinFileNode *bfn = new BinFileNode("AirfoilCollectionEntry");
  bfn->attribute( "cname", cname );
  bfn->attribute( "fname", fname );
  
  if (not crd.empty()) {
    const Real *a = crd[0].pointer();
    bfn->copy( 2*crd.size(), a );  
  }
  
  return BinFileNodePtr(bfn);
}

void AirfoilCollection::AfcEntry::fromBinary(const BinFileNodePtr & bfn)
{
  assert(bfn->name() == "AirfoilCollectionEntry");
  cname = bfn->attribute("cname");
  fname = bfn->attribute("fname");
  
  uint np = bfn->blockElements() / 2;
  crd.resize(np);
  memcpy( &(crd[0][0]), bfn->blockPointer(), np*2*sizeof(Real) );

  // ap = AirfoilPtr(new Airfoil(cname, pts));
}

// ------------------------- AirfoilCollection -------------------------------

uint AirfoilCollection::addFile(const std::string & fname)
{
  // try to identify a name 
  string cname = Airfoil::searchCoordName( fname );
  
  
  AirfoilPtr ap(new Airfoil(cname));
  ap->read(fname);
  
  // cleanup filename 
  string file(fname);
  string::size_type pos;
  pos = file.rfind('/');
  if (pos != string::npos)
    file = file.substr(pos+1);
  pos = file.rfind('\\');
  if (pos != string::npos)
    file = file.substr(pos+1);
  
  const int n = file.size();
  for (int i=0; i<n; ++i)
    file[i] = tolower(file[i]);
  
  if (cname.empty())
    cname = file;
  
  foils.push_back( AfcEntry(cname, file, ap->sectionCoordinates()) );
  return foils.size()-1;
}
    
XmlElement AirfoilCollection::toXml() const
{
  XmlElement xe("AirfoilCollection");
  xe["collection_name"] = clname;
  xe["size"] = str(size());
  
  // set comment element
  if (not descr.empty()) { 
    XmlElement xc("Description");
    xc.text(descr);
    xe.append(std::move(xc));
  }
  
  const uint n = size();
  for (uint i=0; i<n; ++i) 
    xe.append(foils[i].toXml());
  
  return xe;
}
    
void AirfoilCollection::fromXml(const XmlElement & xe)
{
  string tag = xe.name();
  if (tag != "AirfoilCollection")
    throw Error("Invalid XML representation for AirfoilCollection: "+tag);
  
  clear();
  
  clname = xe.attribute("collection_name");
  const int nf = xe.attr2int("size", 0);
  
  foils.reserve(nf);
  XmlElement::const_iterator itr;
  for (itr = xe.begin(); itr != xe.end(); ++itr) {
    if (itr->name() == "AirfoilCollectionEntry") {
      AfcEntry ntry;
      ntry.fromXml(*itr);
      foils.push_back(ntry);
    } else if (itr->name() == "Description") {
      descr = itr->text();
    }
  }
  sort();
}

uint AirfoilCollection::findByCoordName(const std::string & cname) const
{
  // cant rely upon sorting
  const int n = size();
  for (int i=0; i<n; ++i) {
    if ( equal_nocase(foils[i].cname,cname) )
      return i;
  }
  return NotFound;
}
    
uint AirfoilCollection::findByFileName(const std::string & fname) const
{
  // cannot rely on sorting
  const int n = size();
  for (int i=0; i<n; ++i) {
    if ( equal_nocase(foils[i].fname, fname) )
      return i;
  }
  return NotFound;
}

BinFileNodePtr AirfoilCollection::toBinary() const
{
  BinFileNodePtr bf(new BinFileNode("AirfoilCollection"));
  bf->attribute("clname", clname);
  bf->attribute("descr", descr);
  
  const int nf = foils.size();
  for (int i=0; i<nf; ++i) 
    bf->append( foils[i].toBinary() );
  
  return bf;
}

void AirfoilCollection::fromBinary(const BinFileNodePtr & bfn)
{
  if (bfn->name() != "AirfoilCollection")
    throw Error("Incompatible binary file for AirfoilCollection.");
  
  clname = bfn->attribute("clname");
  if (bfn->hasAttribute("descr"))
    descr = bfn->attribute("descr");

  int nc = bfn->nchildren();
  foils.resize(nc);
  for (int i=0; i<nc; ++i)
    foils[i].fromBinary( bfn->childNode(i) );
}
