#! /usr/bin/python

import string;

def collect(file):
  s = open(file,"r").read();
  pos = string.find(s, "void");
  lpos = string.find(s, "CVT_TRANSPOSE");
  s = s[pos:lpos];
  lst = string.split(s, "void");
  fns = [];
  for s in lst:
    pos = string.find(s,";");
    t = string.replace(s[0:pos],"\n","");
    fns.append(string.strip(t));
  # print "found ", len(fns), " functions."
  return lst;

def transfname(s):
  pos = string.find(s, "(");
  st = string.strip(s[0:pos]);
  end = string.find(s,";");
  arglist = s[pos:end];
  if st[-1:] == "_":
    su = st[1:-1];
  else:
    su = st[1:];
  tpl = (st,su,arglist);
  return tpl;

def foverload(f1, f2, arglist):
  p1 = string.find(arglist,"(") + 1;
  p2 = string.find(arglist,")");
  s = string.replace(arglist[p1:p2],"\n","");
  s = string.strip(s);
  words = string.split(s,",");
  tp = [];
  nalist = "";
  for w in words:
    w = string.strip(w);
    if len(nalist) == 0:
      nalist = w;
    else:
      nalist = nalist + ", " + w;
    wds = string.split(w);
    if len(wds) < 2:
      continue;
    #print "words: ", wds
    vname = wds[-1];
    p2 = string.find(vname,"[");
    if p2 > 0:
      vname = vname[:p2];
    tname = string.join(wds[:-1]);
    #print "Type: " , tname, "  Variable: ", vname
    t = (tname,vname);
    tp.append(t);
  if len(tp) > 0:
		fn = "inline void " + f2 + "(" + nalist + ") \n";
		fn = fn + "  {" + f1 + "(";
		fn = fn + tp[0][1];
		for t in tp[1:]:
			fn = fn + ", " + t[1];
		fn = fn + ");}\n"
		return fn;


l = collect("lapack_interface.h");
print "// automatically generated overloaded functions for the lapack interface"
print "// do not edit: use the script genua/tools/lapacktrans.py to regenerate"
print "// (c) 2004 by David Eller david.eller@gmx.net "
print
for s in l:
  (f1,f2,arglist) = transfname(s);
  fn = foverload(f1,f2,arglist);
  if fn:
    print fn;
