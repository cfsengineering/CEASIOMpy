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
#include "standardCamera.h"

#if QT_VERSION >= 0x040000
# include <QKeyEvent>
#endif

using namespace std;
using namespace qglviewer;

Viewer::Viewer(StandardCamera* nfc)
{
  // Change the camera.
  Camera* c = camera();
  setCamera(nfc);
  delete c;
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
  // Restore previous viewer state.
  if (!restoreStateFromFile())
  showEntireScene();

  setKeyDescription(Qt::Key_T, "Toggles camera type (perspective or orthographic)");
  setKeyDescription(Qt::Key_M, "Toggles camera mode (standard or QGLViewer)");

  setMouseBindingDescription(Qt::SHIFT + Qt::MidButton, "Change frustum size (for standard camera in orthographic mode)");

  // Display help window.
  help();
}

void Viewer::showMessage()
{
  QString std = ((StandardCamera*)camera())->isStandard()?"Standard camera":"QGLViewer camera";
  QString type = camera()->type() == Camera::PERSPECTIVE?"Perspective":"Orthographic";
  displayMessage(std + " - " + type);
  emit cameraChanged();
}

void Viewer::keyPressEvent(QKeyEvent *e)
{
  if (e->key() == Qt::Key_M) {
  // 'M' changes mode : standard or QGLViewer camera
    ((StandardCamera*)camera())->toggleMode();
    showMessage();
  } else
    if (e->key() == Qt::Key_T) {
    // 'T' changes the projection type : perspective or orthogonal
      if (camera()->type() == Camera::ORTHOGRAPHIC)
        camera()->setType(Camera::PERSPECTIVE);
      else
        camera()->setType(Camera::ORTHOGRAPHIC);
        showMessage();
      } else
        QGLViewer::keyPressEvent(e);
}

void Viewer::wheelEvent(QWheelEvent *e)
{
  if ((camera()->type() == Camera::ORTHOGRAPHIC) && (((StandardCamera*)camera())->isStandard()) &&
#if QT_VERSION >= 0x040000
    (e->modifiers() & Qt::ShiftModifier))
#else
    (e->state() & Qt::ShiftButton))
#endif
  {
    ((StandardCamera*)camera())->changeOrthoFrustumSize(e->delta());
    emit cameraChanged();
    updateGL();
  }
  else
    QGLViewer::wheelEvent(e);
}

QString Viewer::helpString() const
{
  QString text("<h2>S t a n d a r d C a m e r a</h2>");
  text += "An overloaded <code>Camera</code> class is used, that reproduces the 'standard' OpenGL settings.<br><br>";

  text += "With this camera, the near and (resp. far) plane distance is set to a very small (resp. very large) value. ";
  text += "With the orthographic camera type, the frustum dimensions are fixed. Use <code>Shift</code> and the mouse wheel to change them.<br><br>";

  text += "On the other hand, the QGLViewer camera fits the near and far distances to the scene radius. ";
  text += "Fine tuning is available using <code>zClippingCoefficient()</code> and <code>zNearCoefficient()</code>. ";
  text += "However, visual results do not seem to be impacted by this zBuffer fitted range.<br><br>";
  text += "The QGLViewer camera also adapts the orthographic frustum dimensions to the distance to the <code>revolveAroundPoint()</code> to mimic a perspective camera. ";
  text += "Since this behavior may not be needed, this example shows how to override it.<br><br>";

  text += "The second viewer displays the first one's camera to show its configuration.<br><br>";

  text += "Use <b>M</b> to switch between 'standard' and QGLViewer camera behavior.<br>";
  text += "Use <b>T</b> to switch between perspective and orthographic camera type.<br><br>";

  text += "Use <b>Shift+wheel</b> to change standard camera orthographic size.";

  return text;
}
