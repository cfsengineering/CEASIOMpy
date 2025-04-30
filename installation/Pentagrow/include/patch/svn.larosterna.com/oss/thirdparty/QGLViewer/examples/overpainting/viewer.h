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

class QPaintEvent;
class QPainter;

class Viewer : public QGLViewer
{
public :
  Viewer(QWidget* parent = 0);

protected :
  virtual void draw();
  virtual void init();
  void drawOverpaint(QPainter *painter);

  virtual void paintGL() { update(); };
  virtual void paintEvent(QPaintEvent *event);
  // Could be overloaded to defer final initializations
  //virtual void showEvent(QShowEvent *event);

  virtual QString helpString() const;
};
