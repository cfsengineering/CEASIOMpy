
/* ------------------------------------------------------------------------
 * project:    ftkview
 * file:       trimeshview.cpp
 * begin:      Dec 2008
 * copyright:  (c) 2008 by <dlr@kth.se>
 * ------------------------------------------------------------------------
 * OpenGL viewer for steady 3D plots and animations
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */

#include <string>

#include <QMouseEvent>
#include <QDebug>
#include <surf/tetmesh.h>
#include "meshdrawoptions.h"
#include "spacenav/spacemouseinterface.h"

#include "glew.h"
#include "trimeshview.h"

using namespace std;
using namespace qglviewer;

// ----------------- TriangleGroup -----------------------------------------

int TriangleGroup::hue = 117;

uint TriangleGroup::assign(const TriMesh *m)
{
  idx.clear();
  msh = m;
  if (not msh)
    return 0;
  
  tag = -1;
  
  // generate a color
  nextColor(rgba);

  const int nf = msh->nfaces();
  idx.resize(nf);
  for (int i=0; i<nf; ++i)
    idx[i] = i; 
  
  return idx.size();
}

uint TriangleGroup::extract(const TriMesh *m, int t)
{
  idx.clear();
  msh = m;
  if (not msh)
    return 0;

  // generate a color
  nextColor(rgba);
  
  // extract triangles
  tag = t;
  uint count(0);
  const int nf = msh->nfaces();
  for (int i=0; i<nf; ++i) {
    const TriFace & f( msh->face(i) );
    if (f.tag() == tag) {
      idx.push_back(i);
      ++count;
    }
  }
  return count;
}

void TriangleGroup::nextColor(double col[]) const
{
  // generate a color
  const int sat = 140;
  const int val = 170;
  QColor::fromHsv(hue, sat, val).getRgbF(&col[0], &col[1], &col[2]);
  col[3] = 1.0;
  hue = (hue + 53) % 360;
}

void TriangleGroup::glDraw() const
{
  if (not msh)
    return;
  
  const int nf = idx.size();
  if (nf == 0)
    return;
  
  const PointList<3> & vtx( msh->vertices() );
  const PointList<3> & nrm( msh->normals() );

  glBegin(GL_TRIANGLES);
  glColor4dv(rgba);
  for (int i=0; i<nf; ++i) {
    const TriFace & f( msh->face(idx[i]) );
    const uint *t = f.vertices();
    glNormal3dv(nrm[t[0]].pointer());
    glVertex3dv(vtx[t[0]].pointer());
    glNormal3dv(nrm[t[1]].pointer());
    glVertex3dv(vtx[t[1]].pointer());
    glNormal3dv(nrm[t[2]].pointer());
    glVertex3dv(vtx[t[2]].pointer());
  }
  glEnd();
}

// ----------------- TriMeshView -------------------------------------------

TriMeshView::TriMeshView(QGLContext *ctx, QWidget *parent)
  : QGLViewer(parent), msh(0), pvm(0), bGlInitialized(false)
{
  vLo.setValue(-1.0f, -1.0f, -1.0f);
  vHi.setValue(1.0f, 1.0f, 1.0f);

  // default: draw elements and edges, but no normals
  bDrawEdges = true;
  bDrawPolygons = true;
  bDrawNormals = false;
  bDrawCut = true;

  // default colors
  // cPolygons = Qt::gray;
  cPolygons = QColor::fromRgb(170, 170, 255);
  cEdges = Qt::black;
  cNormals = Qt::darkMagenta;
  cTets = Qt::lightGray;

  // default is perspective projection
  projection = Camera::PERSPECTIVE;
  
  // no display list defined yet
  iDisplayList = NotFound;
  
  // default is xz-plane through origin
  pcut = Plane( vct(0,1,0), 0 );
}

TriMeshView::~TriMeshView()
{
  if (iDisplayList != NotFound) {
    QGLWidget::makeCurrent();
    glDeleteLists(iDisplayList, 1);
  }
}

void TriMeshView::saveSnapshot()
{
  QGLViewer::saveSnapshot(false, false);
}

void TriMeshView::buildDisplayList()
{
  if (not bGlInitialized) {
    if (QGLContext::currentContext())
      initializeGL();
    if (not bGlInitialized)
      return;
  }

  QGLWidget::makeCurrent();
  
  if (iDisplayList != NotFound)
      glDeleteLists(iDisplayList, 1);
  iDisplayList = glGenLists(1);
  glNewList(iDisplayList, GL_COMPILE);
  
  if (msh != 0) {
    if (bDrawPolygons) {
      glEnable(GL_POLYGON_OFFSET_FILL);
      glPolygonOffset(1.0, 1.0);
      drawElements();
      if (bDrawCut) {
        QGLWidget::qglColor(cTets);
        drawTets();
      }
    }
    if (bDrawEdges) {
      QGLWidget::qglColor(cEdges);
      drawEdges();
    }
    if (bDrawNormals) {
      QGLWidget::qglColor(cNormals);
      drawNormals();
    }
  }
  
  glEndList();
}

void TriMeshView::init()
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

  glEnable(GL_DEPTH_TEST);
  glEnable(GL_LINE_SMOOTH);
  glEnable(GL_BLEND);
  glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
  glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
  glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

  bGlInitialized = true;
  emit viewerInitialized();
}

void TriMeshView::clear()
{
  msh = 0;
  pvm = 0;
  mcut.clear();
  buildDisplayList();
  repaint();
}

void TriMeshView::display(const TriMesh *pm)
{
  // new surface mesh means volume mesh does not match any longer
  mcut.clear();
  pvm = 0;
  
  // set surface mesh
  msh = pm;
  if (not msh)
    return;

  // update search tree
  btree = BSearchTree( msh->vertices() );

  Indices tall;
  msh->allTags(tall);
  
  // extract mesh components
  const int nmc = tall.size();
  tgroup.resize(nmc);
  for (int j=0; j<nmc; ++j) 
    tgroup[j].extract(msh, tall[j]);

  // compute average edge length
  lnrm = 0.0;
  const int ne = msh->nedges();
  for (int i=0; i<ne; ++i)
    lnrm += msh->edge(i).length();
  lnrm /= ne;
  
  buildDisplayList();
  updateSceneDimensions();
  QGLViewer::showEntireScene();
}

void TriMeshView::displayCut(const TetMesh *tvm)
{
  display(msh);
  pvm = tvm;
  updateMeshCut();
}

void TriMeshView::updateMeshCut()
{
  bool firstcut = (mcut.nfaces() == 0);
  if (pvm != 0) {
    mcut.clear();
    pvm->cutElements(pcut, mcut);
    mcut.fixate(true);
  } 
  buildDisplayList();
  updateSceneDimensions();
  if (firstcut)
    QGLViewer::showEntireScene();
  repaint();
}

void TriMeshView::fitScreen()
{
  updateSceneDimensions();
  showEntireScene();
}

void TriMeshView::updateSceneDimensions()
{
  if (not msh)
    return;
  
  // find a tight bounding box
  Real flo[3], fhi[3];
  flo[0] = flo[1] = flo[2] = 1e18;
  fhi[0] = fhi[1] = fhi[2] = -1e18;

  const int nv = msh->nvertices();
  for (int i=0; i<nv; ++i) {
    const Vct3 & p( msh->vertex(i) );
    for (int k=0; k<3; ++k) {
      flo[k] = min(flo[k], p[k]);
      fhi[k] = max(fhi[k], p[k]);
    }
  }
  
  const int n = mcut.nvertices();
  for (int i=0; i<n; ++i) {
    const Vct3 & p( mcut.vertex(i) );
    for (int k=0; k<3; ++k) {
      flo[k] = min(flo[k], p[k]);
      fhi[k] = max(fhi[k], p[k]);
    }
  }
  
  // tell QGLTriMeshView about the scene dimensions
  vLo.setValue(flo[0], flo[1], flo[2]);
  vHi.setValue(fhi[0], fhi[1], fhi[2]);
  QGLViewer::setSceneBoundingBox(vLo, vHi);
  // QGLViewer::showEntireScene();
}

void TriMeshView::draw()
{
  if (not bGlInitialized) {
    if (QGLContext::currentContext())
      initializeGL();
    if (not bGlInitialized)
      return;
  }

  QGLWidget::makeCurrent();
  glCallList(iDisplayList);
}

void TriMeshView::drawElements()
{
  const int ng = tgroup.size();
  for (int i=0; i<ng; ++i)
    tgroup[i].glDraw();
}

void TriMeshView::drawTets()
{
  const int nf(mcut.nfaces());
  const PointList<3> & vtx( mcut.vertices() );
  
  Vct3 fn;
  glBegin(GL_TRIANGLES);
  for (int i=0; i<nf; ++i) {
    const TriFace & f( mcut.face(i) );
    const uint *t = f.vertices();
    fn = f.normal().normalized();
    glNormal3dv(fn.pointer());
    glVertex3dv(vtx[t[0]].pointer());
    glVertex3dv(vtx[t[1]].pointer());
    glVertex3dv(vtx[t[2]].pointer());
  }
  glEnd();
}

void TriMeshView::drawEdges()
{
  if (not msh)
    return;
  
  {
    const int ne = msh->nedges();
    const PointList<3> & vtx( msh->vertices() );
    glBegin(GL_LINES);
    for (int i=0; i<ne; ++i) {
      const TriEdge & e( msh->edge(i) );
      glVertex3dv( vtx[e.source()].pointer() );
      glVertex3dv( vtx[e.target()].pointer() );
    }
    glEnd();
  }
  
  if (bDrawCut) {
    const int ne = mcut.nedges();
    const PointList<3> & vtx( mcut.vertices() );
    glBegin(GL_LINES);
    for (int i=0; i<ne; ++i) {
      const TriEdge & e( mcut.edge(i) );
      glVertex3dv( vtx[e.source()].pointer() );
      glVertex3dv( vtx[e.target()].pointer() );
    }
    glEnd();
  }
}

void TriMeshView::drawNormals()
{
  if (not msh)
    return;
  
  const int nv = msh->nvertices();
  const PointList<3> & vtx( msh->vertices() );
  const PointList<3> & nrm( msh->normals() );
  
  Vct3 pt;
  glBegin(GL_LINES);
  for (int i=0; i<nv; ++i) {
    pt = vtx[i] + lnrm*nrm[i];
    glVertex3dv( vtx[i].pointer() );
    glVertex3dv( pt.pointer() );
  }
  glEnd();  
}

uint TriMeshView::nodeUnderPixel(const QPoint & spt, bool & found) const
{
  Vec glpoint;
  glpoint = QGLViewer::camera()->pointUnderPixel(spt, found);
  if (not found)
    return 0;
  else {
    Vct3 pt;
    pt[0] = static_cast<double>(glpoint[0]);
    pt[1] = static_cast<double>(glpoint[1]);
    pt[2] = static_cast<double>(glpoint[2]);
    return btree.nearest(pt);
  }
}

void TriMeshView::mouseReleaseEvent(QMouseEvent* e)
{
  if (e->button() == Qt::LeftButton and msh != 0) {
    bool hit(false);
    uint jnode = nodeUnderPixel(e->pos(), hit);
    QString msg;
    if (hit) {
      const Vct3 & xyz( msh->vertex(jnode) );
      msg.sprintf("Node %d at x = %.3f y = %.3f z = %.3f",
                  jnode, xyz[0], xyz[1], xyz[2]);
    } else {
      msg = tr("No vertex found at this position.");
    }
    emit postStatusMessage(msg);
  }
  
  // call default mouse binding
  QGLViewer::mouseReleaseEvent(e);
}

void TriMeshView::dlgDrawOptions()
{
  MeshDrawOptions *dlg = new MeshDrawOptions(this);
  dlg->execute();
}

bool TriMeshView::orthoCamera() const
{
  return (projection == Camera::ORTHOGRAPHIC);
}

void TriMeshView::toggleOrthoCamera(bool flag)
{
  if (flag) 
    projection = Camera::ORTHOGRAPHIC;
  else 
    projection = Camera::PERSPECTIVE;
  
  QGLViewer::camera()->setType(projection);
  draw();
}

void TriMeshView::multiAxisControl(const SpaceMouseMotionData &mdata)
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

void TriMeshView::multiAxisButtonPressed(uint buttons)
{
  if (buttons & SpaceMouseInterface::LeftButton)
    fitScreen();
}

void TriMeshView::changeCamDirection(MvCamDirection cd)
{
  Vec dir, up;
  switch (cd) {
    case TriMeshView::MvPosX:
      dir.setValue(1.0, 0.0, 0.0);
      up.setValue(0.0, 0.0, 1.0);
      break;
    case TriMeshView::MvNegX:
      dir.setValue(-1.0, 0.0, 0.0);
      up.setValue(0.0, 0.0, 1.0);
      break;
    case TriMeshView::MvPosY:
      dir.setValue(0.0, 1.0, 0.0);
      up.setValue(0.0, 0.0, 1.0);
      break;
    case TriMeshView::MvNegY:
      dir.setValue(0.0, -1.0, 0.0);
      up.setValue(0.0, 0.0, 1.0);
      break;
    case TriMeshView::MvPosZ:
      dir.setValue(0.0, 0.0, 1.0);
      up.setValue(1.0, 0.0, 0.0);
      break;
    case TriMeshView::MvNegZ:
      dir.setValue(0.0, 0.0, -1.0);
      up.setValue(1.0, 0.0, 0.0);
      break;
    case TriMeshView::MvTopLeftFwd:
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

void TriMeshView::keyPressEvent(QKeyEvent *e)
{
  if ((e->key() == Qt::Key_X) and (e->modifiers() != Qt::ShiftModifier)) {
    changeCamDirection(TriMeshView::MvPosX);
    updateGL();
  } else if ((e->key() == Qt::Key_X) and (e->modifiers() == Qt::ShiftModifier)) {
    changeCamDirection(TriMeshView::MvNegX);
    updateGL();
  } else if ((e->key() == Qt::Key_Y) and (e->modifiers() != Qt::ShiftModifier)) {
    changeCamDirection(TriMeshView::MvPosY);
    updateGL();
  } else if ((e->key() == Qt::Key_Y) and (e->modifiers() == Qt::ShiftModifier)) {
    changeCamDirection(TriMeshView::MvNegY);
    updateGL();
  } else if ((e->key() == Qt::Key_Z) and (e->modifiers() != Qt::ShiftModifier)) {
    changeCamDirection(TriMeshView::MvPosZ);
    updateGL();
  } else if ((e->key() == Qt::Key_Z) and (e->modifiers() == Qt::ShiftModifier)) {
    changeCamDirection(TriMeshView::MvNegZ);
    updateGL();
  } else {
    QGLViewer::keyPressEvent(e);
  }
}






