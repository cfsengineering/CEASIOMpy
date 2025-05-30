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

#ifndef BLOBWAR_VIEWER_H
#define BLOBWAR_VIEWER_H

#include "QGLViewer/qglviewer.h"
#include "move.h"
#include "computerPlayer.h"

class Board;
class QTimer;

class BlobWarViewer : public QGLViewer
{
  Q_OBJECT

public:
#if QT_VERSION < 0x040000
  BlobWarViewer(QWidget* parent=NULL, const char* name=0);
#else
  BlobWarViewer(QWidget* parent=NULL);
#endif
  
public slots:
  // F i l e   m e n u
  void load();
  void save();
  void saveAs();

  // G a m e   m e n u
  void newGame();
  void undo();
  void redo();
  void finalizeUndoRedo();
  void bluePlayerIsHuman(bool on);
  void redPlayerIsHuman(bool on);
  void configureBluePlayer();
  void configureRedPlayer();
  
  // D i s p l a y   m e n u
  void toggleAnimation(bool on) { animatePlays_ = on; }
  void toggleDisplayPossibleMoves(bool on) { displayPossibleMoves_ = on; updateGL(); }

  // H e l p   m e n u
  void displayRules();
  void about();

protected :
  virtual void draw();
  virtual void mouseDoubleClickEvent(QMouseEvent *) {};
  virtual void keyPressEvent(QKeyEvent *) {};
  virtual void drawWithNames();
  virtual void postSelection(const QPoint& point);
  virtual void init();
  
  void play(const Move& m);

private slots:
  void simplePlay();
  void flipColor();
  void playComputerMove(QString move, int duration);
  void playNextMove();

private :
  // I n i t i a l i z a t i o n
  void fitCameraToBoard();
  void initViewer();

  // G a m e   p l a y
  void selectBoardFileName();
  
  // C o m p u t e r   p l a y e r s
  void configurePlayer(bool blue);
  void setPlayerIsHuman(bool on, bool blue);

  // G a m e   a n i m a t i o n
  void animatePlay();

  // G a m e   v a r i a b l e s
  Board* board_;
  ComputerPlayer computerPlayer_[2];
  QString boardFileName_;
  int selectedPiece_;

  // D i s p l a y   F l a g s
  bool displayPossibleMoves_;
  bool animatePlays_;    

  // A n i m a t i o n
  qglviewer::KeyFrameInterpolator* kfi_;
  Move currentMove_;
  int animationStep_;
  QTimer* undoTimer_;
};

#endif // BLOBWAR_VIEWER_H
