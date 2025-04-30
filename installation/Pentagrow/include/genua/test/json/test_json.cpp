
#include <cassert>
#include <genua/json/minijson_reader.hpp>
#include <genua/json/minijson_writer.hpp>
#include <genua/rng.h>
#include <genua/timing.h>
#include <genua/strutils.h>
#include <genua/svector.h>
#include <iostream>
#include <fstream>
#include <exception>
#include <vector>

using namespace std;
using namespace minijson;

struct NodeBase;
typedef std::unique_ptr<NodeBase> NodePtr;
typedef std::vector<NodePtr> NodeArray;

NodePtr retrieve_tree(buffer_context &ctx);

struct NodeBase
{
  NodeBase() : iid(gid++) {}
  long iid = 0;
  long level = 0;
  NodeArray children;
  static int gid;

  enum Code { InternalNode=0, SequenceCode, LockboltCode, RivetCode };

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    // writer.write("type", (int) InternalNode );
    writer.write("type", "Node");
    writer.write("iid", iid);
    writer.write("level", level);
    if (not children.empty()) {
      minijson::array_writer arw = writer.nested_array("children");
      for (const NodePtr &p : children)
        arw.write(p);
      arw.close();
    }
    writer.close();
  }

  virtual void fromJsonField(minijson::buffer_context &ctx,
                             const char *field, minijson::value v)
  {
    if (strcmp(field,"iid") == 0)
      iid = v.as_long();
    else if (strcmp(field,"level") == 0)
      level = v.as_long();
    else if (strcmp(field,"children") == 0) {
      minijson::parse_array(ctx, [&](minijson::value /*c*/)
      {
        NodePtr subtree = retrieve_tree(ctx);
        if (subtree != nullptr)
          children.push_back( std::move(subtree) );
      });
    } else if (v.type() == minijson::Object or v.type() == minijson::Array)
      minijson::ignore(ctx);
  }

  static NodePtr load(const std::string &fname) {
    ifstream in(fname);
    std::vector<char> buffer;
    buffer.reserve(16*4096);
    char c;
    while (in.get(c))
      buffer.push_back(c);
    cout << "Fetched " << buffer.size() << " bytes." << endl;
    minijson::buffer_context ctx(&buffer[0], buffer.size());
    return retrieve_tree(ctx);
  }
};

int NodeBase::gid = 1;

namespace minijson
{

template<>
struct default_value_writer<NodePtr>
{
  void operator()(std::ostream& stream, const NodePtr& p,
                  writer_configuration configuration) const
  {
    p->toJson(stream, configuration);
  }
};

} // namespace minijson

struct Sequence : public NodeBase
{
  Sequence() : NodeBase () {}
  Sequence(long s) : NodeBase(), seq(s) {
    IntRng rng(0, 1 << 20);
    std::generate(std::begin(block), std::end(block), rng);
  }
  long seq = 1;
  long prio = 1;
  int block[7];

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    // writer.write("type", (int) SequenceCode);
    writer.write("type", "Sequence");
    writer.write("iid", iid);
    writer.write("level", level);
    writer.write("seq", seq);
    writer.write("prio", prio);
    writer.write_array("block", std::begin(block), std::end(block));
    if (not children.empty()) {
      minijson::array_writer arw = writer.nested_array("children");
      for (const NodePtr &p : children)
        arw.write(p);
      arw.close();
    }
    writer.close();
  }

  virtual void fromJsonField(minijson::buffer_context &ctx,
                             const char *field, minijson::value v)
  {
    if (strcmp(field,"seq") == 0)
      seq = v.as_long();
    else if (strcmp(field,"prio") == 0)
      prio = v.as_long();
    else if (strcmp(field,"block") == 0) {
      int p = 0;
      minijson::parse_array(ctx, [&](minijson::value a)
      {
        assert(a.type() == minijson::Number);
        if (p < 7)
          block[p++] = a.as_long();
      });
    }
    else
      NodeBase::fromJsonField(ctx, field, v);
  }
};

struct Rivet : public NodeBase
{
  Rivet() : NodeBase() {}
  Rivet(double d, double l) : NodeBase(), dia(d), length(l) {
    IntRng rng(0, 1 << 20);
    std::generate(std::begin(block), std::end(block), rng);
    FloatRng fng(0.0, 1.0);
    std::generate(pos.begin(), pos.end(), fng);
  }
  double dia = 0.0;
  double length = 0.0;
  Vct3 pos;
  int block[72];

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    // writer.write("type", (int) RivetCode);
    writer.write("type", "Rivet");
    writer.write("iid", iid);
    writer.write("dia", dia);
    writer.write("length", length);
    writer.write_array("pos", pos.begin(), pos.end());
    writer.write_array("block", std::begin(block), std::end(block));
    writer.close();
  }

  virtual void fromJsonField(minijson::buffer_context &ctx,
                             const char *field, minijson::value v)
  {
    if (strcmp(field,"iid") == 0)
      iid = v.as_long();
    else if (strcmp(field,"level") == 0)
      level = v.as_long();
    else if (strcmp(field,"dia") == 0)
      dia = v.as_double();
    else if (strcmp(field,"length") == 0)
      length = v.as_double();
    else if (strcmp(field,"pos") == 0) {
      int p = 0;
      minijson::parse_array(ctx, [&](minijson::value a)
      {
        assert(a.type() == minijson::Number);
        if (p < 3)
          pos[p++] = a.as_double();
      });
    } else if (strcmp(field,"block") == 0) {
      int p = 0;
      minijson::parse_array(ctx, [&](minijson::value a)
      {
        assert(a.type() == minijson::Number);
        if (p < 72)
          block[p++] = a.as_long();
      });
    }
    else
      minijson::ignore(ctx);
  }
};

struct Lockbolt : public NodeBase
{
  Lockbolt() : NodeBase () {}
  Lockbolt(double d, double l) : NodeBase(), dia(d), length(l) {
    IntRng rng(0, 1 << 20);
    std::generate(std::begin(block), std::end(block), rng);
    FloatRng fng(0.0, 1.0);
    std::generate(pos.begin(), pos.end(), fng);
  }
  double dia = 0.0;
  double length = 0.0;
  Vct3 pos;
  int block[200];

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    // writer.write("type", (int) LockboltCode );
    writer.write("type", "Lockbolt");
    writer.write("iid", iid);
    writer.write("dia", dia);
    writer.write("length", length);
    writer.write_array("pos", pos.begin(), pos.end());
    writer.write_array("block", std::begin(block), std::end(block));
    writer.close();
  }

  virtual void fromJsonField(minijson::buffer_context &ctx,
                             const char *field, minijson::value v)
  {
    if (strcmp(field,"iid") == 0)
      iid = v.as_long();
    else if (strcmp(field,"level") == 0)
      level = v.as_long();
    else if (strcmp(field,"dia") == 0)
      dia = v.as_double();
    else if (strcmp(field,"length") == 0)
      length = v.as_double();
    else if (strcmp(field,"pos") == 0) {
      int p = 0;
      minijson::parse_array(ctx, [&](minijson::value a)
      {
        assert(a.type() == minijson::Number);
        if (p < 3)
          pos[p++] = a.as_double();
      });
    } else if (strcmp(field,"block") == 0) {
      int p = 0;
      minijson::parse_array(ctx, [&](minijson::value a)
      {
        assert(a.type() == minijson::Number);
        if (p < 200)
          block[p++] = a.as_long();
      });
    }
    else
      minijson::ignore(ctx);
  }
};

// -------------------- Example following VPM structure -----------------------

struct ConfigItem : public NodeBase
{
  ConfigItem() : NodeBase () {}
  string name;

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    writer.write("type", "CI");
    writer.write("iid", iid);
    if (not name.empty())
      writer.write("name", name);
    if (not children.empty()) {
      minijson::array_writer arw = writer.nested_array("children");
      for (const NodePtr &p : children)
        arw.write(p);
      arw.close();
    }
    writer.close();
  }

  virtual void fromJsonField(minijson::buffer_context &ctx,
                             const char *field, minijson::value v)
  {
    if (strcmp(field,"name") == 0)
      name = v.as_string();
    else
      NodeBase::fromJsonField(ctx, field, v);
  }
};

struct DesignSolution : public NodeBase
{
  DesignSolution() : NodeBase () {}
  string name;

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    writer.write("type", "DS");
    writer.write("iid", iid);
    if (not name.empty())
      writer.write("name", name);
    if (not children.empty()) {
      minijson::array_writer arw = writer.nested_array("children");
      for (const NodePtr &p : children)
        arw.write(p);
      arw.close();
    }
    writer.close();
  }

  virtual void fromJsonField(minijson::buffer_context &ctx,
                             const char *field, minijson::value v)
  {
    if (strcmp(field,"name") == 0)
      name = v.as_string();
    else
      NodeBase::fromJsonField(ctx, field, v);
  }
};

struct PartReference : public NodeBase
{
  PartReference() : NodeBase () {}
  string path = "partfile.3dxml";

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    writer.write("type", "Part");
    writer.write("iid", iid);
    writer.write("file", string("partfile") + str(iid) + ".3dxml");
    writer.close();
  }

  virtual void fromJsonField(minijson::buffer_context &ctx,
                             const char *field, minijson::value v)
  {
    if (strcmp(field,"iid") == 0)
      iid = v.as_long();
    else if (strcmp(field,"level") == 0)
      level = v.as_long();
    else if (strcmp(field,"file") == 0)
      path = v.as_string();
    else
      minijson::ignore(ctx);
  }
};

struct Fastener : public NodeBase
{
  Fastener() : NodeBase() {
    FloatRng fng(0.0, 1.0);
    std::generate(pos.begin(), pos.end(), fng);
    std::generate(dir.begin(), dir.end(), fng);
  }
  Fastener(double d, double l) : NodeBase(), dia(d), length(l) {
    FloatRng fng(0.0, 1.0);
    std::generate(pos.begin(), pos.end(), fng);
    std::generate(dir.begin(), dir.end(), fng);
  }
  double dia = 0.0;
  double length = 0.0;
  string fastenerClass = "Lockbolt";
  string fastenerModel = "HL510AZ";
  string name = "";
  Vct3 pos, dir;

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    // writer.write("type", (int) RivetCode);
    writer.write("type", "F");
    writer.write("class", fastenerClass);
    writer.write("model", fastenerModel);
    writer.write("iid", iid);
    writer.write("diameter", dia);
    writer.write("length", length);
    writer.write_array("location", pos.begin(), pos.end());
    writer.write_array("direction", dir.begin(), dir.end());
    writer.close();
  }

  virtual void fromJsonField(minijson::buffer_context &ctx,
                             const char *field, minijson::value v)
  {
    if (strcmp(field,"iid") == 0)
      iid = v.as_long();
    else if (strcmp(field,"level") == 0)
      level = v.as_long();
    else if (strcmp(field,"diameter") == 0)
      dia = v.as_double();
    else if (strcmp(field,"length") == 0)
      length = v.as_double();
    else if (strcmp(field,"class") == 0)
      fastenerClass = v.as_string();
    else if (strcmp(field,"model") == 0)
      fastenerModel = v.as_string();
    else if (strcmp(field,"location") == 0) {
      int p = 0;
      minijson::parse_array(ctx, [&](minijson::value a)
      {
        assert(a.type() == minijson::Number);
        if (p < 3)
          pos[p++] = a.as_double();
      });
    } else if (strcmp(field,"direction") == 0) {
      int p = 0;
      minijson::parse_array(ctx, [&](minijson::value a)
      {
        assert(a.type() == minijson::Number);
        if (p < 3)
          dir[p++] = a.as_double();
      });
    }
    else
    minijson::ignore(ctx);
  }
};

struct FastenerGroup : public NodeBase
{
  FastenerGroup() : NodeBase() {}
  string name;

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    writer.write("type", "STD");
    writer.write("iid", iid);
    writer.write("level", level);
    if (not name.empty())
      writer.write("name", name);
    if (not children.empty()) {
      minijson::array_writer arw = writer.nested_array("children");
      for (const NodePtr &p : children)
        arw.write(p);
      arw.close();
    }
    writer.close();
  }

  virtual void fromJsonField(minijson::buffer_context &ctx,
                             const char *field, minijson::value v)
  {
    if (strcmp(field,"name") == 0)
      name = v.as_string();
    else
      NodeBase::fromJsonField(ctx, field, v);
  }
};

struct PartGroup : public NodeBase
{
  PartGroup() : NodeBase() {}

  virtual void toJson(std::ostream& stream,
                      writer_configuration configuration) const
  {
    minijson::object_writer writer(stream, configuration);
    writer.write("type", "BFH");
    writer.write("iid", iid);
    writer.write("level", level);
    if (not children.empty()) {
      minijson::array_writer arw = writer.nested_array("children");
      for (const NodePtr &p : children)
        arw.write(p);
      arw.close();
    }
    writer.close();
  }
};

NodePtr make_sequence(int s, int n)
{
  FloatRng rng(3.4, 12.9);
  Sequence *root = new Sequence(s);
  root->children.resize(n);
  for (int i=0; i<n; ++i) {
    if (i%4 != 0) {
      root->children[i] = NodePtr( new Rivet(4.0, rng()) );
    } else {
      root->children[i] = NodePtr( new Lockbolt(6.0, rng()) );
    }
  }
  return NodePtr(root);
}

NodePtr make_branch(int l)
{
  IntRng rng(2,9);
  if (l <= 0)
    return make_sequence(rng(), 7);

  NodeBase *root = new NodeBase;
  root->level = l;
  int m = rng();
  root->children.resize(m);
  for (int j=0; j<m; ++j)
    root->children[j] = make_branch(l-1);

  return NodePtr(root);
}

NodePtr make_fgroup(int n)
{
  FloatRng rng(3.4, 12.9);
  FastenerGroup *root = new FastenerGroup;
  root->name = "V5324415STD" + str(root->iid);
  root->children.resize(n);
  Fastener *pf = nullptr;
  for (int i=0; i<n; ++i) {
    pf = new Fastener;
    pf->length = rng();
    if (i%4 != 0) {
      pf->dia = 4.8;
      pf->fastenerClass = "Rivet";
      pf->fastenerModel = "NAS1097";
    } else {
      pf->dia = 6.4;
      pf->fastenerClass = "Lockbolt";
    }
    root->children[i] = NodePtr(pf);
  }
  return NodePtr(root);
}

NodePtr make_plmtree(int l)
{
  {
    IntRng rng(7,39);
    if (l <= 0)
      return make_fgroup(rng());
  }

  ConfigItem *root = new ConfigItem;
  root->name = "MS53.4CI" + str(root->iid);
  root->level = l;

  IntRng rng(3,9);
  int m = rng();
  root->children.resize(m);
  for (int j=0; j<m; ++j) {
    DesignSolution *pds = new DesignSolution;
    pds->name = "W53.4DS" + str(pds->iid);
    int n = rng();
    pds->children.resize(n);
    for (int k=0; k<n; ++k)
      pds->children[k] = make_plmtree(l-1);
    root->children[j] = NodePtr(pds);
  }

  return NodePtr(root);
}


NodePtr retrieve_tree(buffer_context &ctx)
{
  NodeBase *node = nullptr;
  minijson::parse_object(ctx, [&](const char* name, minijson::value v)
  {
    if (strcmp(name, "type") == 0) {
      const char *vs = v.as_string();
      if (strcmp(vs, "Node") == 0)
        node = new NodeBase;
      else if (strcmp(vs, "Sequence") == 0)
        node = new Sequence;
      else if (strcmp(vs, "Rivet") == 0)
        node = new Rivet;
      else if (strcmp(vs, "Lockbolt") == 0)
        node = new Lockbolt;
      else if (strcmp(vs, "DS") == 0)
        node = new DesignSolution;
      else if (strcmp(vs, "CI") == 0)
        node = new ConfigItem;
      else if (strcmp(vs, "F") == 0)
        node = new Fastener;
      else if (strcmp(vs, "Part") == 0)
        node = new PartReference;
      else if (strcmp(vs, "STD") == 0)
        node = new FastenerGroup;
      else if (strcmp(vs, "BFH") == 0)
        node = new PartGroup;
      else
        node = nullptr;
      //      assert(v.type() == minijson::Number);
      //      switch (v.as_long()) {
      //      case NodeBase::InternalNode:
      //        node = new NodeBase;
      //        break;
      //      case NodeBase::SequenceCode:
      //        node = new Sequence;
      //        break;
      //      case NodeBase::RivetCode:
      //        node = new Rivet;
      //        break;
      //      case NodeBase::LockboltCode:
      //        node = new Lockbolt;
      //        break;
      //      default:
      //        node = nullptr;
      //      }
    } else {
      if (node != nullptr)
        node->fromJsonField(ctx, name, v);
      else
        minijson::ignore(ctx);
    }
  });
  return NodePtr(node);
}



int main(int argc, char *argv[])
{
  try {

    int depth = 3;
    if (argc > 1)
      depth = atoi(argv[1]);

    const char *fname = "object1.json";
    std::vector<double> wval{0.1, 0.0, 0.87};

    // test writer
    {
      ofstream os(fname);
      minijson::normalize_stream_settings(os);
      minijson::object_writer w(os,
                                minijson::writer_configuration()
                                .pretty_printing(true).indent_spaces(2));
      w.write("tag", "IntegratedResults");
      w.write("alpha", 4.5);
      w.write("Mach", 0.87);
      w.write_array("Coefficients", wval.begin(), wval.end());
      w.close();
      os.flush();
      os.close();
    }

    // test reader
    {
      ifstream in(fname);
      minijson::istream_context ctx(in);
      minijson::parse_object(ctx, [&](const char *name, minijson::value v){
        minijson::dispatch(name)
            <<"alpha">> [&]{ cout << "Alpha found: " << v.as_double() << endl; }
        <<"Mach">> [&]{ cout << "Mach found: " << v.as_double() << endl; }
        <<"Coefficients">> [&]
        {
          cout << "Coef: ";
          minijson::parse_array(ctx, [&](value va)
          {
            cout << va.as_double() << ", ";
          });
          cout << endl;
        }
        <<minijson::any>> [&]{ minijson::ignore(ctx); };
      });
    }

    Wallclock clk;
    clk.start();
    NodePtr root = make_plmtree(depth);
    clk.stop();
    cout << "Tree created: " << clk.elapsed() << endl;

    clk.start();
    {
      ofstream os("prettytree.json");
      minijson::normalize_stream_settings(os);
      writer_configuration cfg;
      root->toJson(os, cfg.pretty_printing(true).indent_spaces(2));
      os.flush();
      os.close();
    }
    clk.stop();
    cout << "Tree written prettily: " << clk.elapsed() << endl;

    clk.start();
    {
      ofstream os("densetree.json");
      minijson::normalize_stream_settings(os);
      writer_configuration cfg;
      root->toJson(os, cfg);
      os.flush();
      os.close();
    }
    clk.stop();
    cout << "Tree written densely: " << clk.elapsed() << endl;

    NodePtr reload;
    clk.start();
    {
      try {
        reload = NodeBase::load("densetree.json");
      } catch (minijson::parse_error &error) {
        cerr << "Parse error: " << error.what() << endl
             << " at " << error.offset() << endl;

      }
    }
    clk.stop();
    cout << "Loading tree from dense file: " << clk.elapsed() << endl;

    if (reload != nullptr) {
      ofstream os("reloaded.json");
      minijson::normalize_stream_settings(os);
      writer_configuration cfg;
      reload->toJson(os, cfg.pretty_printing(true).indent_spaces(2));
      os.flush();
      os.close();
    }

  } catch (runtime_error &xcp) {
    cerr << xcp.what() << endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;

  return 0;
}
