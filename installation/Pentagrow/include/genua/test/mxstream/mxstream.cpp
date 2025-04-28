
// test streaming output

#include <genua/mxmesh.h>
#include <genua/xcept.h>
#include <genua/strutils.h>
#include <genua/mxstreamer.h>
#include <genua/mxsolutiontree.h>

#include <iostream>

using namespace std;

MxMeshPtr create_big_mesh(size_t nv, size_t ne)
{
  MxMeshPtr mxp = boost::make_shared<MxMesh>();

  mxp->appendNodes( PointList<3>(nv) );

  // keep indices in range, cgns may check index range...
  Indices idx(4*ne);
  for (size_t i=0; i<4*ne; ++i)
    idx[i] = lrand48() % nv;

  mxp->appendSection( Mx::Tet4, idx );
  return mxp;
}

int main(int argc, char *argv[])
{
  try {

    MxStreamer stream;

    const size_t nv = 1000;
    MxMeshPtr pmx = create_big_mesh(nv, 5*nv);

    {
      stream.open("streamed.zml", pmx.get());

      MxSolutionTreePtr tree[4], root;
      root = boost::make_shared<MxSolutionTree>("Subcases");
      for (int k=0; k<4; ++k) {
        tree[k] = boost::make_shared<MxSolutionTree>("Case "+str(k+1));
        root->append(tree[k]);
      }

      const size_t nf = 4;
      for (size_t i=0; i<nf; ++i) {
        Vector field(nv);
        field = Real(i+1);
        string fieldName = "Field "+str(i+1);
        size_t idx = stream.append(fieldName, field);
        tree[idx%4]->appendField(idx);

        pmx->appendField(fieldName, field);
      }

      stream.append(*root);
      stream.close();

      pmx->solutionTree(root);
      pmx->toXml(true).toGbf(true)->write("check.zml", BinFileNode::CompressedLZ4);
    }

    {
      BinFileNodePtr bfp = BinFileNode::read("streamed.zml");
      if (bfp) {
        XmlElement xe;
        xe.fromGbf(bfp, true);
        xe.write("streamed_xmlelement.xml");
      }
    }

    {
      BinFileNodePtr bfp = BinFileNode::read("streamed.zml");
      if (not bfp)
        throw Error("Failed to read bfp at all.");

      bfp->summary(cout);

      XmlElement xe;
      xe.fromGbf(bfp, true);

      MxMesh imp;
      imp.fromXml(xe);

      cout << "Re-import:" << endl;
      cout << imp.nnodes() << " nodes, "
           << imp.nelements() << " elements" << endl;
      cout << imp.nfields() << " fields." << endl;
      MxSolutionTreePtr pst = imp.solutionTree();
      if (pst)
        cout << "Tree: " << pst->name();
      else
        cout << "No tree." << endl;
      imp.toXml(true).toGbf(true)->write("reimport.zml",
                                         BinFileNode::CompressedLZ4);
    }

  } catch (Error & xcp) {
    cerr << xcp.what() << endl;
    return -1;
  }
  
  return 0;
}
