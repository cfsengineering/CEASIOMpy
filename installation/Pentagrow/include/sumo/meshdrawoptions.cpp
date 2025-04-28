
/* ------------------------------------------------------------------------
 * file:       meshdrawoptions.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Modify settings for TriMeshView
 * ------------------------------------------------------------------------ */

#include "trimeshview.h"
#include "meshdrawoptions.h"
#include <genua/plane.h>

MeshDrawOptions::MeshDrawOptions(TriMeshView *v) : QDialog(v), tmv(v)
{
  setupUi(this);
  retranslateUi(this);
  
  QDialog::setModal(false);
  
  cbDrawPolygons->setChecked( tmv->drawPolygonFlag() );
  cbDrawEdges->setChecked( tmv->drawEdgeFlag() );
  cbDrawNormals->setChecked( tmv->drawNormalFlag() );
  cbDrawCut->setChecked( tmv->drawCutFlag() );
  rbOrthographic->setChecked( tmv->orthoCamera() );

  sbDistance->setValue( tmv->cutPlaneDistance() );
  const Vct3 & cpn( tmv->cutPlaneNormal() );
  Real nx = fabs(cpn[0]);
  Real ny = fabs(cpn[1]);
  Real nz = fabs(cpn[2]);
  if ( nx > ny and nx > nz )
    rbYZPlane->setChecked(true);
  else if (ny > nx and ny > nz)
    rbXZPlane->setChecked(true);
  else 
    rbXYPlane->setChecked(true);
  
  connect(pbApply, SIGNAL(clicked()), this, SLOT(applyChanges()));
  connect(pbOK, SIGNAL(clicked()), this, SLOT(applyChanges()));
}

void MeshDrawOptions::execute()
{
  QDialog::show();
}

void MeshDrawOptions::applyChanges()
{
  if (tmv == 0)
    return;
  
  tmv->toggleDrawPolygons( cbDrawPolygons->isChecked() );
  tmv->toggleDrawEdges( cbDrawEdges->isChecked() );
  tmv->toggleDrawNormals( cbDrawNormals->isChecked() );
  tmv->toggleDrawCut( cbDrawCut->isChecked() );
  
  if (cbDrawCut->isChecked()) {
    double dst = sbDistance->value();
    if (rbXYPlane->isChecked())
      tmv->cuttingPlane( Plane(vct(0,0,1), dst) );
    else if (rbXZPlane->isChecked())
      tmv->cuttingPlane( Plane(vct(0,1,0), dst) );
    else if (rbYZPlane->isChecked())
      tmv->cuttingPlane( Plane(vct(1,0,0), dst) );
  }
  
  tmv->toggleOrthoCamera( rbOrthographic->isChecked() );
  tmv->updateMeshCut();
}


