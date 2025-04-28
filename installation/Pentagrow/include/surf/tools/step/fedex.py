# -*- coding: utf-8 -*-
#
# fedex.py
#
# Generates C++ classes from EXPRESS definition file.
# + Recognizes typedefs and enumerations
# + Generates class hierarchies
# + Aggregate entities use integer references, not pointers
# + Declaration order is correct
# + Stub code for read/write operations is written to cpp file
# - optional attributes are not recognized
# - short form not recognized

import string

creator_table = [];
enum_names = set();
select_names = set();
all_typedefs = dict();
all_entities = dict();
entities_written = set();
entities_waiting = set();

def expToClass(s):
  return "Step"+string.capwords(s.strip(), '_').replace('_',"");

class step_attribute:
  
  def __init__(self, s):
    self.var = "";
    self.dim = 1;
    self.typ = "StepID";
    self.cmm = "";
    self.isenum = 0;
    self.isselect = 0;
    self.skip = 0;
    self.optional = 0;
    self.classify(s);
    
  def declare(self):
    if self.dim == 1:
      return "%s %s; // %s" % (self.typ, self.var, self.cmm);
    elif self.dim == -1:
      return "std::vector<%s> %s; // %s" % (self.typ, self.var, self.cmm);
    elif self.dim == -2:
      return "DMatrix<%s> %s; // %s" % (self.typ, self.var, self.cmm);
    else:
      return "%s %s[%d]; // %s" % (self.typ, self.var, self.dim, self.cmm);
      
  def readCode(self):
    if self.skip:
      return "line.skipAttr(); // %s skipped" % self.var;
    elif self.isenum:
      if self.dim == 1:
        if self.optional:
          return "line.option() ? %s.read(line) : line.skipAttr();" % self.var;
        else:
          return "%s.read(line);" % self.var;
      elif self.dim < 0:
        if self.isselect:
          return "line.readSelectArray(%s);" % self.var;
        else:
          return "line.readEnumArray(%s);" % self.var;
      else:
        if self.isselect:
          return "line.readSelectArray<%d>(%s);" % (self.dim,self.var);
        else:
          return "line.readEnumArray<%d>(%s);" % (self.dim,self.var);
    elif self.dim > 1:
      return "line.readArrayAttr<%d>(%s);" % (self.dim, self.var);
    else:
      if self.optional:
        return "line.option() ? line.readAttr(%s) : line.skipAttr();" % self.var;
      else:
        return "line.readAttr(%s);" % self.var;
    
  def writeCode(self):
    if self.skip:
      return "// attribute %s skipped." % self.var;
    elif self.isenum:
      if self.dim == 1:
        return "%s.write(os);" % self.var;
      elif self.dim < 0:
        if self.isselect:
          return "StepFileLine::writeSelectArray(os, %s);" % self.var;
        else:
          return "StepFileLine::writeEnumArray(os, %s);" % self.var;
      else:
        if self.isselect:
          return "StepFileLine::writeSelectArray<%d>(os, %s);" % (self.dim,self.var);
        else:
          return "StepFileLine::writeEnumArray<%d>(os, %s);" % (self.dim,self.var);
    elif self.dim > 1:
      return "StepFileLine::writeArrayAttr<%d>(os, %s);" % (self.dim, self.var);
    else:
      if self.optional and self.typ == "StepID":
        return "StepFileLine::writeAttr(os, %s, '$');" % self.var;
      else:
        return "StepFileLine::writeAttr(os, %s);" % self.var;
    
  def classify(self, s):
    wds = s.strip(";, \n\t\r").split();
    self.var = wds[0].strip();
    rawtyp = wds[-1].strip();
    self.cmm = rawtyp;
    if rawtyp in enum_names:
      self.isenum = 1;
      self.typ = expToClass(rawtyp);
    else:
      if rawtyp in all_typedefs:
        rawtyp = all_typedefs[rawtyp];
      if rawtyp == "INTEGER":
        self.typ = "int";
      elif rawtyp == "REAL":
        self.typ = "double";
      elif rawtyp == "STRING":
        self.typ = "std::string";
      elif rawtyp == "BOOLEAN":
        self.typ = "bool";
      elif rawtyp == "LOGICAL":
        self.typ = "StepLogical";
        self.isenum = 1;
      else:
        self.typ = "StepID";
      
    # determine array status
    lcount = s.count("LIST");
    if lcount > 1:
      self.dim = -2;
    elif lcount == 1 or s.count("BAG") == 1 or s.count("SET") == 1:
      p1 = s.find(']') - 1;
      if p1 >= 0 and s[p1] != '?':
        self.dim = int(s[p1]);
      else: 
        self.dim = -1;
    else:
      self.dim = 1;
      
    if self.typ in select_names:
      self.isselect = 1;
      
    if s.count("OPTIONAL") > 0:
      self.optional = 1;
      
    # replace reserved words
    if self.var == "class":
      self.var = self.cmm + '_' + self.var;
          
          
class step_entity:
  
  def __init__(self, s):
    self.exp = s.strip("; \t\n\r");
    self.name = expToClass(self.exp);
    self.base = ["StepEntity"];
    self.attr = [];
    self.assembling = 1;
    self.expanded = 0;
   
  def append(self, s):
    if self.assembling == 0:
      return;
    elif s.count("UNIQUE"):
      self.assembling = 0;
    elif s.count("DERIVE"):
      self.assembling = 0;
    elif s.count("WHERE"):
      self.assembling = 0;
      
    if s.count("SUBTYPE OF"):
      cls = s[s.find('(')+1 : s.find(')')].split(',');
      self.base = map(expToClass, cls);
    elif s.count(':'):
      self.attr.append( step_attribute(s) );
        
  def typeCode(self):
    return self.name.replace("Step", "Step::");
      
  def prependAttr(self, emap):
    for b in reversed(self.base):
      self.recPrepAttr(b, emap);
    # remove duplicates
    tmp = [];
    for a in self.attr:
      if a not in tmp:
        tmp.append(a);
    if len(tmp) != len(self.attr):
      print "Erased duplicate attributes from ", self.name
    self.attr = tmp;
    self.expanded = 1;
      
  def recPrepAttr(self, bclass, emap):
    if bclass == "StepEntity":
      return;
    cls = emap[bclass];
    self.attr = cls.attr + self.attr;
    if cls.expanded:
      return;
    for b in cls.base:
      self.recPrepAttr(b, emap);
      
  def toCpp(self, hp, cp):
    
    # enqueue if any one of the base classes is not yet written 
    # to file
    for b in self.base:
      if b not in entities_written:
        # print self.name, " waiting for ", b;
        entities_waiting.add(self);
        return 0;
      #else:
        #print "Base class ", b, " is already written."; 
        
    #print "Writing ", self.name;
    entities_written.add(self.name);

    # write header
    #bcls = string.join(self.base, ', public ')
    #hp.write("class {0} : public {1}\n".format(self.name,bcls));
    hp.write("class %s : public StepEntity\n" % self.name);
    hp.write("{\n  public:\n");
    hp.write("    {0}(StepID entityId=0) : StepEntity(entityId) ".format(self.name));
    
    for a in self.attr:
      if a.typ == "StepID" and a.dim == 1:
        hp.write(", %s(0)" % a.var);  
    
    hp.write(" {}\n");
    hp.write("    virtual ~{0}()".format(self.name));
    hp.write(" {}\n");
    hp.write("    virtual bool read(StepFileLine & line);\n");
    hp.write("    virtual void write(std::ostream & os) const;\n");
    keyString = self.exp.upper();
    hp.write('    virtual const char *keyString() const {return "%s";}\n'%keyString);
    if len(self.attr) > 0:
      hp.write("  public:\n");
    for a in self.attr:
      hp.write("    %s\n" % a.declare() );
    # hp.write("    static const char *key_string;\n");
    hp.write("};\n\n");
    
    # register and declare creator function
    crf = "step_create_%s" % self.exp;
    creator_table.append( (self.exp.upper(), crf) );
    # hp.write("%s *%s(StepFileLine & line);\n\n" % (self.name, crf));
    hp.write("StepEntity *%s(StepFileLine & line);\n\n" % (crf));
    
    # implementation
    cp.write("// ------------ %s\n\n" % self.name);
    
    # cp.write('const char %s::key_string[] = "%s";\n\n' % (self.name, self.exp.upper()));
    
    cp.write("bool %s::read(StepFileLine & line)\n" % self.name);
    cp.write("{\n");
    cp.write("  bool ok = true;\n");
    #for b in self.base:
    #  cp.write("  ok &= %s::read(line);\n" % b);
    for a in self.attr:
      cp.write("  ok &= %s\n" % a.readCode());
    cp.write("  return ok;\n")
    cp.write("}\n\n");
    
    # write implementation
    cp.write("void %s::write(std::ostream & os) const\n" % self.name);
    cp.write("{\n");
    
    #for b in self.base:
    #  cp.write("  %s::write(os);\n" % b);
    #  cp.write("  os << ',';\n");
    nattr = len(self.attr);
    if nattr > 1:
      for i in xrange(0,nattr-1):
        a = self.attr[i];    
        cp.write("  %s os << ',';\n" % a.writeCode());
      a = self.attr[-1];
      cp.write("  %s\n" % a.writeCode());
    elif nattr == 1:
      cp.write("  %s\n" % self.attr[0].writeCode());
    cp.write("}\n\n");
    
    # write creation function
    # cp.write("%s *step_create_%s(StepFileLine & line)\n" % (self.name, self.exp));
    cp.write("StepEntity *step_create_%s(StepFileLine & line)\n" % (self.exp));
    cp.write("{\n");
    cp.write("  %s *entity = new %s;\n" % (self.name, self.name));
    cp.write("  entity->read(line);\n");
    cp.write("  return entity;\n");
    cp.write("}\n");
    
    return 1;
      
class step_enum:
  
  def __init__(self, s):
    self.exp = s.strip("; \t\n\r");
    self.name = expToClass(self.exp);
    self.values = [];
    self.isselect = 0;
    
  def append(self, s):
    self.values.append( s.strip("();, \n\t\r") );
  
  def toCpp(self, fp, cp):
    if self.isselect:
      self.toSelectCpp(fp,cp);
    else:
      self.toEnumCpp(fp,cp);
      
  def toEnumCpp(self, hp, cp):
    
    # compute string table dimensions
    lmax = 0;
    lval = len(self.values);
    for v in self.values:
      lmax = max(lmax, len(v)+3);
    
    # write header
    hp.write("class {0} : public StepEnum\n".format(self.name));
    hp.write("{\n  public:\n");
    hp.write("  typedef enum {\n    ");
    s = string.join(self.values, ",\n    ");
    hp.write(s + " } Code;\n");
    hp.write("  public:\n");
    hp.write("    bool read(StepFileLine & line) {\n");
    hp.write("      int iv = 0;\n");
    hp.write("      bool ok = StepEnum::read(line, %d, stringrep, iv);\n" % (lval));
    hp.write("      value = (%s::Code) iv;\n" % (self.name));
    hp.write("      return ok;\n");
    hp.write("    }\n");
    hp.write("    void write(std::ostream & os) const {\n");
    hp.write("      int i = (int) value;\n");
    hp.write("      assert(i < %d);\n" % (lval));
    hp.write("      os << stringrep[i];\n");
    hp.write("    }\n");
    
    tpl = "    bool operator== (const %s & a) const\n" \
    "      {return value == a.value;}\n" \
    "    bool operator!= (const %s & a) const\n" \
    "      {return value != a.value;}\n" % (self.name, self.name);
    hdr.write(tpl);
    tpl = "    bool operator== (const %s::Code & a) const\n" \
    "      {return value == a;}\n" \
    "    bool operator!= (const %s::Code & a) const\n" \
    "      {return value != a;}\n" % (self.name, self.name);
    hdr.write(tpl);
    
    hp.write("  public:\n");
    hp.write("    {0}::Code value;\n".format(self.name));
    hp.write("  private:\n");
    hp.write("    static const char *stringrep[];\n");
    hp.write("};\n\n");
    
    # write implementation
    cp.write("// ------------ {0}\n\n".format(self.name));
    cp.write('const char *%s::stringrep[] = {' % (self.name) );
    for v in self.values:
      cp.write('\n    ".{0}.",'.format(v.upper()));
    cp.write("    };\n\n")
    
  def toSelectCpp(self, hp, cp):
    
    # compute string table dimensions
    lmax = 0;
    lval = len(self.values);
    for v in self.values:
      lmax = max(lmax, len(v)+3);
    
    # write header
    hp.write("class {0} : public StepSelect\n".format(self.name));
    hp.write("{\n  public:\n");
    hp.write("  enum Code {\n    ");
    s = string.join(self.values, ",\n    ");
    hp.write(s + " };\n");
    hp.write("  public:\n");
    hp.write("    %s() : StepSelect() {} \n" % (self.name));
    hp.write("    bool read(StepFileLine & line) {\n");
    hp.write("      bool ok = StepSelect::read(line, %d, stringrep);\n" % (len(self.values)));
    hp.write("      if (ok and keyIndex >= 0) \n");
    hp.write("        value = (%s::Code) keyIndex;\n" % (self.name));
    hp.write("      return (type != NotSet);\n");
    hp.write("    }\n");
    hp.write("    void write(std::ostream & os) const {\n");
    hp.write("      StepSelect::write(os, stringrep);\n");
    hp.write("    }\n");
    
    hp.write("  public:\n");
    hp.write("    {0}::Code value;\n".format(self.name));
    hp.write("  private:\n");
    hp.write("    static const char *stringrep[];\n");
    hp.write("};\n\n");
    
    # write implementation
    cp.write("// ------------ {0}\n\n".format(self.name));
    cp.write('const char *%s::stringrep[] = {' % (self.name) );
    for v in self.values:
      cp.write('\n    "{0}",'.format(v.upper()));
    cp.write("    };\n\n")


# main

fp = open("wg3n916_ap203.exp", 'r');
#fp = open("snippet.exp", 'r');
hdr = open("step_ap203.h", 'w');
cpp = open("step_ap203.cpp", 'w');

current_mode = 0;
mode_entity = 1;
mode_enum = 2;

hdr.write("#ifndef SURF_AP203_H\n");
hdr.write("#define SURF_AP203_H\n\n");
hdr.write("// automatically created by surf/tools/fedex.py -- do not edit\n\n");
hdr.write('#include "step.h"\n');
hdr.write('#include "stepentity.h"\n');
hdr.write("#include <cassert>\n\n");

cpp.write('#include "stepline.h"\n\n');
cpp.write('#include "step_ap203.h"\n\n');
cpp.write("// automatically created by surf/tools/fedex.py -- do not edit\n\n");

base_types = set(["INTEGER", "REAL", "BOOLEAN", "LOGICAL", "STRING"]);

entities_written.add("StepEntity");

for line in fp:
  if current_mode == mode_entity:
    if line.count("END_ENTITY") == 1:
      current_mode = 0;
      # current_entity.toCpp(hdr, cpp);
      entities_waiting.add(current_entity);
      all_entities[current_entity.name] = current_entity;
    else:
      current_entity.append(line.strip());
  elif current_mode == mode_enum:
    if line.count("END_TYPE") == 1:
      current_mode = 0;
      enum_names.add(current_enum.exp);
      current_enum.toCpp(hdr, cpp);
    else:
      current_enum.append(line);
  elif current_mode == 0:
    if line.count(" ENTITY") == 1:
      wds = line.strip().split();
      current_mode = mode_entity;
      current_entity = step_entity(wds[1]);
    elif line.count("= ENUMERATION OF") == 1 or line.count("= SELECT") == 1:
      wds = line.strip().split();
      current_mode = mode_enum;
      current_enum = step_enum(wds[1]);
      if line.count("= SELECT") == 1:
        current_enum.isselect = 1;
        select_names.add( current_enum.name );
    elif line.count(" TYPE") == 1:
      wds = line.strip("; \n\t\r").split();
      if len(wds) == 4:
        if wds[-1] in base_types:
          all_typedefs[wds[1]] = wds[-1];
        elif wds[-1] in all_typedefs:
          all_typedefs[wds[1]] = all_typedefs[wds[-1]];
          
# print len(entities_waiting), " entities not written.";

# insert base class attributes
for e in entities_waiting:
  e.prependAttr(all_entities);

# write waiting entities
while len(entities_waiting) > 0:
  tmp = set();
  for e in entities_waiting:
    if e.toCpp(hdr,cpp) == 1:
      tmp.add(e);
  entities_waiting -= tmp;
  if len(tmp) == 0:
    print len(entities_waiting), " entities not written.";
    break;
  else:
    print len(tmp), "entities written ";

#print select_names

#td_keys = map( string.upper, all_typedefs.keys() );
#for key in td_keys:
#  print '"%s",' % key

#print all_typedefs.values()

fp.close();
hdr.write("#endif\n");
hdr.close();
cpp.close();

hdr = open("stepentitycreator.h", 'w');

# write creator class
hdr.write("#ifndef SURF_STEPENTITYCREATOR_H\n");
hdr.write("#define SURF_STEPENTITYCREATOR_H\n\n");
hdr.write('#include "step.h"\n');
hdr.write('#include "stepentity.h"\n');
hdr.write('#include "stepline.h"\n');
hdr.write('#include <map>\n\n');
hdr.write("// automatically created by surf/tools/fedex.py -- do not edit\n\n");
hdr.write("class StepEntityCreator\n{\npublic:\n");
hdr.write("  StepEntityCreator();\n");
hdr.write("  StepEntity *create(StepFileLine & line, const std::string & key) const;\n");
hdr.write("private:\n");
hdr.write("  typedef std::map<std::string, StepEntityCreatorFunction> FunctionMap;\n")
hdr.write("  FunctionMap fmap;\n};\n");
hdr.write("#endif\n");
hdr.close();

cpp = open("stepentitycreator.cpp", 'w')

cpp.write("// automatically created by surf/tools/fedex.py -- do not edit\n\n");
cpp.write('#include "stepentitycreator.h"\n');
cpp.write('#include "step_ap203.h"\n\n');
cpp.write("// ------------ StepEntityCreator\n\n");
cpp.write("StepEntityCreator::StepEntityCreator()\n{\n");
for kf in creator_table:
  cpp.write('  fmap["%s"] = %s;\n' % (kf[0], kf[1]));
cpp.write("}\n\n");
cpp.write("StepEntity *StepEntityCreator::create(StepFileLine & line, "
          "const std::string & key) const\n{\n");
cpp.write("  StepEntity *ep = 0;\n");
cpp.write("  FunctionMap::const_iterator itr = fmap.find(key);\n");
cpp.write("  if (itr != fmap.end())\n");
cpp.write("    ep = (*(*itr->second))(line);\n");
cpp.write("  return ep;\n");
cpp.write("}\n\n");
cpp.close();


# print creator_table
#print enum_names
