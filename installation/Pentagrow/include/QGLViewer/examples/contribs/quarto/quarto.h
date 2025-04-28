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

#ifndef QUARTO_H
#define QUARTO_H

#include <qvariant.h>
#include <qmainwindow.h>
#include "glview.h"
#include "piece.h"
#include <iostream>

class QVBoxLayout;
class QHBoxLayout;
class QGridLayout;
class QPopupMenu;
class QFrame;
class QGroupBox;
class QLabel;
class QPushButton;
class QWidget;

class Quarto : public QMainWindow
{
  Q_OBJECT

public:
#if QT_VERSION < 0x040000
  Quarto(QWidget* parent=NULL, const char* name=0, WFlags fl=WType_TopLevel);
#else
  Quarto(QWidget* parent=NULL);
#endif

  ~Quarto();

  QFrame* GLFrameJeu, *GLFramePieces;
  // buttons
  QGroupBox* GameGroupBox;
  QLabel* TourDeJeuLabel, *NomLabel;
  QPushButton* ResetButton, *QuitButton;
  QPopupMenu *GagnantPopUp;

public slots:
  virtual void New();
  virtual void Exit();
  virtual void changeTour();
  virtual void piecePlacee();
  virtual void finDeJeu();

signals:
  void updategl();

protected:
  QVBoxLayout* QuartoLayout, *VLayout1, *VLayout2, *VLayout3;
  QHBoxLayout* MainHLayout, *HLayout1, *HLayout2, *HLayout3, *HLayout4;

  bool joueur;
  bool pieceplacee;
  int width, height;
  GLViewJeu *vuePlateau;
  GLViewPieces *vuePieces;
  SetOfPiece *setofpiece;
  virtual void init(bool);
};

#endif // QUARTO_H
