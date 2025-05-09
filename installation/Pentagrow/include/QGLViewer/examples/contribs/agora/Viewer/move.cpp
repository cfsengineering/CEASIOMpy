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

Move::Move(const QPoint& s, const QPoint& e, bool under)
: start_(s), end_(e), under_(under)
{}

Move::Move(const Board* const b, int s, int e, bool under)
{
  start_ = b->pointFromInt(s);
  end_   = b->pointFromInt(e);
  under_ = under;
}

Move::Move(const QString text)
{
#if QT_VERSION < 0x040000
  QStringList list = QStringList::split(QRegExp("\\D+"), text);
#else
  QStringList list = text.split(QRegExp("\\D+"), QString::SkipEmptyParts);
#endif

  start_ = QPoint(list[0].toInt(), list[1].toInt());
  end_ = QPoint(list[2].toInt(), list[3].toInt());

  under_ = text.contains('<');
}

bool Move::isValid(const Board* const b) const
{
  if (b->isValid(start()) &&
	  b->isValid(end()) &&
	  abs(start().x()-end().x()) <= 1 &&
	  abs(start().y()-end().y()) <= 1 &&
	  start() != end() &&
	  b->caseAt(start()).nbTop() > 0 &&
	  b->caseAt(start()).topIsBlack() == b->blackPlays())
	  if (goesUnder())
		  return ((b->caseAt(start()).topAltitude() <= b->caseAt(end()).topAltitude()) && 
				  (b->caseAt(end()).nbTop() > 0) &&
				  (b->caseAt(end()).topIsBlack() != b->blackPlays()));
	  else
		  return ((b->caseAt(end()).nbTop() == 0) || 
		          ((b->caseAt(start()).topAltitude() >= b->caseAt(end()).topAltitude()) && (b->caseAt(end()).topIsBlack() != b->blackPlays())));
	return false;
}

void Move::updateBoard(const Board* b) const
{
	// No tests here, assume move is valid
    b->caseAt(start()).removePiece();
    b->caseAt(end()).addPiece(goesUnder(), b->blackPlays());
}

std::ostream& operator<<(std::ostream& out, const Move& m)
{
  out << "((" << m.start().x() << "," << m.start().y() << ")" << (m.goesUnder()?"<":">") << "(" << m.end().x() << ","<< m.end().y() << "))" << std::endl;
  return out;
}

