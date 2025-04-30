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

#include "luxo.h"
#include <math.h>

using namespace qglviewer;
using namespace std;

//////////////////////////////////  V i e w e r  ////////////////////////////////////////

QString Viewer::helpString() const
{
  QString text("<h2>L u x o  �</h2>");
  text += "This example illustrates several functionnalities of QGLViewer, ";
  text += "showing how easy it is to create a moderately complex application.<br><br>";
  text += "The famous luxo lamp (�Pixar) can interactively be manipulated ";
  text += "with the mouse. <b>Shift</b> left click on an a part of the lamp to select it, ";
  text += "and then move it with the mouse. Press the <b>Control</b> key or select the background ";
  text += "to move the camera instead.<br><br>";
  text += "A simpler object selection example is given in the <i>select</i> example. ";
  text += "A simpler frame displacement example is available in <i>manipulatedFrame</i> and ";
  text += "a simpler constrained frame example is illustrated in <i>constrainedFrame</i>. ";
  text += "See <i>multiSelect</i> for a multi-object selection example.<br><br>";
  text += "Feel free to use this code as the starting point of a multiple frame manipulation application.";
  return text;
}

void Viewer::initSpotLight()
{
  glMatrixMode(GL_MODELVIEW);
  glEnable(GL_LIGHT1);
  glLoadIdentity();

  // Light default parameters
  GLfloat spot_dir[3]       = {0.0, 0.0, 1.0};
  GLfloat light_ambient[4]  = {0.5, 0.5, 0.5, 1.0};
  GLfloat light_specular[4] = {1.0, 1.0, 1.0, 1.0};
  GLfloat light_diffuse[4]  = {3.0, 3.0, 1.0, 1.0};

  glLightfv(GL_LIGHT1, GL_SPOT_DIRECTION, spot_dir);
  glLightf( GL_LIGHT1, GL_SPOT_EXPONENT,  3.0);
  glLightf( GL_LIGHT1, GL_SPOT_CUTOFF,    50.0);
  glLightf( GL_LIGHT1, GL_CONSTANT_ATTENUATION, 0.5);
  glLightf( GL_LIGHT1, GL_LINEAR_ATTENUATION, 1.0);
  glLightf( GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 1.5);
  glLightfv(GL_LIGHT1, GL_AMBIENT,  light_ambient);
  glLightfv(GL_LIGHT1, GL_SPECULAR, light_specular);
  glLightfv(GL_LIGHT1, GL_DIFFUSE,  light_diffuse);
}

void Viewer::init()
{
  restoreStateFromFile();

  // Make camera the default manipulated frame.
  setManipulatedFrame( camera()->frame() );

#if QT_VERSION < 0x040000
  // Preserve CAMERA bindings, see setHandlerKeyboardModifiers documentation.
  setHandlerKeyboardModifiers(QGLViewer::CAMERA, Qt::AltButton);
  // The frames can be move without any key pressed
  setHandlerKeyboardModifiers(QGLViewer::FRAME, Qt::NoButton);
  // The camera can always be moved with the Control key.
  setHandlerKeyboardModifiers(QGLViewer::CAMERA, Qt::ControlButton);
#else
  setHandlerKeyboardModifiers(QGLViewer::CAMERA, Qt::AltModifier);
  setHandlerKeyboardModifiers(QGLViewer::FRAME, Qt::NoModifier);
  setHandlerKeyboardModifiers(QGLViewer::CAMERA, Qt::ControlModifier);
#endif

  initSpotLight();

  help();
}

void Viewer::draw()
{
  luxo.draw();

  // Draw the ground
  glColor3f(0.4f, 0.4f, 0.4f);
  const float nbPatches = 100;
  glNormal3f(0.0,0.0,1.0);
  for (int j=0; j<nbPatches; ++j)
    {
      glBegin(GL_QUAD_STRIP);
      for (int i=0; i<=nbPatches; ++i)
	{
	  glVertex2f((2*i/nbPatches-1.0), (2*j/nbPatches-1.0));
	  glVertex2f((2*i/nbPatches-1.0), (2*(j+1)/nbPatches-1.0));
	}
      glEnd();
    }
}

void Viewer::drawWithNames()
{
  // Render scene with objects ids
  luxo.draw(true);
}

void Viewer::postSelection(const QPoint&)
{
  if (selectedName() == -1)
    {
      // Camera will be the default frame is no object is selected.
      setManipulatedFrame( camera()->frame() );
      luxo.setSelectedFrameNumber(4); // dummy value meaning camera
    }
  else
    {
      setManipulatedFrame(luxo.frame(selectedName()));
      luxo.setSelectedFrameNumber(selectedName());
    }
}

//////////////////////////////////  L u x o ////////////////////////////////////////

Luxo::Luxo()
{
  for (unsigned short i=0; i<4; ++i)
    {
      frame_[i] = new ManipulatedFrame();

      // Creates a hierarchy of frames.
      if (i>0)
	frame(i)->setReferenceFrame(frame(i-1));
    }

  // Initialize frames
  frame(1)->setTranslation(Vec(0.0, 0.0, 0.08f)); // Base height
  frame(2)->setTranslation(Vec(0.0, 0.0, 0.5f));  // Arm length
  frame(3)->setTranslation(Vec(0.0, 0.0, 0.5f));  // Arm length

  frame(1)->setRotation(Quaternion(Vec(1.0,0.0,0.0), 0.6));
  frame(2)->setRotation(Quaternion(Vec(1.0,0.0,0.0), -2.0));
  frame(3)->setRotation(Quaternion(Vec(1.0,-0.3f,0.0), -1.7));

  // Set frame constraints
  WorldConstraint* baseConstraint = new WorldConstraint();
  baseConstraint->setTranslationConstraint(AxisPlaneConstraint::PLANE, Vec(0.0,0.0,1.0));
  baseConstraint->setRotationConstraint(AxisPlaneConstraint::AXIS, Vec(0.0,0.0,1.0));
  frame(0)->setConstraint(baseConstraint);

  LocalConstraint* XAxis = new LocalConstraint();
  XAxis->setTranslationConstraint(AxisPlaneConstraint::FORBIDDEN,  Vec(0.0,0.0,0.0));
  XAxis->setRotationConstraint   (AxisPlaneConstraint::AXIS, Vec(1.0,0.0,0.0));
  frame(1)->setConstraint(XAxis);
  frame(2)->setConstraint(XAxis);

  LocalConstraint* headConstraint = new LocalConstraint();
  headConstraint->setTranslationConstraint(AxisPlaneConstraint::FORBIDDEN, Vec(0.0,0.0,0.0));
  frame(3)->setConstraint(headConstraint);

  // Means camera is selected.
  selected = 4;
}

void Luxo::draw(bool names)
{
  // Luxo's local frame
  glPushMatrix();
  glMultMatrixd(frame(0)->matrix());

  if (names) glPushName(0);
  setColor(0);
  drawBase();
  if (names) glPopName();

  if (names) glPushName(1);
  glMultMatrixd(frame(1)->matrix());
  setColor(1);
  drawCylinder();
  drawArm();
  if (names) glPopName();

  if (names) glPushName(2);
  glMultMatrixd(frame(2)->matrix());
  setColor(2);
  drawCylinder();
  drawArm();
  if (names) glPopName();

  if (names) glPushName(3);
  glMultMatrixd(frame(3)->matrix());
  setColor(3);
  drawHead();
  if (names) glPopName();

  // Add light
  const GLfloat pos[4] = {0.0, 0.0, 0.0, 1.0};
  glLightfv(GL_LIGHT1, GL_POSITION, pos);
  const GLfloat spot_dir[3]  = {0.0, 0.0, 1.0};
  glLightfv(GL_LIGHT1, GL_SPOT_DIRECTION, spot_dir);
  glPopMatrix();
}

void Luxo::drawBase()
{
  drawCone(0.0, 0.03f, 0.15f, 0.15f, 30);
  drawCone(0.03f, 0.05f, 0.15f, 0.13f, 30);
  drawCone(0.05f, 0.07f, 0.13f, 0.01f, 30);
  drawCone(0.07f, 0.09f, 0.01f, 0.01f, 10);
}

void Luxo::drawArm()
{
  glTranslatef(0.02f, 0.0, 0.0);
  drawCone(0.0, 0.5f, 0.01f, 0.01f, 10);
  glTranslatef(-0.04f, 0.0, 0.0);
  drawCone(0.0, 0.5f, 0.01f, 0.01f, 10);
  glTranslatef(0.02f, 0.0, 0.0);
}

void Luxo::drawHead()
{
  drawCone(-0.02f, 0.06f, 0.04f, 0.04f, 30);
  drawCone(0.06f, 0.15f, 0.04f, 0.17f, 30);
  drawCone(0.15f, 0.17f, 0.17f, 0.17f, 30);
}

void Luxo::drawCylinder()
{
  glPushMatrix();
  glRotatef(90, 0.0, 1.0, 0.0);
  drawCone(-0.05f, 0.05f, 0.02f, 0.02f, 20);
  glPopMatrix();
}

void Luxo::setColor(unsigned short nb)
{
  if (nb == selected)
    glColor3f(0.9f, 0.9f, 0.0);
  else
    glColor3f(0.9f, 0.9f, 0.9f);
}

// Draws a truncated cone aligned with the Z axis.
void Luxo::drawCone(float zMin, float zMax, float r1, float r2, int nbSub)
{
  static GLUquadric* quadric = gluNewQuadric();

  glTranslatef(0.0, 0.0, zMin);
  gluCylinder(quadric, r1, r2, zMax-zMin, nbSub, 1);
  glTranslatef(0.0, 0.0, -zMin);
}

