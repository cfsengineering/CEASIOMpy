
/* ------------------------------------------------------------------------
 * file:       exporttritet.cpp
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog to adjust settings for TRITET boundary mesh export
 * ------------------------------------------------------------------------ */
 
#include <QString>
#include <QFileDialog>
#include <surf/tetmesh.h>
#include <genua/ioglue.h>
#include "util.h"
#include "assembly.h"
#include "exporttritet.h"

#include <QDebug>

using std::string;

ExportTritet::ExportTritet(QWidget *parent, Assembly & mdl) :
            QDialog(parent), asy(mdl), twt(asy.mesh())
{
  setupUi( this );
  retranslateUi( this );
  
  cbFormat->clear();
  cbFormat->addItem("TetGen (.smesh)");
  cbFormat->addItem("TRITET (.dat)");
  
  // define engine boundaries 
  const int ne(asy.njet());
  for (int i=0; i<ne; ++i) {
    const JetEngineSpec & js(asy.jetEngine(i));
    twt.setBoundary( js.name()+"Intake", js.intakeElements() );
    twt.setBoundary( js.name()+"Nozzle", js.nozzleElements() );
  }
  
  // determine default dimensions
  const TriMesh & bmesh(asy.mesh());
  Real barea = bmesh.area();
  Real rinit = sqrt(barea) * 8;
  sbFfRadius->setValue(rinit);
  
  connect( sbFfRefineLevel, SIGNAL(valueChanged(int)),
           this, SLOT(updateTriangleCount(int)) );
 
  updateTriangleCount(sbFfRefineLevel->value());
}

bool ExportTritet::execute(const QString & lastdir)
{
  if (QDialog::exec() == QDialog::Accepted) {
    
    string csname = str(leCaseName->text());
    if (csname.empty())
      csname = "Case1";
    twt.caseName(csname);
    
    if (rbSphereFarfield->isChecked()) {
      double radius = sbFfRadius->value();
      int nref = sbFfRefineLevel->value();
      twt.sphericalFarfield(radius, nref);
    }
    
    QString caption = tr("Save mesh to file");
    QString filter;
    if (cbFormat->currentIndex() == 0)
      filter = tr("Tetgen boundary mesh (*.smesh);; "
                  "Tritet boundary mesh (*.dat);; All files (*)");
    else
      filter = tr("Tritet boundary mesh (*.dat);; "
                  "Tetgen boundary mesh (*.smesh);; All files (*)");
    
    QString fn = QFileDialog::getSaveFileName(this, caption, lastdir, filter);
    if (not fn.isEmpty()) {

      if (cbFormat->currentIndex() == 0) {
        TetMesh & tvm( asy.volumeMesh() );
        tvm.clear();

        qDebug("Boundary export: initialising boundaries...");
        asy.initMeshBoundaries( sbFfRadius->value(),
                                sbFfRefineLevel->value() );

        // write smesh file to tmp directory
        qDebug("smesh Boundaries: %d Triangles: %d",
               tvm.nboundaries(), tvm.nfaces());
        tvm.writeSmesh(str(fn));

        // twt.writeTetgen(os);
      } else {

        qDebug("TRITET export.");

        ofstream os(asPath(fn).c_str());
        twt.write(os);
      }
    } else {
      return false;
    }
    
  } else {
    return false;
  }
  return true;
}

void ExportTritet::updateTriangleCount(int)
{
  uint nref = sbFfRefineLevel->value();
  uint ntri = 20u * uint( pow(4.0, double(nref)) );
  lbTriCount->setText( QString::number(ntri) );
}



