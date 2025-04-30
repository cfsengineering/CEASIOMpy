
/* ------------------------------------------------------------------------
 * file:       renderview.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * 3D View widget for surfaces
 * ------------------------------------------------------------------------ */

#include "glew.h"
#include "renderview.h"
#include "transformationdialog.h"
#include "pool.h"
#include "util.h"
#include "fitindicator.h"
#include "spacenav/spacemouseinterface.h"
#include <boost/bind.hpp>
#include <genua/threadpool.h>
#include <genua/sysinfo.h>
#include <genua/timing.h>
#include <genua/zipfile.h>
#include <genua/cgnsfile.h>
#include <surf/igesfile.h>
#include <surf/stepfile.h>
#include "frameprojector.h"
#include <QMouseEvent>
#include <QMessageBox>
#include <QStringList>
#include <QFileDialog>

using namespace std;
using namespace qglviewer;

RenderView::RenderView(QGLContext *, QWidget *parent, AssemblyPtr pm)
  : QGLViewer(parent), model(pm), bShown(false), bGlInitialized(false)
{
  vLo.setValue(-1.0f, -1.0f, -1.0f);
  vHi.setValue(1.0f, 1.0f, 1.0f);

  // default colors
  cPolygon = Qt::gray;
  cLine = Qt::red;

  // construct help string
  shelp = tr("<h2> 3D view page </h2>");
  shelp += tr("<b>Short instructions:</b>"
              "Use the left mouse button to rotate, middle button to zoom "
              "and right button to pan. Find detailed instructions on the "
              "tab pages of this window. ");
  
  // undefined display list
  iDisplayList = NotFound;

  // internal dialogs
  trafoDlg = 0;

  framePj.reset( new FrameProjector );
  findic.reset( new FitIndicator );
}

RenderView::~RenderView()
{
  if (iDisplayList != NotFound) {
    QGLWidget::makeCurrent();
    glDeleteLists(iDisplayList, 1);
  }
}

void RenderView::setModel(AssemblyPtr pm)
{
  model = pm;
  bShown = false;
  findic->assign(model);
  updateGeometry();
}

void RenderView::loadAnyOverlay(const QStringList &files)
{
  if (files.isEmpty())
    return;

  if (files.size() > 1) {
    postStatusMsg(tr("Multiple overlay files: Interpreted as STL model."));
    loadStlOverlay(files);
  } else {
    const QString & file(files[0]);
    std::string fname = str(file);

    // first, try to instantiate a MxMesh in native format
    if (file.endsWith(".zml")) {
      postStatusMsg(tr("Importing overlay from native compressed format."));
      loadXmlOverlay(file);
    } else if (ZipFile::isZip(fname)) {
      postStatusMsg(tr("Zipped file: Interpreted as compressed XML overlay."));
      loadXmlOverlay(file);
    } else if (StepFile::isStepFile(fname)) {
      postStatusMsg(tr("ISO-10303 recognized: Interpreted as STEP AP203 overlay."));
      loadStepOverlay(file);
    } else if ( CgnsFile::isCgns(fname) ) {
      postStatusMsg(tr("CGNS file recognized: Importing surfaces from mesh."));
      loadMeshOverlay(file);
    } else if ( file.endsWith(".bmsh") ) {
      postStatusMsg(tr("Assuming EDGE .bmsh file, importing surfaces from mesh."));
      loadMeshOverlay(file);
    } else if ( IgesFile::isIges(fname) ) {
      postStatusMsg(tr("Imported file interpreted as IGES."));
      loadIgesOverlay(file);
    } else if ( file.endsWith(".stl") or file.endsWith(".STL") ) {
      postStatusMsg(tr("Assuming STL file."));
      loadStlOverlay(files);
    } else {
      QMessageBox::warning(this, tr("Cannot import overlay"),
                           tr("File format for overlay file"
                              " not recognized. Please select a format from"
                              " the list in the file selection dialog.") );
    }
  }
}

void RenderView::loadIgesOverlay(const QString & fname)
{
  if (not IgesFile::isIges(str(fname))) {
    QMessageBox::warning(this, tr("Cannot import IGES overlay"),
                         tr("Selected file does not appear to be an"
                            " IGES file.") );
    return;
  }

  try {
    IgesFile file;
    file.read( str(fname) );
    ovldisp.tesselate(file);
  } catch (Error & xcp) {
    QMessageBox::warning(this, tr("Cannot import IGES overlay"),
                         tr("Problem importing IGES file:") +
                         QString::fromStdString(xcp.what()) );
    return;
  } catch (std::bad_alloc) {
    QMessageBox::warning(this, tr("Cannot import IGES overlay"),
                         tr("Problem importing IGES file: Out of memory.") );
    return;
  }

  if (trafoDlg != 0)
    trafoDlg->setTrafo( ovldisp.currentTrafo() );
  updateGeometry();
  buildProjector();
  fitScreen();
}

void RenderView::loadStepOverlay(const QString & fname)
{
  try {
    StepFile file;
    file.read( str(fname) );
    ovldisp.tesselate(file);
  } catch (Error & xcp) {
    QMessageBox::warning(this, tr("Cannot import STEP overlay"),
                         tr("Problem importing STEP file:") +
                         QString::fromStdString(xcp.what()) );
    return;
  } catch (std::bad_alloc) {
    QMessageBox::warning(this, tr("Cannot import STEP overlay"),
                         tr("Problem importing STEP file: Out of memory.") );
    return;
  }

  if (trafoDlg != 0)
    trafoDlg->setTrafo( ovldisp.currentTrafo() );

  Wallclock clk;

  clk.start();
  updateGeometry();
  clk.stop();
  qDebug("Geometry update: %f", clk.elapsed());

  buildProjector();
  fitScreen();
  qDebug("Leaving loadStepOverlay...");
}

void RenderView::loadMeshOverlay(const QString &fname)
{
  try {

    std::string fileName = str(fname);
    if (CgnsFile::isCgns(fileName)) {
      ovldisp.fromCGNS( fileName );
    } else if (fname.endsWith(".bmsh")) {
      ovldisp.fromBmsh( fileName );
    } else {
      QMessageBox::warning(this, tr("Cannot import mesh overlay"),
                           tr("Mesh file format not recognized or "
                              "not supported."));
      return;
    }

  } catch (Error & xcp) {
    QMessageBox::warning(this, tr("Cannot import mesh overlay"),
                         tr("Problem importing mesh file:") +
                         QString::fromStdString(xcp.what()) );
    return;
  } catch (std::bad_alloc) {
    QMessageBox::warning(this, tr("Cannot import mesh overlay"),
                         tr("Problem importing mesh file: Out of memory.") );
    return;
  }

  if (trafoDlg != 0)
    trafoDlg->setTrafo( ovldisp.currentTrafo() );

  Wallclock clk;

  clk.start();
  updateGeometry();
  clk.stop();
  qDebug("Geometry update: %f", clk.elapsed());

  buildProjector();
  fitScreen();
  qDebug("Leaving loadMeshOverlay...");
}

void RenderView::loadStlOverlay(const QStringList &files)
{
  const int nfile = files.size();
  StringArray fileNames(nfile);
  for (int i=0; i<nfile; ++i)
    fileNames[i] = str(files[i]);

  try {
    ovldisp.fromSTL(fileNames);
  } catch (Error & xcp) {
    QMessageBox::warning(this, tr("Cannot import STL overlay"),
                         tr("Problem importing STL files: ") + files.join(", ")
                         + tr(": %1").arg( QString::fromStdString(xcp.what()) ) );
    return;
  } catch (std::bad_alloc) {
    QMessageBox::warning(this, tr("Cannot import STL overlay"),
                         tr("Problem importing STL files: Out of memory.") );
    return;
  }

  if (trafoDlg != 0)
    trafoDlg->setTrafo( ovldisp.currentTrafo() );
  updateGeometry();
  buildProjector();
  fitScreen();
}

void RenderView::loadXmlOverlay(const QString &fname)
{
  try {
    XmlElement xe;
    xe.read( str(fname) );
    if (xe.name() == "Product" or xe.name() == "MxMesh") {
      ovldisp.fromXml(xe);
    } else {
      XmlElement::const_iterator itr = xe.findChild("Product");
      if (itr != xe.end())
        ovldisp.fromXml(*itr);
      else
        QMessageBox::warning(this, tr("Cannot load overlay"),
                             tr("Unsupported XML format:") +
                             QString::fromStdString(xe.name()) );
    }

  } catch (Error & xcp) {
    QMessageBox::warning(this, tr("Cannot load overlay"),
                         tr("Problem loading overlay from XML/ZML file:") +
                         QString::fromStdString(xcp.what()) );
    return;
  } catch (std::bad_alloc) {
    QMessageBox::warning(this, tr("Cannot load overlay"),
                         tr("Problem loading overlay: Out of memory.") );
    return;
  }

  if (trafoDlg != 0)
    trafoDlg->setTrafo( ovldisp.currentTrafo() );
  updateGeometry();
  buildProjector();
  fitScreen();
}

void RenderView::saveOverlayAs()
{
  QString caption = tr("Select file for overlay geometry");
  QString filter = tr("Compressed XML (*.zml);;"
                      "All files (*)");
  QString selfilter;
  QString lastdir = QFileInfo(ovlFileName).absolutePath();
  QString fn = QFileDialog::getSaveFileName(this, caption, lastdir,
                                            filter, &selfilter);
  if (fn.isEmpty())
    return;

  ovlFileName = fn;

  try {

    // debug
    cout << "output tf: " << ovldisp.currentTrafo();

    ovldisp.toXml(true).zwrite( str(ovlFileName), 0 );
  } catch (Error & xcp) {
    QString msg;
    msg  = tr("<b>Problem saving overlay file: '")+ovlFileName+"'.</b>\n";
    msg += tr("Error message: ")+qstr(xcp.what());
    QMessageBox::information( this, "sumo", msg);
    return;
  }
}

void RenderView::saveOverlay()
{
  // when called w/o overlay filename, let user choose one
  if (ovlFileName.isEmpty())
    saveOverlayAs();

  // if cancelled, do not try to save
  if (ovlFileName.isEmpty())
    return;

  try {

    // debug
    cout << "output tf: " << ovldisp.currentTrafo();

    ovldisp.toXml(true).zwrite( str(ovlFileName), 0 );
  } catch (Error & xcp) {
    QString msg;
    msg  = tr("<b>Problem saving overlay file: '")+ovlFileName+"'.</b>\n";
    msg += tr("Error message: ")+qstr(xcp.what());
    QMessageBox::information( this, "sumo", msg);
    return;
  }
}

void RenderView::buildProjector()
{
  try {
    ovldisp.rebuildProjector(*framePj);
    framePj->transformation( ovldisp.currentTrafo() );
  } catch (Error & xcp) {
    framePj->clear();
    QMessageBox::warning(this, tr("Cannot construct projector."),
                         tr("Problem when constructing CAD geometry projector: ") +
                         QString::fromStdString(xcp.what()) );
  } catch (std::bad_alloc) {
    QMessageBox::warning(this, tr("Cannot construct projector."),
                         tr("Problem when constructing CAD geometry projector: Out of memory.") );
    return;
  }
}

void RenderView::updateProjector()
{
  framePj->transformation( ovldisp.currentTrafo() );
}

void RenderView::init()
{
  QGLWidget::makeCurrent();
  if (QGLContext::currentContext() == 0)
    return;

  // must initialize GLEW once we have a context
  GLenum err = glewInit();
  if (err != GLEW_OK) {
    cerr << "GLEW initialization failed." << glewGetErrorString(err) << endl;
    abort();
  }

  QGLViewer::camera()->setType(Camera::PERSPECTIVE);
  QGLViewer::setBackgroundColor(QColor(255, 255, 255));
  QGLViewer::setMouseBinding(Qt::LeftButton + Qt::SHIFT, RAP_FROM_PIXEL, true);

  glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
  glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE);
  glEnable(GL_DEPTH_TEST);
  glEnable(GL_NORMALIZE);
  glEnable(GL_LINE_SMOOTH);
  glEnable(GL_BLEND);
  glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
  glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
  glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

  bGlInitialized = true;
  emit viewerInitialized();
}

void RenderView::buildDisplayList()
{
  QGLWidget::makeCurrent();
  if (not bGlInitialized) {
    if (QGLContext::currentContext())
      initializeGL();
    if (not bGlInitialized)
      return;
  }

  if (not model)
    return;
  
  // ovldisp.initDisplay();
  if (iDisplayList != NotFound)
    glDeleteLists(iDisplayList, 1);
  iDisplayList = glGenLists(1);
  glNewList(iDisplayList, GL_COMPILE);

  const int nc = model->ncomponents();

  // compute grids for drawing in parallel
  if (SysInfo::nthread() > 1) {

#pragma omp parallel for schedule(dynamic)
    for (int i=0; i<nc; ++i)
      model->sumoComponent(i)->updateVizGrid();

  } else {
    for (int i=0; i<nc; ++i)
      model->sumoComponent(i)->updateVizGrid();
  }

  // we cannot draw in parallel as OpenGL may only be accessed
  // by one thread at a time (global state)
  for (int i=0; i<nc; ++i)
    model->sumoComponent(i)->glDraw();
  model->ctsystem().draw();
  
  glEndList();

  Wallclock clk;
  clk.start("Overlay::build()...");
  if (trafoDlg != 0)
    ovldisp.applyTrafo( trafoDlg->currentTrafo() );
  ovldisp.build();
  clk.stop("s");
}

void RenderView::draw()
{
  QGLWidget::makeCurrent();
  if (not bGlInitialized) {
    if (QGLContext::currentContext())
      initializeGL();
    if (not bGlInitialized)
      return;
  }

  glCallList(iDisplayList);
  if (not bShown) {
    QGLViewer::showEntireScene();
    bShown = true;
  }

  ovldisp.draw();
  findic->draw();
}

void RenderView::updateGeometry()
{
  Wallclock clk;

  clk.start();
  buildDisplayList();
  clk.stop();
  cout << "Build display list: " << clk.elapsed() << endl;

  updateSceneDimensions();
  repaint();
}

void RenderView::updateSceneDimensions()
{
  if (not model)
    return;
  
  // find a tight bounding box
  float flo[3], fhi[3];
  flo[0] = flo[1] = flo[2] = 1e18f;
  fhi[0] = fhi[1] = fhi[2] = -1e18f;
  for (uint i=0; i<model->nbodies(); ++i)
    model->body(i)->extendBoundingBox(flo, fhi);
  for (uint i=0; i<model->nwings(); ++i)
    model->wing(i)->extendBoundingBox(flo, fhi);

  Wallclock clk;
  clk.start();
  ovldisp.extendBox(flo, fhi);
  clk.stop();
  cout << "Bounding box computation: " << clk.elapsed() << endl;

  // tell QGLViewer about the scene dimensions
  vLo.setValue(flo[0], flo[1], flo[2]);
  vHi.setValue(fhi[0], fhi[1], fhi[2]);
  QGLViewer::setSceneBoundingBox(vLo, vHi);
  // QGLViewer::showEntireScene();
}

void RenderView::showOverlay(bool flag)
{
  if (flag != ovldisp.visible()) {
    ovldisp.visible( flag );
    updateGeometry();
  }
}

void RenderView::wireframeOverlay(bool flag)
{
  // OverlayGrid::drawPolygons( not flag );
  // ovldisp.clearDisplayList();
  ovldisp.drawPolygons( not flag );
  ovldisp.drawLines( flag );
  updateGeometry();
}

void RenderView::trafoOverlay()
{
  if (trafoDlg == 0) {
    trafoDlg = new TransformationDialog(this);
    connect(trafoDlg, SIGNAL(trafoChanged()), this, SLOT(updateGeometry()));
    connect(trafoDlg, SIGNAL(trafoChanged()), this, SLOT(updateProjector()));
  }

  trafoDlg->setTrafo( ovldisp.currentTrafo() );
  trafoDlg->show();
}

void RenderView::fitScreen()
{
  updateSceneDimensions();
  showEntireScene();
}

void RenderView::multiAxisControl(const SpaceMouseMotionData &mdata)
{
  const float tscale = 0.125f * QGLViewer::sceneRadius();
  const float rscale = 1e-1f;

  // quadratic sensitivities
  const float p2f = 4.0f;
  Vct6f dof;
  for (int k=0; k<6; ++k) {
    float v = mdata.axisSpeed(k);  // in [0,1], but usually < 0.5
    dof[k] = v + p2f*sq(v)*sign(v);
  }

  float dx = -tscale * dof[0];
  float dy = +tscale * dof[2];
  float dz = +tscale * dof[1];

  float rx = -rscale * dof[3];
  float ry = -rscale * dof[4];
  float rz =  rscale * dof[5];

  // extract screen coordinates first
  const Vec & screenUp = camera()->upVector();
  const Vec & screenRight = camera()->rightVector();
  const Vec & screenIn = camera()->viewDirection();

  Vct3f trn;
  for (int k=0; k<3; ++k)
    trn[k] = dx*screenRight[k] + dy*screenUp[k] + dz*screenIn[k];

  Quaternion qx( Vec(1.0,0.0,0.0), rx ); // pitch
  Quaternion qy( Vec(0.0,1.0,0.0), rz ); // yaw (!)
  Quaternion qz( Vec(0.0,0.0,1.0), ry ); // roll (!)

  Vec rap = camera()->revolveAroundPoint();
  camera()->frame()->rotateAroundPoint(qz*qy*qx, rap);
  camera()->frame()->translate( (float) trn[0],
      (float) trn[1],
      (float) trn[2] );
  repaint();
}

void RenderView::multiAxisButtonPressed(uint buttons)
{
  if (buttons & SpaceMouseInterface::LeftButton)
    fitScreen();
}

void RenderView::changeCamDirection(MvCamDirection cd)
{
  Vec dir, up;
  switch (cd) {
  case MvPosX:
    dir.setValue(1.0, 0.0, 0.0);
    up.setValue(0.0, 0.0, 1.0);
    break;
  case MvNegX:
    dir.setValue(-1.0, 0.0, 0.0);
    up.setValue(0.0, 0.0, 1.0);
    break;
  case MvPosY:
    dir.setValue(0.0, 1.0, 0.0);
    up.setValue(0.0, 0.0, 1.0);
    break;
  case MvNegY:
    dir.setValue(0.0, -1.0, 0.0);
    up.setValue(0.0, 0.0, 1.0);
    break;
  case MvPosZ:
    dir.setValue(0.0, 0.0, 1.0);
    up.setValue(1.0, 0.0, 0.0);
    break;
  case MvNegZ:
    dir.setValue(0.0, 0.0, -1.0);
    up.setValue(1.0, 0.0, 0.0);
    break;
  case MvTopLeftFwd:
    dir.setValue(1.0, 1.0, -1.0);
    up.setValue(0.0, 0.0, 1.0);
    break;
  default:
    return;
  }
  
  Camera *pc = QGLViewer::camera();
  pc->setViewDirection(dir);
  pc->setUpVector(up);
  pc->showEntireScene();
}

void RenderView::keyPressEvent(QKeyEvent *e)
{
  if ((e->key() == Qt::Key_X) and (e->modifiers() != Qt::ShiftModifier)) {
    changeCamDirection(MvPosX);
    updateGL();
  } else if ((e->key() == Qt::Key_X) and (e->modifiers() == Qt::ShiftModifier)) {
    changeCamDirection(MvNegX);
    updateGL();
  } else if ((e->key() == Qt::Key_Y) and (e->modifiers() != Qt::ShiftModifier)) {
    changeCamDirection(MvPosY);
    updateGL();
  } else if ((e->key() == Qt::Key_Y) and (e->modifiers() == Qt::ShiftModifier)) {
    changeCamDirection(MvNegY);
    updateGL();
  } else if ((e->key() == Qt::Key_Z) and (e->modifiers() != Qt::ShiftModifier)) {
    changeCamDirection(MvPosZ);
    updateGL();
  } else if ((e->key() == Qt::Key_Z) and (e->modifiers() == Qt::ShiftModifier)) {
    changeCamDirection(MvNegZ);
    updateGL();
  } else {
    QGLViewer::keyPressEvent(e);
  }
}

QString RenderView::helpString() const
{
  return shelp;
}

void RenderView::saveSnapshot()
{
  QGLViewer::saveSnapshot(false, false);
}

void RenderView::mouseReleaseEvent(QMouseEvent *e)
{
  if (e->button() == Qt::LeftButton) {
    bool found(false);
    Vec pos = QGLViewer::camera()->pointUnderPixel(e->pos(), found);
    if (found) {
      QString s("Position: ");
      s += QString::number(pos[0], 'f', 4) + " ";
      s += QString::number(pos[1], 'f', 4) + " ";
      s += QString::number(pos[2], 'f', 4);
      emit mousePosMsg(s);
    }
  }
  
  QGLViewer::mouseReleaseEvent(e);
}

