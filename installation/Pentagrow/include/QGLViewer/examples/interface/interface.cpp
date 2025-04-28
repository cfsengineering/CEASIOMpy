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

#include "interface.h"
#include <math.h>

// Constructor must call the base class constructor.
#if QT_VERSION < 0x040000
Viewer::Viewer(QWidget *parent, const char *name)
  : QGLViewer(parent, name)
#else
Viewer::Viewer(QWidget *parent)
    : QGLViewer(parent)
#endif
{
  restoreStateFromFile();
  help();
}

void Viewer::draw()
{
  // Draws a spiral
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
      glColor3f(1.0-ratio, 0.2f , ratio);
      glNormal3f(nor*c, up, nor*s);
      glVertex3f(r1*c, alt, r1*s);
      glVertex3f(r2*c, alt+0.05, r2*s);
    }
  glEnd();
}

QString Viewer::helpString() const
{
  QString text("<h2>I n t e r f a c e</h2>");
  text += "A GUI can be added to a QGLViewer widget using Qt's <i>Designer</i>. Signals and slots ";
  text += "can then be connected to and from the viewer.<br><br>";
  text += "You can install the QGLViewer designer plugin to make the QGLViewer appear as a ";
  text += "standard Qt widget in the Designer's widget tabs. See installation pages for details.<br><br>";
  text += "An other option (with Qt version 2 or 3) is to add a <i>Custom Widget</i> in Designer. ";
  text += "All the available QGLViewer's signals and slots are listed in a <code>qglviewer.cw</code> ";
  text += "(custom widget) file, located in the QGLViewer <code>include</code> directory.";
  return text;
}
