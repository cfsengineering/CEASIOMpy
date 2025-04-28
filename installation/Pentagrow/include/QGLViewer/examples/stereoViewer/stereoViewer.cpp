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

#include "stereoViewer.h"
#include <qapplication.h>
#include <math.h>

using namespace std;

void Viewer::init()
{
  restoreStateFromFile();

  // Activate the stereo display. Press 'S' to toggle.
  setStereoDisplay(true);

  help();
}

QString Viewer::helpString() const
{
  QString text("<h2>S t e r e o V i e w e r</h2>");
  text += "You can display in stereo with no change to your application, provided that your hardware supports stereo display.<br><br>";
  
  text += "If you get a <b>Stereo not supported on this display</b> error message, check that ";
  text += "your machine supports stereo (search for quad-buffer in <i>glxinfo</i> and find stereo glasses !).<br><br>";
  
  text += "You can then toggle the stereo display by pressing <b>S</b> in any application.";
  return text;
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
      const float nor = 0.5;
      const float up = sqrt(1.0-nor*nor);
      glColor3f(1.0-ratio, 0.2f , ratio);
      glNormal3f(nor*c, up, nor*s);
      glVertex3f(r1*c, alt, r1*s);
      glVertex3f(r2*c, alt+0.05f, r2*s);
    }
  glEnd();

  return;
}
