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

#ifndef BOARD_H
#define BOARD_H

#include "move.h"
#include "case.h"
#include "undo.h"

#include <qstring.h>
#include <qsize.h>
#if QT_VERSION < 0x040000
# include <qvaluevector.h>
#else
# include <qvector.h>
#endif

class Board
{
  friend class Move;
  
public:
  Board() : board_(NULL) {};

  void draw() const;
  void drawSelectedPiece(int piece) const;
  void drawPossibleDestinations(int piece, bool select=false) const;
  void drawSelectablePieces() const;

  // Used for animation
  //void doNotDrawPiece(const QPoint& p) { board_[p.x()][p.y()] = Board::EMPTY; };
  //void doDrawPiece(const QPoint& p) { board_[p.x()][p.y()] = blackColor(blackPlays_); };
  //void drawFlippingPieces(const QPoint& p, bool flip) const;
  
  void play(const Move& m);

  QSize size() const { return QSize(sizeX_, sizeY_); };
  
  QString statusMessage() const;

  bool canBeSelected(const QPoint& p) const;
  bool canBeSelected(int i) const { return canBeSelected(pointFromInt(i)); }

  bool isValid(const QPoint& p) const;
  
  bool gameIsOver() const;
  bool blackPlays() const { return blackPlays_; };
  int nbMovesLeft() const { return nbMovesLeft_; };

  bool undo();
  bool redo();

  Case& caseAt(const QPoint p) const { return board_[p.x()][p.y()]; };

  QString stateString() const;
  void initFromStateString(const QString& s);

  Move randomMove(bool black) const;

  // Input-Output
  friend std::ostream& operator<<(std::ostream& out, const Board& p);
  friend std::istream& operator>>(std::istream& in, Board& b);

private:  
  void resize(int sizeX, int sizeY);
  bool pieceCanMove(const QPoint& p) const;

  int intFromPoint(const QPoint& p) const { return p.x()*sizeY_ + p.y(); };
  QPoint pointFromInt(int i) const { return QPoint(i/sizeY_, i%sizeY_); };
  
  int sizeX_, sizeY_;
  int nbMovesLeft_;
  Case** board_;
  bool blackPlays_;
  Undo undo_;
};

#endif // BOARD_H
