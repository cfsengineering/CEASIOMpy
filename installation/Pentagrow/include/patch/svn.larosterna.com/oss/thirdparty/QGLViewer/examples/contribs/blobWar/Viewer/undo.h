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

#ifndef UNDO_H
#define UNDO_H

// To get QT_VERSION
#include "qglobal.h"
#include <iostream>

#if QT_VERSION < 0x040000
# include <qvaluevector.h>
#else
# include <qstringlist.h> 
#endif

class Undo
{
public:
  Undo() { clear(); }

  void clear();
  void addState(const QString& s);
  
  QString undoState();
  QString redoState();

  bool isEmpty() const { return state_.isEmpty(); };

  int nbMoves() const { return index_; };
  
  friend std::ostream& operator<<(std::ostream& out, const Undo& u);
  friend std::istream& operator>>(std::istream& in, Undo& u);

private:
#if QT_VERSION < 0x040000
  QValueVector<QString> state_;
#else
  QStringList state_;
#endif
  int index_, maxIndex_;
};

#endif // UNDO_H
