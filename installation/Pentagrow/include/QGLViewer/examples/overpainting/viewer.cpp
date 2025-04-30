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

#include "viewer.h"

#include <QPainter>

using namespace std;

#ifndef GL_MULTISAMPLE
#define GL_MULTISAMPLE  0x809D
#endif

Viewer::Viewer(QWidget* parent)
: QGLViewer(QGLFormat(QGL::SampleBuffers), parent) {
  setAttribute(Qt::WA_NoSystemBackground);
}

void Viewer::drawOverpaint(QPainter *painter) {
	painter->save();
    painter->translate(width()/2, height()/2);
	QRadialGradient radialGrad(QPointF(-40, -40), 100);
	radialGrad.setColorAt(0, QColor(255, 255, 255, 100));
	radialGrad.setColorAt(1, QColor(200, 200, 0, 100)); 
    painter->setBrush(QBrush(radialGrad));
	painter->drawRoundRect(-100, -100, 200, 200);
    painter->restore();
}

// Draws a spiral
void Viewer::draw()
{
  const float nbSteps = 200.0;

  glBegin(GL_QUAD_STRIP);
  for (int i=0; i<nbSteps; ++i)
    {
      const float ratio = i/nbSteps;
      const float angle = 21.0*ratio;
      const float c = cos(angle);
      const float s = sin(angle);
      const float r1 = 1.0 - 0.8f*ratio;
      const float r2 = 0.8f - 0.8f*ratio;
      const float alt = ratio - 0.5f;
      const float nor = 0.5f;
      const float up = sqrt(1.0-nor*nor);
      glColor3f(1.0-ratio, 0.2f , ratio);
      glNormal3f(nor*c, up, nor*s);
      glVertex3f(r1*c, alt, r1*s);
      glVertex3f(r2*c, alt+0.05f, r2*s);
    }
  glEnd();
}

void Viewer::init()
{
  restoreStateFromFile();
  help();
}

void Viewer::paintEvent(QPaintEvent *event)
{
	Q_UNUSED(event)
    QPainter painter;
    painter.begin(this);
    painter.setRenderHint(QPainter::Antialiasing);

	// Save current OpenGL state
    glPushAttrib(GL_ALL_ATTRIB_BITS);
    glMatrixMode(GL_PROJECTION);
    glPushMatrix();
    glMatrixMode(GL_MODELVIEW);
    glPushMatrix();

	// Reset OpenGL parameters
    glShadeModel(GL_SMOOTH);
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_CULL_FACE);
    glEnable(GL_LIGHTING);
    glEnable(GL_LIGHT0);
    glEnable(GL_MULTISAMPLE);
    static GLfloat lightPosition[4] = { 1.0, 5.0, 5.0, 1.0 };
    glLightfv(GL_LIGHT0, GL_POSITION, lightPosition);
    qglClearColor(backgroundColor());
	
	// Classical 3D drawing, usually performed by paintGL().
	preDraw();
	draw();
    postDraw();

	// Restore OpenGL state
    glMatrixMode(GL_MODELVIEW);
    glPopMatrix();
    glMatrixMode(GL_PROJECTION);
    glPopMatrix();
    glPopAttrib();

    drawOverpaint(&painter);

    painter.end();
}

QString Viewer::helpString() const
{
  QString text("<h2>O v e r p a i n t</h2>");
  text += ".";
  return text;
}
