
/* ------------------------------------------------------------------------
 * project:    scope
 * file:       view.cpp
 * copyright:  (c) 2009 by <dlr@kth.se>
 * ------------------------------------------------------------------------
 * Interface to QGLViewer
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */

#include "glew.h"
#include "view.h"
#include "plotcontroller.h"
#include "meshplotter.h"
#include "spacenav/spacemouseinterface.h"
#include <genua/transformation.h>
#include <QMouseEvent>
#include <QSettings>
#include <QDebug>

#ifdef Q_OS_MACX
#include <OpenGL/OpenGL.h>
#endif

#include <iostream>

using namespace std;
using namespace qglviewer;

float ViewManager::s_animation_tscale = (1.0f / 2048.0f);

ViewManager::ViewManager(QWidget *parent)
  : QGLViewer(parent), plotControl(0),
    bPickElement(false), bPickNode(false), bGlInitialized(false)
{
  unity(viewTransform);

  QSettings settings;
  s_animation_tscale = settings.value("view-animation-tscale",
                                      s_animation_tscale).toFloat();
  bBlendedAA = settings.value("scope-enable-blendaa", (not ishidpi())).toBool();
  qDebug("Blending from settings: %d", bBlendedAA);

  bPickOnMouseRelease = true;

#if QT_VERSION >= QT_VERSION_CHECK(5,0,0)
  QGLViewer::camera()->devicePixelRatio( devicePixelRatio() );
#endif
}

ViewManager::~ViewManager()
{
  QSettings settings;
  settings.setValue("view-animation-tscale", s_animation_tscale);
}

bool ViewManager::ishidpi() const
{
#if QT_VERSION >= QT_VERSION_CHECK(5,0,0)
  return devicePixelRatio() > 1;
#else
  return false;
#endif
}

void ViewManager::assign(PlotController *plc)
{
  if (plc != plotControl) {
    plotControl = plc;

    if (plotControl != 0) {
      plotControl->autoUpdate(true);
      connect(plotControl, SIGNAL(needBoxUpdate()),
              this, SLOT(updateSceneDimensions()));
      connect(plotControl, SIGNAL(needRedraw()),
              this, SLOT(repaint()) );
    }
  }
}

bool ViewManager::pointUnderPixel(const QPoint & pscreen, Vct3f &pos) const
{
  QPoint pixel(pscreen);

  // FIXME: Logic error for hi-dpi displays

  //#if QT_VERSION >= QT_VERSION_CHECK(5,0,0)
  //  // account for screen point -> pixel conversion on Retina display
  //  pixel *= devicePixelRatio();
  //#endif

  bool found;
  qglviewer::Vec glpoint;
  glpoint = QGLViewer::camera()->pointUnderPixel(pixel, found);
  if (found) {
    for (int k=0; k<3; ++k)
      pos[k] = glpoint[k];
  }

  return found;
}

void ViewManager::clear()
{
  repaint();
}

void ViewManager::saveSnapshot()
{
  QGLViewer::saveSnapshot(false, false);
}

void ViewManager::updateDrawing()
{
  //  // recompute which elements to display
  //  plotter->updateIndices();

  //  // use deformed indices and recompute normals
  //  plotter->updateVertices();

  //  if (iPlotField == NotFound and colorSetting == FieldContourClr)
  //    colorSetting = SectionClr;

  //  switch (colorSetting) {
  //  case FieldContourClr:
  //    plotter->switchField(iPlotField, fBlueLimit, fRedLimit, eCondensationMode);
  //    break;
  //  case ElementQualityClr:
  //    plotter->colorFromQuality(fBlueLimit, fRedLimit);
  //    break;
  //  case BocoClr:
  //    plotter->bcColors();
  //    break;
  //  case SectionClr:
  //  default:
  //    plotter->secColors();
  //    break;
  //  }

  //  if (iSurfStrml != NotFound) {
  //    // plotter->surfStreamlines(iSurfStrml);
  //  } else if (iHedgehog != NotFound) {
  //    plotter->hedgehog(iHedgehog, needleScale);
  //  } else {
  //    plotter->clearStreamlines();
  //  }

  updateSceneDimensions();
}

void ViewManager::updateRepaint()
{
  updateDrawing();
  repaint();
}

void ViewManager::startAnimation()
{
  bAnimating = true;
  animtime.start();
  QGLViewer::setAnimationPeriod(0);
  QGLViewer::startAnimation();
  emit animationRunning(true);
}

void ViewManager::stopAnimation()
{
  bAnimating = false;
  QGLViewer::stopAnimation();
  // updateDrawing();
  emit animationRunning(false);
}

void ViewManager::animate()
{
  float rtime = animtime.elapsed() * s_animation_tscale;
  plotControl->animate( rtime );
}

void ViewManager::togglePerspective(bool flag)
{
  if (flag)
    QGLViewer::camera()->setType(Camera::PERSPECTIVE);
  else
    QGLViewer::camera()->setType(Camera::ORTHOGRAPHIC);
  repaint();
}

void ViewManager::changeCamDirection(MvCamDirection cd)
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

void ViewManager::multiAxisControl(const SpaceMouseMotionData &mdata)
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

void ViewManager::multiAxisButtonPressed(uint buttons)
{
  if (buttons & SpaceMouseInterface::LeftButton)
    showEntireScene();
}

void ViewManager::updateSceneDimensions()
{
  lobox =  1e12;
  hibox = -1e12;

  if (plotControl != 0)
    plotControl->plotter()->boundingBox(lobox.pointer(), hibox.pointer());

  cout << "BB low " << lobox << " high " << hibox << endl;

  // tell QGLViewer
  Vec vLo, vHi;
  vLo.setValue(lobox[0], lobox[1], lobox[2]);
  vHi.setValue(hibox[0], hibox[1], hibox[2]);
  QGLViewer::setSceneBoundingBox(vLo, vHi);

  for (int k=0; k<3; ++k)
    aidGrid[k].rescale(lobox, hibox);
}

void ViewManager::init()
{
  QGLWidget::makeCurrent();
  if (QGLContext::currentContext() == 0)
    return;

  // must initialize glew once we have a valid context
  GLenum err = glewInit();
  if (err != GLEW_OK) {
    cerr << "GLEW initialization failed." << glewGetErrorString(err) << endl;
    abort();
  }

#ifdef Q_OS_MACX
  CGLContextObj ctx = CGLGetCurrentContext();
  CGLError cgerr =  CGLEnable( ctx, kCGLCEMPEngine);
  if (cgerr != kCGLNoError )
    qDebug("Multithreaded rendering not available.");
  else
    qDebug("Multithreaded rendering enabled.");

  // because this make the 3D view unusable since glReadPixels blocks
  if ( strstr((const char *) glGetString(GL_VENDOR), "NVIDIA") )
    bPickOnMouseRelease = false;

  qDebug("Vendor: %s", (const char *) glGetString(GL_VENDOR));
#endif

  QGLViewer::camera()->setType(Camera::PERSPECTIVE);
  QGLViewer::setBackgroundColor(QColor(255, 255, 255));
  QGLViewer::setMouseBinding(Qt::LeftButton + Qt::SHIFT, RAP_FROM_PIXEL, true);

  if (bBlendedAA) {
    qDebug("Enabling blended antialiasing.");
    glEnable(GL_LINE_SMOOTH);
    glEnable(GL_POLYGON_SMOOTH);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST);
    glHint(GL_POLYGON_SMOOTH_HINT, GL_NICEST);
  } else {
    qDebug("Disabling blended antialiasing.");
    glDisable(GL_LINE_SMOOTH);
    glDisable(GL_POLYGON_SMOOTH);
  }

  bGlInitialized = true;
  emit viewerInitialized();
}

void ViewManager::draw()
{
  QGLWidget::makeCurrent();
  if (not bGlInitialized) {
    initializeGL();
    if (not bGlInitialized)
      return;
  }

  glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, 1);
  glEnable(GL_POLYGON_OFFSET_FILL);
  glPolygonOffset(1.0, 1.0);

  // apply transformation
  // glMatrixMode(GL_MODELVIEW);
  // glPushMatrix();
  // glMultMatrixf(viewTransform.pointer());

  // cout << "TFM:" << endl << viewTransform << endl;

  if (plotControl)
    plotControl->draw();

  // glPopMatrix();
}

void ViewManager::togglePickElement(bool flag)
{
  bPickElement = flag;
  if (flag) {
    if (plotControl) {
      MeshPlotterPtr mplot = plotControl->plotter();
      if (mplot)
        mplot->updateElementTree();
    }
    setCursor(QCursor(Qt::CrossCursor));
    bPickNode = false;
  } else {
    setCursor(QCursor(Qt::ArrowCursor));
  }
}

void ViewManager::togglePickNode(bool flag)
{
  bPickNode = flag;
  if (flag) {
    setCursor(QCursor(Qt::CrossCursor));
    bPickElement = false;
  } else {
    setCursor(QCursor(Qt::ArrowCursor));
  }
}

void ViewManager::enablePerspectiveProjection(bool flag)
{
  QSettings settings;
  settings.setValue("scope-perspective-projection", flag);
  if (flag) {
    camera()->setType( Camera::PERSPECTIVE );
  } else {
    camera()->setType( Camera::ORTHOGRAPHIC );
  }
  repaint();
}

void ViewManager::mouseReleaseEvent(QMouseEvent* e)
{
  if (bPickElement) {

    if (e->button() == Qt::LeftButton) {

      Vct3f p;
      bool found = pointUnderPixel(e->pos(), p);
      // qglviewer::Vec p = QGLViewer::camera()->pointUnderPixel(e->pos(), found);
      if (found and plotControl) {
        MeshPlotterPtr mplot = plotControl->plotter();
        if (not mplot)
          return;
        uint gix = mplot->nearestElement(p);
        if (gix != NotFound)
          emit elementPicked(gix);
      }
    }

  } else if (bPickNode) {

    if (e->button() == Qt::LeftButton) {

      Vct3f p;
      bool found = pointUnderPixel(e->pos(), p);
      // qglviewer::Vec p = QGLViewer::camera()->pointUnderPixel(e->pos(), found);
      if (found and plotControl) {
        MeshPlotterPtr mplot = plotControl->plotter();
        if (not mplot)
          return;
        uint nn = mplot->nearestNode( p );
        if (nn != NotFound)
          emit nodePicked(nn);
      }
    }

  } else if (bPickOnMouseRelease) {

    Vct3f p;
    bool found = pointUnderPixel(e->pos(), p);
    if (found) {
      MeshPlotterPtr mplot = plotControl->plotter();
      if (not mplot)
        return;
      uint nn = mplot->nearestNode( p );
      QString msg = tr("Position: %1, %2, %3 Node: %4")
          .arg(p[0]).arg(p[1]).arg(p[2]).arg(nn);
      MxMeshPtr pmx = plotControl->pmesh();
      uint cf = plotControl->contourField();
      if (cf != NotFound) {
        const MxMeshField & f(pmx->field(cf));
        if (f.nodal()) {
          QString fname = QString::fromStdString(f.name());
          if (f.ndimension() == 1) {
            float val;
            f.scalar(nn, val);
            msg += tr(", Field '%5': %6").arg(fname).arg(val);
          } else if (f.ndimension() == 3) {
            Vct3 val;
            f.value(nn, val);
            msg += tr(", Field '%5': (%6, %7, %8)")
                .arg(fname).arg(val[0]).arg(val[1]).arg(val[2]);
          }
        }
      }
      postStatusMessage(msg);
    }
  }

  // qDebug() << "Mouse release at: " << e->pos();
  if ((e->button() == Qt::LeftButton) and
      (e->modifiers() & Qt::ShiftModifier))
  {
    // qDebug() << "RAP: ";
    Camera *cam = QGLViewer::camera();
    if (cam)
      cam->setRevolveAroundPointFromPixel( e->pos() );
  }

  QGLViewer::mouseReleaseEvent(e);
}

void ViewManager::keyPressEvent(QKeyEvent *e)
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

