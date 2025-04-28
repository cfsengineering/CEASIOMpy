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

#include "move.h"
#include "board.h"
#include "qstringlist.h"
#include "qregexp.h"

#include "QGLViewer/keyFrameInterpolator.h"
using namespace qglviewer;

Move::Move(const QPoint& s, const QPoint& e)
  : start_(s), end_(e)
{}

Move::Move(const Board* const b, int s, int e)
{
  start_ = b->pointFromInt(s);
  end_   = b->pointFromInt(e);
}

Move::Move(const QString text)
{
#if QT_VERSION < 0x040000
  QStringList list = QStringList::split(QRegExp("\\D"), text);
#else
  QStringList list = text.split(QRegExp("\\D"), QString::SkipEmptyParts);
#endif

  start_ = QPoint(list[0].toInt(), list[1].toInt());
  end_ = QPoint(list[2].toInt(), list[3].toInt());
}

bool Move::isValid(const Board* const b) const
{
  return (b->isValid(start()) &&
	  b->isValid(end()) &&
	  abs(start().x()-end().x()) <= 2 &&
	  abs(start().y()-end().y()) <= 2 &&
	  start() != end() &&
	  b->stateOf(start())==Board::blueColor(b->bluePlays()) &&
	  b->stateOf(end())==Board::EMPTY);
}

bool Move::isClose() const
{
  QPoint delta = start() - end();
  return (abs(delta.x()) < 2) && (abs(delta.y())<2);
}

int Move::numberOfNewPieces(const Board& b) const
{
  int res = 0;

  for (int i=-1; i<=1; ++i)
    for (int j=-1; j<=1; ++j)
      {
	const QPoint p(end().x()+i, end().y()+j);
	if (b.isValid(p) && b.stateOf(p) == Board::blueColor(!b.bluePlays()))
	  res++;
      }

  if (isClose())
    res++;

  return res;
}

std::ostream& operator<<(std::ostream& out, const Move& m)
{
  out << "(" << m.start().x() << "," << m.start().y() << ") -> (" << m.end().x() << ","<< m.end().y() << ")" << std::endl;
  return out;
}

