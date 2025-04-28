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

#ifndef MOVE_H
#define MOVE_H

#include <qpoint.h>
#include <iostream>

class Board;

class Move
{  
public:
  Move() {};
  Move(const QPoint& s, const QPoint& e);
  Move(const Board* const b, int s, int e);
  Move(const QString text);

  bool isValid(const Board* const b) const;  
  bool isClose() const;

  int numberOfNewPieces(const Board& b) const;

  friend std::ostream& operator<<(std::ostream& out, const Move& m);

  const QPoint& start() const { return start_; }
  const QPoint& end() const { return end_; }

private:
  QPoint start_, end_;
};

#endif // MOVE_H
