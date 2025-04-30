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

#include "screenCoordSystem.h"
#include <stdio.h>
#include <stdlib.h> // RAND_MAX

using namespace qglviewer;
using namespace std;

void Viewer::init()
{
  for (int i=0; i<nbSaucers; i++)
    {
      Vec pos;
      pos.x = rand() / static_cast<float>(RAND_MAX) - 0.5;
      pos.y = rand() / static_cast<float>(RAND_MAX) - 0.5;
      pos.z = rand() / static_cast<float>(RAND_MAX) - 0.5;

      Quaternion ori(Vec(static_cast<float>(rand()) / RAND_MAX,
			  static_cast<float>(rand()) / RAND_MAX,
			  static_cast<float>(rand()) / RAND_MAX),
		      rand() / static_cast<float>(RAND_MAX) * M_PI);

      saucerPos[i].setPosition(pos);
      saucerPos[i].setOrientation(ori);

      saucerColor[i].setRgb(int(255.0 * rand() / static_cast<float>(RAND_MAX)),
			    int(255.0 * rand() / static_cast<float>(RAND_MAX)),
			    int(255.0 * rand() / static_cast<float>(RAND_MAX)));
    }

  restoreStateFromFile();
  help();
}

QString Viewer::helpString() const
{
  QString text("<h2>S c r e e n C o o r d S y s t e m</h2>");
  text += "This example illustrates the <i>startScreenCoordinatesSystem()</i> function ";
  text += "which enables a GL drawing directly into the screen coordinate system.<br><br>";
  text += "The arrows are drawned using this method. The screen projection coordinates ";
  text += "of the objects is determined using <code>camera()->projectedCoordinatesOf()</code>, ";
  text += "thus <i>attaching</i> the 2D arrows to 3D objects.";
  return text;
}

void Viewer::drawSaucer() const
{
  static GLUquadric* quadric = gluNewQuadric();

  glTranslatef(0.0, 0.0, -0.014f);
  gluCylinder(quadric, 0.015, 0.03, 0.004, 32, 1);
  glTranslatef(0.0, 0.0, 0.004f);
  gluCylinder(quadric, 0.03, 0.04, 0.01, 32, 1);
  glTranslatef(0.0, 0.0, 0.01f);
  gluCylinder(quadric, 0.05, 0.03, 0.02, 32, 1);
  glTranslatef(0.0, 0.0, 0.02f);
  gluCylinder(quadric, 0.03, 0.0, 0.003, 32, 1);
  glTranslatef(0.0, 0.0, -0.02f);
}

void Viewer::draw()
{
  static Vec proj[nbSaucers];

  int i;
  // Draw 3D flying saucers
  for (i=0; i<nbSaucers; i++)
    {
      glPushMatrix();
      glMultMatrixd(saucerPos[i].matrix());
      qglColor(saucerColor[i]);
      drawSaucer();
      glPopMatrix();
    }

  // Draw the arrows
  qglColor(foregroundColor());
  startScreenCoordinatesSystem();
  for (i=0; i<nbSaucers; i++)
    {
      glBegin(GL_POLYGON);
      proj[i] = camera()->projectedCoordinatesOf(saucerPos[i].position());
      // The small z offset makes the arrow slightly above the saucer, so that it is always visible
      glVertex3fv(proj[i] + Vec(-55, 0, -0.001f));
      glVertex3fv(proj[i] + Vec(-17,-5, -0.001f));
      glVertex3fv(proj[i] + Vec( -5, 0, -0.001f));
      glVertex3fv(proj[i] + Vec(-17, 5, -0.001f));
      glEnd();
    }
  stopScreenCoordinatesSystem();

  // Draw text id
  glDisable(GL_LIGHTING);
  for (i=0; i<nbSaucers; i++)
    drawText(int(proj[i].x)-60, int(proj[i].y)+4, QString::number(i));
  glEnable(GL_LIGHTING);
}


