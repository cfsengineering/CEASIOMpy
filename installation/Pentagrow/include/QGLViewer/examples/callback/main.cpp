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

#include "callback.h"
#include <QGLViewer/qglviewer.h>
#include <qapplication.h>
#include <qmessagebox.h>

using namespace std;

void help()
{
  QString text("<h2>C a l l b a c k</h2>");
  text += "This example is conceptually the same as simpleViewer.<br>";
  text += "The difference is that it uses the Qt signal/slot mechanism ";
  text += "instead of deriving the QGLViewer class. ";
  text += "The QGLViewer::drawNeeded() signal is connected to the Scene::draw() method. ";
  text += "The two classes are otherwise completely independant.";

  QMessageBox::information(NULL, "Callback exemple", text);
}

int main(int argc, char** argv)
{
  QApplication application(argc,argv);

  // Instantiate the viewer.
  QGLViewer viewer;

  // Restore the previous viewer state.
  viewer.restoreStateFromFile();

  // Create a scene, giving a pointer to the associated viewer.
  Scene s(&viewer);

#if QT_VERSION < 0x040000
  application.setMainWidget(&viewer);
#else
  viewer.setWindowTitle("callback");
#endif

  help();

  viewer.show();

  return application.exec();
}
