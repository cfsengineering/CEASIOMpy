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

#include "fastDraw.h"

using namespace std;
using namespace qglviewer;

void Viewer::init()
{
  // Increase the material shininess, so that the difference between
  // the two versions of the spiral is more visible.
  glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 50.0);
  GLfloat specular_color[4] = { 0.8f, 0.8f, 0.8f, 1.0 };
  glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,  specular_color);

  restoreStateFromFile();
  help();
}

static void drawSpiral(bool simplified = false)
{
  int nbSteps = 600;
  int nbSub = 50;
  if (simplified)
    {
      nbSteps = 60;
      nbSub = 2;
    }

  for (float n=0; n<nbSub; ++n)
    {
      glBegin(GL_QUAD_STRIP);
      for (float i=0.0; i<nbSteps; ++i)
	{
	  float ratio = i/nbSteps;
	  float angle = 21.0*ratio;
	  float radius = 1.0 - 0.5*ratio;

	  Vec center(radius*cos(angle), ratio-0.5, radius*sin(angle));

	  for (unsigned short j=0; j<2; ++j)
	    {
	      float delta = 3.0*(n+j)/nbSub;
	      Vec shift(cos(angle)*cos(delta), sin(delta), sin(angle)*cos(delta));

	      glColor3f(1-ratio, (n+j)/nbSub , ratio);
	      glNormal3fv(shift);
	      glVertex3fv(center+0.2f*shift);
	    }
	}
      glEnd();
    }
}

void Viewer::draw()
{
  drawSpiral();
}

void Viewer::fastDraw()
{
  drawSpiral(true);
}

QString Viewer::helpString() const
{
  QString text("<h2>F a s t D r a w</h2>");
  text += "The <code>fastDraw()</code> function is called instead of <code>draw()</code> when the camera ";
  text += "is manipulated. Providing such a simplified version of <code>draw()</code> allows for interactive ";
  text += "frame rates when the camera is moved, even for very complex scenes.";
  return text;
}
