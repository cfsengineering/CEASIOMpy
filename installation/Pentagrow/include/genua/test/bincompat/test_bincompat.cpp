
#include <genua/forward.h>
#include <genua/xmlelement.h>
#include <genua/algo.h>
#include <genua/dvector.h>
#include <genua/dbprint.h>

#include <iostream>
#include <fstream>

using namespace std;

struct ObjectV1
{
  ObjectV1(const char *s, Real x=1.0) : name(s) {
    array1.allocate(40);
    fill(array1.begin(), array1.end(), x);
  }
  XmlElement toXml(bool share) const {
    XmlElement xe("Object");
    xe["name"] = name;
    xe["version"] = "1";
    xe["count1"] = str(array1.size());
    xe.asBinary(array1.size(), array1.pointer(), share);
    return xe;
  }
  void fromXml(const XmlElement &xe) {
    name = xe.attribute("name");
    size_t c1 = xe.attr2int("count1", 0);
    array1.allocate(c1);
    xe.fetch(c1, array1.pointer());
  }
  string name;
  Vector array1;
};

struct ObjectV2
{
  ObjectV2(const char *s) : name(s), child("ChildObject", 2.1) {
    array1.allocate(48);
    fill(array1.begin(), array1.end(), 2.0);
  }
  XmlElement toXml(bool share) const {
    XmlElement xe("Object");
    xe["name"] = name;
    xe["version"] = "2";
    xe["count1"] = str(array1.size());
    xe.asBinary(array1.size(), array1.pointer(), share);
    xe.append(child.toXml(share));
    return xe;
  }
  void fromXml(const XmlElement &xe) {
    name = xe.attribute("name");
    size_t c1 = xe.attr2int("count1", 0);
    array1.allocate(c1);
    xe.fetch(c1, array1.pointer());
    for (const XmlElement &c : xe) {
      string id = c.attribute("name", "");
      if (id == "ChildObject")
        child.fromXml(c);
      else
        dbprint("Unrecognized: ",id);
    }
  }
  string name;
  ObjectV1 child;
  Vector array1;
};

struct ObjectV3
{
  ObjectV3(const char *s) : name(s), prep("Prepend", 3.1), child("ChildObject", 3.2) {
    array1.allocate(64);
    fill(array1.begin(), array1.end(), 3.0);
  }
  XmlElement toXml(bool share) const {
    XmlElement xe("Object");
    xe["name"] = name;
    xe["version"] = "3";
    xe["count1"] = str(array1.size());
    xe.asBinary(array1.size(), array1.pointer(), share);
    xe.append(prep.toXml(share));
    xe.append(child.toXml(share));
    return xe;
  }
  void fromXml(const XmlElement &xe) {
    name = xe.attribute("name");
    size_t c1 = xe.attr2int("count1", 0);
    array1.allocate(c1);
    xe.fetch(c1, array1.pointer());
    for (const XmlElement &c : xe) {
      string id = c.attribute("name", "");
      if (id == "ChildObject")
        child.fromXml(c);
      else if (id == "Prepend")
        prep.fromXml(c);
      else
        dbprint("Unrecognized: ",id);
    }
  }
  string name;
  ObjectV1 prep;
  ObjectV1 child;
  Vector array1;
};


int main(int argc, char *argv[])
{
  try {

    {

      // write a V1 object as reference
      ObjectV1 obj1("obj1");
      XmlElement x1 = obj1.toXml(true);
      x1.xwrite("reference_obj1.xml");
      x1.write("object1.zml", XmlElement::ZippedXml);

      // write a V2 object to be re-read as V1
      ObjectV2 obj2("obj2");
      XmlElement x2 = obj2.toXml(true);
      x2.xwrite("reference_obj2.xml");
      x2.write("object2.zml", XmlElement::ZippedXml);

      // write a V3 object to be re-read as V2
      ObjectV3 obj3("obj3");
      XmlElement x3 = obj3.toXml(true);
      x3.xwrite("reference_obj3.xml");
      x3.write("object3.zml", XmlElement::ZippedXml);

    }

    // read object2's xml representation as a obj1
    ObjectV1 ro1("Recovered");
    XmlElement r1;
    r1.read("object2.zml");
    ro1.fromXml(r1);

    // validate
    ro1.toXml(true).xwrite("validation_obj1.xml");

    // read object2's xml representation
    ObjectV2 ro2("Recovered");
    XmlElement r3;
    r3.read("object3.zml");
    ro2.fromXml(r3);

    // validate
    ro2.toXml(true).xwrite("validation_obj2.xml");


  } catch (Error & xcp) {
    cerr << xcp.what();
    return -1;
  }

  return 0;
}
