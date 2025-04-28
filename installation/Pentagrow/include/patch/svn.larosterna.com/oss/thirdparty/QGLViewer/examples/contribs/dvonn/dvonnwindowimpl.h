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

#ifndef DVONNWINDOWIMPL_H
#define DVONNWINDOWIMPL_H

#include <qglobal.h>

#if QT_VERSION >= 0x040000
# include "ui_dvonnwindow.Qt4.h"
  class DvonnWindow : public QMainWindow, public Ui::DvonnWindow
  {
  public:
    DvonnWindow() { setupUi(this); }
  };
#else
# if QT_VERSION >= 0x030000
#  include "dvonnwindow.Qt3.h"
# else
#  error "No designer .ui file available for Qt 2"
# endif
#endif
#include "game.h"

class QTextBrowser;
class QLabel;
class QTimer;

//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
// Interface of DvonnWindowImpl
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
class DvonnWindowImpl : public DvonnWindow
{
  Q_OBJECT
public:
  DvonnWindowImpl(dvonn::Game* g);
public slots:
  void load();
  void save();
  void saveAs();
  void print();

  void newGame();
  void undo();
  void redo();

  void help();
  void about();

  void randomlyFinishPlacement();
  void randomlyMoveStack();
  void play(dvonn::Game::Placement);
  void play(dvonn::Game::Move);
protected:
  QString labelFor(dvonn::Player);
  QString labelFor(dvonn::Phase);
  void updateStatusBar();
protected slots:
  void animateScore();
private:
  dvonn::Game*  game_;
  QTextBrowser* rulesBrowser_;
  QLabel*       currentPlayerLB_;
  QLabel*       currentPhaseLB_;
  QTimer*       startAnimScoreTimer_;

};

#endif // DVONNWINDOWIMPL_H
