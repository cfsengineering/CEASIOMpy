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

#include "frustumCulling.h"
#include "cullingCamera.h"
#include "box.h"

using namespace qglviewer;

void Viewer::draw()
{
  Box::Root->drawIfAllChildrenAreVisible(cullingCamera);

  if (cullingCamera == camera())
    // Main viewer computes its plane equation
    cullingCamera->computeFrustumPlanesEquations();
  else
    {
      // Observer viewer draws cullingCamera
      glLineWidth(4.0);
      glColor4f(1.0, 1.0, 1.0, 0.5);
      cullingCamera->draw();
    }
}

void Viewer::init()
{
  // Restore previous viewer state.
  restoreStateFromFile();

  if (cullingCamera != camera())
    {
      // Observer viewer configuration
      glEnable(GL_BLEND);
      glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
      help();
    }
  
  glDisable(GL_LIGHTING);
}

QString Viewer::helpString() const
{
  QString text("<h2>F r u s t u m C u l l i n g</h2>");

  text += "A hierarchical octree structure is clipped against the camera's frustum clipping planes, obtained ";
  text += "using <code>getFrustumPlanesCoefficients</code>. A second viewer uses <code>drawCamera()</code> to ";
  text += "display an external view of the first viewer's camera.<br><br>";

  text += "This frustum culling implementation is quite naive. Many optimisation techniques are available in ";
  text += "the litterature.";

  return text;
}
