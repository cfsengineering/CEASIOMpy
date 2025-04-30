
/* ------------------------------------------------------------------------
 * file:       dlgsavemesh.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Display mesh details
 * ------------------------------------------------------------------------ */
 
#include <QMessageBox>
#include <genua/trimesh.h>
#include "sumo.h"
#include "dlgsavemesh.h"
 
using namespace std;
 
DlgSaveMesh::DlgSaveMesh(SumoMain *parent, const TriMesh & tg) 
  : QDialog(parent), pMain(parent) 
{
  setupUi(this);
  retranslateUi(this);

  // check if mesh is closed
  msg = tr("<b>Diagnosis</b><hr>");
  msg += tr("Surface mesh is not closed (or multiply connected) at <br>");
  
  bool ism(true);
  const int ne = tg.nedges();
  for (int i=0; i<ne; ++i) {
    int edeg = tg.edegree(i);
    if (edeg != 2) {
      ism = false;
      const TriEdge & e( tg.edge(i) );
      const Vct3 & ps( tg.vertex(e.source()) );
      
      msg += tr("edge %1 of degree %2 between ").arg(i).arg(edeg);
      msg += tr("vertex %1 and ").arg(e.source());
      msg += tr("vertex %1. <br>").arg(e.target());
      msg += tr("Location: %1, %2, %3").arg(ps[0], 0, 'f', 3).arg(ps[1], 0, 'f', 3).arg(ps[2], 0, 'f', 3);
      break;
    }
  }
  
  uint nv = tg.nvertices();
  uint nf = tg.nfaces();
  Real area = tg.area();
  Real volm = tg.volume();
  
  if (ism) {
    lbTopology->setText(tr("closed"));
  } else {
    
    lbTopology->setText(tr("<a href=#msg>not closed</a>"));
  }
    
  lbTriangles->setText(QString::number(nf));
  lbVertices->setText(QString::number(nv));
  lbArea->setText(QString::number(area));
  lbVolume->setText(QString::number(volm));
  
  // connect link in label to message box
  connect(lbTopology, SIGNAL(linkActivated(const QString&)), 
          this, SLOT(showMessage(const QString&)) );
  
  // connect save button to slot
  connect(pbSave, SIGNAL(clicked()), pMain, SLOT(saveSurfaceMesh()));
  connect(pbSave, SIGNAL(clicked()), this, SLOT(close()) );
  
  // if mesh is watertight, allow shortcut to volume mesh 
  if (ism) {
    connect(pbGenVolMesh, SIGNAL(clicked()), 
            pMain, SLOT(generateVolMesh()) );
    connect(pbGenVolMesh, SIGNAL(clicked()), this, SLOT(close()) );
  } else {
    pbGenVolMesh->setEnabled(false);
  }
  
  // show dialog as non-modal so that the user may inspect 
  // the mesh before saving
  setModal(false);
}

void DlgSaveMesh::showMessage(const QString &)
{
  QMessageBox::information(pMain, tr("Mesh not closed"), msg);
}
