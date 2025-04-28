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

#include "keyboardAndMouse.h"
#if QT_VERSION < 0x040000
# include <qpopupmenu.h>
#else
# include <QMenu>
# include <QKeyEvent>
# include <QMouseEvent>
#endif
#include <qcursor.h>
#include <qmap.h>
#include <math.h>

using namespace std;

// Draws a spiral
void Viewer::draw()
{
  const float nbSteps = 80.0;

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
      glColor3f(fabs(c), 0.2f, fabs(s));
      glNormal3f(nor*c, up, nor*s);
      glVertex3f(r1*c, alt, r1*s);
      glVertex3f(r2*c, alt+0.05, r2*s);
    }
  glEnd();
}

void Viewer::init()
{
  // Restore previous viewer state.
  restoreStateFromFile();


  /////////////////////////////////////////////////////
  //       Keyboard shortcut customization           //
  //      Changes standard action key bindings       //
  /////////////////////////////////////////////////////

  // Define 'Control+Q' as the new exit shortcut (default was 'Escape')
  setShortcut(EXIT_VIEWER, Qt::CTRL+Qt::Key_Q);

  // Set 'Control+F' as the FPS toggle state key.
  setShortcut(DISPLAY_FPS, Qt::CTRL+Qt::Key_F);

  // Disable draw grid toggle shortcut (default was 'G')
  setShortcut(DRAW_GRID, 0);


  // Add custom key description (see keyPressEvent).
  setKeyDescription(Qt::Key_W, "Toggles wire frame display");
  setKeyDescription(Qt::Key_F, "Toggles flat shading display");


  /////////////////////////////////////////////////////
  //         Mouse bindings customization            //
  //     Changes standard action mouse bindings      //
  /////////////////////////////////////////////////////

  // Left and right buttons together make a camera zoom : emulates a mouse third button if needed.
  setMouseBinding(Qt::LeftButton | Qt::RightButton, CAMERA, ZOOM);

  // Disable previous TRANSLATE mouse binding (and remove it from help mouse tab).
  setMouseBinding(Qt::RightButton, NO_CLICK_ACTION);

#if QT_VERSION < 0x040000
  // Alt+left button translates the camera (since right button will popup a menu).
  setMouseBinding(Qt::AltButton | Qt::LeftButton, CAMERA, TRANSLATE);
  // Define Control+Shift+Right button as selection shortcut
  setMouseBinding(Qt::ControlButton | Qt::ShiftButton | Qt::RightButton, SELECT);
  // Alt + mouse wheel MOVE_FORWARD the camera.
  setWheelBinding(Qt::AltButton, CAMERA, MOVE_FORWARD);
#else
  setMouseBinding(Qt::ControlModifier | Qt::ShiftModifier | Qt::RightButton, SELECT);
  setWheelBinding(Qt::AltModifier, CAMERA, MOVE_FORWARD);
  setMouseBinding(Qt::AltModifier | Qt::LeftButton, CAMERA, TRANSLATE);
#endif

  // Add custom mouse bindings description (see mousePressEvent())
  setMouseBindingDescription(Qt::RightButton, "Opens a camera path context menu");

  // Display the help window. The help window tabs are automatically updated when you define new
  // standard key or mouse bindings (as is done above). Custom bindings descriptions are added using
  // setKeyDescription() and setMouseBindingDescription().
  help();
}


///////////////////////////////////////////////
//      Define new key bindings : F & W      //
///////////////////////////////////////////////

void Viewer::keyPressEvent(QKeyEvent *e)
{
  // Get event modifiers key
#if QT_VERSION < 0x040000
  // Bug in Qt : use 0x0f00 instead of Qt::KeyButtonMask with Qt versions < 3.1
  const Qt::ButtonState modifiers = (Qt::ButtonState)(e->state() & Qt::KeyButtonMask);
#else
  const Qt::KeyboardModifiers modifiers = e->modifiers();
#endif

  // A simple switch on e->key() is not sufficient if we want to take state key into account.
  // With a switch, it would have been impossible to separate 'F' from 'CTRL+F'.
  // That's why we use imbricated if...else and a "handled" boolean.
  bool handled = false;
  if ((e->key()==Qt::Key_W) && (modifiers==Qt::NoButton))
    {
      wireframe_ = !wireframe_;
      if (wireframe_)
	glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
      else
	glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
      handled = true;
      updateGL();
    }
  else
    if ((e->key()==Qt::Key_F) && (modifiers==Qt::NoButton))
      {
	flatShading_ = !flatShading_;
	if (flatShading_)
	  glShadeModel(GL_FLAT);
	else
	  glShadeModel(GL_SMOOTH);
	handled = true;
	updateGL();
      }
  // ... and so on with other else/if blocks.

  if (!handled)
    QGLViewer::keyPressEvent(e);
}


///////////////////////////////////////////////////////////
//             Define new mouse bindings                 //
//   A camera viewpoint menu binded on right button      //
///////////////////////////////////////////////////////////

void Viewer::mousePressEvent(QMouseEvent* e)
{
#if QT_VERSION < 0x040000
  if ((e->button() == Qt::RightButton) && (e->state() == Qt::NoButton))
#else
  if ((e->button() == Qt::RightButton) && (e->modifiers() == Qt::NoButton))
#endif
    {
#if QT_VERSION < 0x040000
      QPopupMenu menu( this );
      menu.insertItem("Camera positions");
      menu.insertSeparator();
      QMap<int, int> menuMap;
#else
      QMenu menu( this );
      menu.addAction("Camera positions");
      menu.addSeparator();
      QMap<QAction*, int> menuMap;
#endif

      bool atLeastOne = false;
      // We only test the 20 first indexes. This is a limitation.
      for (unsigned short i=0; i<20; ++i)
	if (camera()->keyFrameInterpolator(i))
	  {
	    atLeastOne = true;
	    QString text;
	    if (camera()->keyFrameInterpolator(i)->numberOfKeyFrames() == 1)
	      text = "Position "+QString::number(i);
	    else
	      text = "Path "+QString::number(i);

#if QT_VERSION < 0x040000
	    menuMap[menu.insertItem(text)] = i;
#else
	    menuMap[menu.addAction(text)] = i;
#endif
	  }

      if (!atLeastOne)
	{
#if QT_VERSION < 0x040000
	  menu.insertItem("No position defined");
	  menu.insertItem("Use to Alt+Fx to define one");
#else
	  menu.addAction("No position defined");
	  menu.addAction("Use to Alt+Fx to define one");
#endif
	}

#if QT_VERSION < 0x040000
      menu.setMouseTracking(true);
      int select = menu.exec(e->globalPos());

      if (atLeastOne && select != -1)
	camera()->playPath(menuMap[select]);
#else
      QAction* action = menu.exec(e->globalPos());

      if (atLeastOne && action)
	camera()->playPath(menuMap[action]);
#endif
    }
  else
    QGLViewer::mousePressEvent(e);
}

QString Viewer::helpString() const
{
  QString text("<h2>K e y b o a r d A n d M o u s e</h2>");
  text += "This example illustrates the mouse and key bindings customization.<br><br>";
  text += "Use <code>setShortcut()</code> to change standard action key bindings (display of axis, grid or fps, exit shortcut...).<br><br>";
  text += "Use <code>setMouseBinding()</code> and <code>setWheelBinding()</code> to change standard action mouse bindings ";
  text += "(camera rotation, translation, object selection...).<br><br>";
  text += "If you want to define <b>new</b> key or mouse actions, overload <code>keyPressEvent()</code> and/or ";
  text += "<code>mouse(Press|Move|Release)Event()</code> to define and bind your own new actions. ";
  text += "Use <code>setKeyDescription()</code> and <code>setMouseBindingDescription()</code> to add a description of your bindings in the help window.<br><br>";
  text += "In this example, we defined the <b>F</b> and <b>W</b> keys and the right mouse button opens a popup menu. ";
  text += "See the keyboard and mouse tabs in this help window for the complete bindings description.<br><br>";
  text += "By the way, exit shortcut has been binded to <b>Ctrl+Q</b>.";
  return text;
}

