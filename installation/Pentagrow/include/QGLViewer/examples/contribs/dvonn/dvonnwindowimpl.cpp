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

#include "dvonnwindowimpl.h"
#include "dvonnviewer.h"
#include <qmessagebox.h>
#include <qfile.h>
#include <qfileinfo.h>
#include <qfiledialog.h>
#include <qaction.h>
#include <qtextbrowser.h>
#include <qapplication.h>
#include <qdir.h>
#include <qlabel.h>
#include <qstatusbar.h>
#include <qtimer.h>

using namespace std;
using namespace dvonn;

//************************************************************
// Implementation of DvonnWindowImpl
//************************************************************
DvonnWindowImpl::DvonnWindowImpl(dvonn::Game* g)
  : DvonnWindow(), game_(g)
{
  dvonnViewer->setGame(g);

  connect(dvonnViewer,SIGNAL(requested(dvonn::Game::Placement)),
	  this,SLOT(play(dvonn::Game::Placement)));
  connect(dvonnViewer,SIGNAL(requested(dvonn::Game::Move)),
	  this,SLOT(play(dvonn::Game::Move)));

  gameRandomlyFinishAction->setEnabled(game_->phase() != MovePhase);
  gameRandomlyMoveStackAction->setEnabled(false);

  rulesBrowser_ = new QTextBrowser(NULL);
#if QT_VERSION < 0x040000
  rulesBrowser_->mimeSourceFactory()->setFilePath(QStringList()<<qApp->applicationDirPath()<<QDir(qApp->applicationDirPath()).filePath("rules/"));
  rulesBrowser_->setSource("rules/rules.html");
#else
  rulesBrowser_->setSearchPaths(QStringList()<<qApp->applicationDirPath()<<QDir(qApp->applicationDirPath()).filePath("rules/"));
  rulesBrowser_->setSource(QUrl("rules/rules.html"));
#endif
  rulesBrowser_->resize(600,600);

  gameUndoAction->setEnabled(false);
  gameRedoAction->setEnabled(false);

  // Populate the status bar (it is a shame we cannot do it in designer)
  currentPlayerLB_ = new QLabel(labelFor(game_->theOnePlaying()),
				statusBar());
  statusBar()->addWidget(currentPlayerLB_);
  currentPhaseLB_ = new QLabel(labelFor(game_->phase()),
			       statusBar());
  statusBar()->addWidget(currentPhaseLB_);
  currentPhaseLB_->setFrameShape(QLabel::NoFrame);
  currentPhaseLB_->setFrameShadow(QLabel::Plain);
  currentPhaseLB_->setSizePolicy(QSizePolicy::Preferred,
				 QSizePolicy::MinimumExpanding);

  startAnimScoreTimer_ = new QTimer(this);
  connect(startAnimScoreTimer_,SIGNAL(timeout()),
	  this,SLOT(animateScore()));
}
QString
DvonnWindowImpl::labelFor(Player p)
{
  switch (p)
  {
  case WhitePlayer: return tr("Whites");
  case BlackPlayer: return tr("Blacks");
  }
  return "";
}
QString
DvonnWindowImpl::labelFor(Phase p)
{
  switch (p)
  {
  case RedPlacementPhase:   return tr("Place red chip");
  case PiecePlacementPhase: return tr("Place your chip");
  case MovePhase:           return tr("Move a free stack you control");
  case GameOverPhase:
    {
      QString score = QString("W %1 to B %2")
	.arg(game_->score(WhitePlayer))
	.arg(game_->score(BlackPlayer));
      return "Game is over "+score;
    }
  }
  return "";
}
void
DvonnWindowImpl::help()
{
  rulesBrowser_->reload();
  rulesBrowser_->show();
}
void
DvonnWindowImpl::about()
{
  QMessageBox::about(this, " D v o n n",tr("D v o n n\nCreated by Xavier D�coret\nVersion 1.0 - August 2004"));
}
void
DvonnWindowImpl::load()
{
#if QT_VERSION < 0x040000
  QString fileName = QFileDialog::getOpenFileName("","Dvonn files (*.dvo);;All files (*)", this);
#else
  QString fileName = QFileDialog::getOpenFileName(this, "Select a game", "", "Dvonn files (*.dvo);;All files (*)");
#endif
  
  // In case of Cancel
  if (fileName.isEmpty())
    return;

  game_->load(fileName);
  fileSaveAction->setEnabled(true);
  gameRandomlyFinishAction->setEnabled(game_->phase() != MovePhase);
  gameRandomlyMoveStackAction->setEnabled(game_->phase() == MovePhase);
  gameUndoAction->setEnabled(false);
  gameRedoAction->setEnabled(false);
  dvonnViewer->updateGL();
  updateStatusBar();
}
void
DvonnWindowImpl::save()
{
  game_->save();
}
void
DvonnWindowImpl::saveAs()
{
#if QT_VERSION < 0x040000
  QString fileName = QFileDialog::getSaveFileName("", "Dvonn files (*.dvo);;All files (*)", this, game_->fileName().latin1());
#else
  QString fileName = QFileDialog::getSaveFileName(this, "Save game", game_->fileName(), "Dvonn files (*.dvo);;All files (*)");
#endif

  // In case of Cancel
  if (fileName.isEmpty())
    return;

  QFileInfo fi(fileName);

#if QT_VERSION < 0x040000
  if (fi.extension().isEmpty())
#else
    if (fi.suffix().isEmpty())
#endif
    {
      fileName += ".dvo";
      fi.setFile(fileName);
    }

#if QT_VERSION < 0x040000
  if (fi.exists())
    if (QMessageBox::warning(this ,tr("Existing file"),
			     tr("File ")+fi.fileName()+tr(" already exists.\nSave anyway ?"),
			     QMessageBox::Yes,
			     QMessageBox::Cancel) == QMessageBox::Cancel)
      return;

  if (!fi.isWritable())
    {
      QMessageBox::warning(this ,tr("Cannot save"),
			   tr("File ")+fi.fileName()+tr(" is not writeable."));
      return;
    }
#endif

  game_->saveAs(fileName);
  fileSaveAction->setEnabled(true);
}
void
DvonnWindowImpl::newGame()
{
  if (QMessageBox::warning(this ,tr("New game"),
			   tr("Quit current game to start new?"),
			   QMessageBox::Yes,
			   QMessageBox::No) == QMessageBox::Yes)
  {
    game_->reinit();
    gameRandomlyFinishAction->setEnabled(true);
    gameRandomlyMoveStackAction->setEnabled(false);
    gameUndoAction->setEnabled(false);
    gameRedoAction->setEnabled(false);
    dvonnViewer->updateGL();
    startAnimScoreTimer_->stop();
    updateStatusBar();
  }
}
void
DvonnWindowImpl::updateStatusBar()
{
  currentPhaseLB_->setText(labelFor(game_->phase()));
  currentPlayerLB_->setText(labelFor(game_->theOnePlaying()));
}
void
DvonnWindowImpl::randomlyFinishPlacement()
{
  game_->randomlyFinishPlacement();
  gameRandomlyFinishAction->setEnabled(false);
  gameRandomlyMoveStackAction->setEnabled(true);
  gameUndoAction->setEnabled(true);
  gameRedoAction->setEnabled(false);
  dvonnViewer->updateGL();
  updateStatusBar();
}
void
DvonnWindowImpl::randomlyMoveStack()
{
  if (game_->phase() != MovePhase) return;
  Game::Move m;
  if (game_->getRandomMove(game_->theOnePlaying(),m))
  {
    dvonnViewer->animateMove(m);
    gameRandomlyMoveStackAction->setEnabled(!game_->isOver());
    gameUndoAction->setEnabled(true);
    gameRedoAction->setEnabled(false);
    dvonnViewer->updateGL();
  }
  updateStatusBar();
}
void
DvonnWindowImpl::play(dvonn::Game::Placement p)
{
  game_->doPlacement(p);
  gameRandomlyFinishAction->setEnabled(game_->phase() != MovePhase);
  gameRandomlyMoveStackAction->setEnabled(game_->phase() == MovePhase);
  gameUndoAction->setEnabled(true);
  gameRedoAction->setEnabled(false);
  dvonnViewer->updateGL();
  updateStatusBar();
}
void
DvonnWindowImpl::play(dvonn::Game::Move m)
{
  bool wasOVer = game_->isOver();
  // When the game is over, we allow any moves so we can animate scores
  game_->doMove(m);
  dvonnViewer->fadeOut(game_->killedBy(m));
  gameRandomlyMoveStackAction->setEnabled(game_->phase() == MovePhase);
  gameUndoAction->setEnabled(true);
  gameRedoAction->setEnabled(false);
  dvonnViewer->updateGL();
  updateStatusBar();
  if (game_->isOver())
  {
    if (wasOVer)
      animateScore();
    else
      startAnimScoreTimer_->start(1000);
  }
}
void
DvonnWindowImpl::print()
{
  // TODO: print also the list of moves
  cout<<game_->board().prettyPrinted()<<endl;
}
void
DvonnWindowImpl::undo()
{
  game_->undo();
  gameRandomlyFinishAction->setEnabled(game_->phase() != MovePhase);
  gameRandomlyMoveStackAction->setEnabled(game_->phase() == MovePhase);
  gameUndoAction->setEnabled(game_->canUndo());
  gameRedoAction->setEnabled(true);
  dvonnViewer->stopAllAnimations();
  startAnimScoreTimer_->stop();
  dvonnViewer->updateGL();
  updateStatusBar();
}
void
DvonnWindowImpl::redo()
{
  game_->redo();
  gameRandomlyFinishAction->setEnabled(game_->phase() != MovePhase);
  gameRandomlyMoveStackAction->setEnabled(game_->phase() == MovePhase);
  gameUndoAction->setEnabled(true);
  gameRedoAction->setEnabled(game_->canRedo());
  dvonnViewer->stopAllAnimations();
  dvonnViewer->updateGL();
  updateStatusBar();
}
void
DvonnWindowImpl::animateScore()
{
  dvonnViewer->animateScore();
  startAnimScoreTimer_->stop();
}
