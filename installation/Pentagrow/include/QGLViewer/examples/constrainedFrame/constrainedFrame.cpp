/****************************************************************************

 Copyright (C) 2002-2008 Gilles Debunne. All rights reserved.

 This file is part of the QGLViewer library version 2.3.1.

 http://www.libqglviewer.com - contact@libqglviewer.com

 This file may be used under the terms of the GNU General Public License 
 versions 2.0 or 3.0 as published by the Free Software Foundation and
 appearing in the LICENSE file included in the packaging of this file.
 In addition, as a special exception, Gilles Debunne gives you certain 
 additional rights, described in the file GPL_EXCEPTION in this package.

 libQGLViewer uses dual licensing. Commercial/proprietary software must
 purchase a libQGLViewer Commercial License.

 This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
 WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.

*****************************************************************************/

#include "constrainedFrame.h"

#if QT_VERSION >= 0x040000
# include <QKeyEvent>
#endif

using namespace qglviewer;
using namespace std;

static AxisPlaneConstraint::Type nextTranslationConstraintType(const AxisPlaneConstraint::Type& type)
{
  switch (type)
    {
    case AxisPlaneConstraint::FREE  : return AxisPlaneConstraint::PLANE; break;
    case AxisPlaneConstraint::PLANE : return AxisPlaneConstraint::AXIS;  break;
    case AxisPlaneConstraint::AXIS  : return AxisPlaneConstraint::FORBIDDEN;  break;
    case AxisPlaneConstraint::FORBIDDEN : return AxisPlaneConstraint::FREE; break;
    default : return AxisPlaneConstraint::FREE;
    }
}

static AxisPlaneConstraint::Type nextRotationConstraintType(const AxisPlaneConstraint::Type& type)
{
  switch (type)
    {
    case AxisPlaneConstraint::FREE  : return AxisPlaneConstraint::AXIS; break;
    case AxisPlaneConstraint::AXIS  : return AxisPlaneConstraint::FORBIDDEN;  break;
    case AxisPlaneConstraint::PLANE :
    case AxisPlaneConstraint::FORBIDDEN : return AxisPlaneConstraint::FREE; break;
    default : return AxisPlaneConstraint::FREE;
    }
}

void Viewer::changeConstraint()
{
  unsigned short previous = activeConstraint;
  activeConstraint = (activeConstraint+1)%3;

  constraints[activeConstraint]->setTranslationConstraintType(constraints[previous]->translationConstraintType());
  constraints[activeConstraint]->setTranslationConstraintDirection(constraints[previous]->translationConstraintDirection());
  constraints[activeConstraint]->setRotationConstraintType(constraints[previous]->rotationConstraintType());
  constraints[activeConstraint]->setRotationConstraintDirection(constraints[previous]->rotationConstraintDirection());

  frame->setConstraint(constraints[activeConstraint]);
}

void Viewer::init()
{
  constraints[0] = new LocalConstraint();
  constraints[1] = new WorldConstraint();
  constraints[2] = new CameraConstraint(camera());

  transDir = 0; // X direction
  rotDir   = 0; // X direction
  activeConstraint = 0;

  frame = new ManipulatedFrame();
  setManipulatedFrame(frame);
  frame->setConstraint(constraints[activeConstraint]);

#if QT_VERSION < 0x040000
  // Preserve CAMERA bindings, see setHandlerKeyboardModifiers documentation.
  setHandlerKeyboardModifiers(QGLViewer::CAMERA, Qt::AltButton);
  // The frames can be move without any key pressed
  setHandlerKeyboardModifiers(QGLViewer::FRAME, Qt::NoButton);
  // The camera can always be moved with the Control key.
  setHandlerKeyboardModifiers(QGLViewer::CAMERA, Qt::ControlButton);

  setMouseBinding(Qt::ShiftButton | Qt::LeftButton,  QGLViewer::FRAME, QGLViewer::ROTATE,    false);
  setMouseBinding(Qt::ShiftButton | Qt::RightButton, QGLViewer::FRAME, QGLViewer::TRANSLATE, false);
  setMouseBinding(Qt::ShiftButton | Qt::MidButton,   QGLViewer::FRAME, QGLViewer::ZOOM,      false);
  setWheelBinding(Qt::ShiftButton,                   QGLViewer::FRAME, QGLViewer::ZOOM,      false);
#else
  setHandlerKeyboardModifiers(QGLViewer::CAMERA, Qt::AltModifier);
  setHandlerKeyboardModifiers(QGLViewer::FRAME, Qt::NoModifier);
  setHandlerKeyboardModifiers(QGLViewer::CAMERA, Qt::ControlModifier);

  setMouseBinding(Qt::ShiftModifier | Qt::LeftButton,  QGLViewer::FRAME, QGLViewer::ROTATE,    false);
  setMouseBinding(Qt::ShiftModifier | Qt::RightButton, QGLViewer::FRAME, QGLViewer::TRANSLATE, false);
  setMouseBinding(Qt::ShiftModifier | Qt::MidButton,   QGLViewer::FRAME, QGLViewer::ZOOM,      false);
  setWheelBinding(Qt::ShiftModifier,                   QGLViewer::FRAME, QGLViewer::ZOOM,      false);
#endif

  setAxisIsDrawn();

  setKeyDescription(Qt::Key_G, "Change translation constraint direction");
  setKeyDescription(Qt::Key_D, "Change rotation constraint direction");
  setKeyDescription(Qt::Key_Space, "Change constraint reference");
  setKeyDescription(Qt::Key_T, "Change translation constraint type");
  setKeyDescription(Qt::Key_R, "Change rotation constraint type");

  restoreStateFromFile();
  help();
}

void Viewer::draw()
{
  glMultMatrixd(frame->matrix());
  drawAxis(0.4f);
  const float scale = 0.3f;
  glScalef(scale, scale, scale);

  const float nbSteps = 200.0;
  glBegin(GL_QUAD_STRIP);
  for (float i=0; i<nbSteps; ++i)
    {
      float ratio = i/nbSteps;
      float angle = 21.0*ratio;
      float c = cos(angle);
      float s = sin(angle);
      float r1 = 1.0 - 0.8*ratio;
      float r2 = 0.8 - 0.8*ratio;
      float alt = ratio - 0.5;
      const float nor = .5;
      const float up = sqrt(1.0-nor*nor);
      glColor3f(1-ratio, 0.2f , ratio);
      glNormal3f(nor*c*scale, up*scale, nor*s*scale);
      glVertex3f(r1*c, alt, r1*s);
      glVertex3f(r2*c, alt+0.05, r2*s);
    }
  glEnd();

  displayText();
}

void Viewer::keyPressEvent(QKeyEvent *e)
{
  switch (e->key())
    {
    case Qt::Key_G : transDir = (transDir+1)%3; break;
    case Qt::Key_D : rotDir   = (rotDir+1)%3;   break;
    case Qt::Key_Space: changeConstraint();     break;
    case Qt::Key_T :
      constraints[activeConstraint]->setTranslationConstraintType(nextTranslationConstraintType(constraints[activeConstraint]->translationConstraintType()));
      break;
    case Qt::Key_R :
      constraints[activeConstraint]->setRotationConstraintType(nextRotationConstraintType(constraints[activeConstraint]->rotationConstraintType()));
      break;
    default:
      QGLViewer::keyPressEvent(e);
    }

  Vec dir(0.0,0.0,0.0);
  dir[transDir] = 1.0;
  constraints[activeConstraint]->setTranslationConstraintDirection(dir);

  dir = Vec(0.0,0.0,0.0);
  dir[rotDir] = 1.0;
  constraints[activeConstraint]->setRotationConstraintDirection(dir);

  updateGL();
}

void Viewer::displayType(const AxisPlaneConstraint::Type type, const int x, const int y, const char c)
{
  QString text;
  switch (type)
    {
    case AxisPlaneConstraint::FREE:  text = QString("FREE (%1)").arg(c);  break;
    case AxisPlaneConstraint::PLANE: text = QString("PLANE (%1)").arg(c); break;
    case AxisPlaneConstraint::AXIS:  text = QString("AXIS (%1)").arg(c); break;
    case AxisPlaneConstraint::FORBIDDEN: text = QString("FORBIDDEN (%1)").arg(c); break;
    }
  drawText(x, y, text);
}

void Viewer::displayDir(const unsigned short dir, const int x, const int y, const char c)
{
  QString text;
  switch (dir)
    {
    case 0: text = QString("X (%1)").arg(c); break;
    case 1: text = QString("Y (%1)").arg(c); break;
    case 2: text = QString("Z (%1)").arg(c); break;
    }
  drawText(x, y, text);
}

void Viewer::displayText()
{
  qglColor(foregroundColor());
  glDisable(GL_LIGHTING);
  drawText(10, height()-30, "TRANSLATION :");
  displayDir(transDir, 190, height()-30, 'G');
  displayType(constraints[activeConstraint]->translationConstraintType(), 10, height()-60, 'T');

  drawText(width()-220,height()-30, "ROTATION");
  displayDir(rotDir, width()-100, height()-30, 'D');
  displayType(constraints[activeConstraint]->rotationConstraintType(), width()-220, height()-60, 'R');

  switch (activeConstraint)
    {
    case 0 : drawText(20,20, "Constraint direction defined w/r to LOCAL (SPACE)"); break;
    case 1 : drawText(20,20, "Constraint direction defined w/r to WORLD (SPACE)"); break;
    case 2 : drawText(20,20, "Constraint direction defined w/r to CAMERA (SPACE)"); break;
    }
  glEnable(GL_LIGHTING);
}

QString Viewer::helpString() const
{
  QString text("<h2>C o n s t r a i n e d F r a m e</h2>");
  text += "A manipulated frame can be constrained in its displacement.<br><br>";
  text += "Try the different translation (press <b>G</b> and <b>T</b>) and rotation ";
  text += "(<b>D</b> and <b>R</b>) constraints while moving the frame with the mouse.<br><br>";
  text += "The constraints can be defined with respect to various coordinates";
  text += "systems : press <b>Space</b> to switch.<br><br>";
  text += "Press the <b>Control</b> key while moving the mouse to move the camera.<br>";
  text += "Press the <b>Shift</b> key to temporally disable the constraint.<br><br>";
  text += "You can easily define your own constraints to create a specific frame behavior.";
  return text;
}

