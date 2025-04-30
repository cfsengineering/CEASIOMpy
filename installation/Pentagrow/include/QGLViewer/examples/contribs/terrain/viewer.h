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

// TP OpenGL: Joerg Liebelt, Serigne Sow
#ifndef __SIMPLEVIEW_H__
#define __SIMPLEVIEW_H__

#include <QGLViewer/qglviewer.h>

class Viewer : public QGLViewer
{
private:
  bool drawMesh;

protected :
  virtual void draw();
  virtual void init();
  virtual void animate();		//pour l'eau
  virtual QString helpString() const;

  bool CheckExtension(const QString& szExtensionName );	//CODE EXTERNE

public:
  bool DrawInit( void );
  bool DrawShutdown( void );
  void keyPressEvent(QKeyEvent *e);
};


#endif

