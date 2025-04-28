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
#include <qcolor.h>

class Viewer : public QGLViewer
{
protected :
  virtual void init();
  virtual void draw();
  virtual QString helpString() const;

private :
  void drawSaucer() const;

#if WIN32 && QT_VERSION < 0x030000
# define nbSaucers 10
#else
  static const int nbSaucers = 10;
#endif
  qglviewer::Frame saucerPos[nbSaucers];
  QColor saucerColor[nbSaucers];
};
