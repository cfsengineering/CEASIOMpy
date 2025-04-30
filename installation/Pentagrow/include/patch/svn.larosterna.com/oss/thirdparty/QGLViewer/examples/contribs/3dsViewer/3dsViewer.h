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

#include <QGLViewer/qglviewer.h>

#include <lib3ds/file.h>
#include <lib3ds/node.h>

class Viewer : public QGLViewer
{
public :
  Viewer() : file(NULL), current_frame(0.0), camera_name(NULL) {};

protected :
  virtual void draw();
  virtual void animate();
  virtual void init();
  virtual void keyPressEvent(QKeyEvent *e);
  virtual QString helpString() const;

  void renderNode(Lib3dsNode *node);
  void loadFile();
  void initScene();

private :
  Lib3dsFile *file;
  float current_frame;
  char* camera_name;
};
