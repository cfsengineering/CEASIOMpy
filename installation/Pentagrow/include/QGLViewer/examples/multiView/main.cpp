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

#include "multiView.h"
#include <qapplication.h>
#include <qsplitter.h>

int main(int argc, char** argv)
{
  QApplication application(argc,argv);

  // Create Splitters
  QSplitter *hSplit  = new QSplitter(Qt::Vertical);
  QSplitter *vSplit1 = new QSplitter(hSplit);
  QSplitter *vSplit2 = new QSplitter(hSplit);

  // Create the scene
  Scene* s = new Scene();

  // Instantiate the viewers.
  Viewer side  (s,0,vSplit1);
  Viewer top   (s,1,vSplit1, &side);
  Viewer front (s,2,vSplit2, &side);
  Viewer persp (s,3,vSplit2, &side);

  
#if QT_VERSION < 0x040000
  application.setMainWidget(hSplit);
#else
  hSplit->setWindowTitle("multiView");
#endif

  // Set main QSplitter as the main widget.
  hSplit->show();

  return application.exec();
}
