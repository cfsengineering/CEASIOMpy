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

#include "QGLViewer/qglviewer.h"
#include "object.h"

#if QT_VERSION < 0x040000
# include "qptrvector.h"
#endif

class Viewer : public QGLViewer
{
public:
  Viewer();

protected :
  virtual void draw();
  virtual void init();
  virtual QString helpString() const;

  // Selection functions
  virtual void drawWithNames();
  virtual void endSelection(const QPoint&);

  // Mouse events functions
  virtual void mousePressEvent(QMouseEvent *e);
  virtual void mouseMoveEvent(QMouseEvent *e);
  virtual void mouseReleaseEvent(QMouseEvent *e);

private :
  void startManipulation();
  void drawSelectionRectangle() const;
  void addIdToSelection(int id);
  void removeIdFromSelection(int id);

  // Current rectangular selection
  QRect rectangle_;

  // Different selection modes
  enum SelectionMode { NONE, ADD, REMOVE };
  SelectionMode selectionMode_;

#if QT_VERSION < 0x040000
  // Objects of the scene
  QPtrVector<Object> objects_;
  // ids of the selected objects
  QValueList<int> selection_;
#else
  QList<Object*> objects_;
  QList<int> selection_;
#endif

};
