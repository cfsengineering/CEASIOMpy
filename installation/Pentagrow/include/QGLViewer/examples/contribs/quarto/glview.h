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

#ifndef GLVIEW_H
#define GLVIEW_H

#include <qgl.h>
#include <QGLViewer/qglviewer.h>
#include <iostream>
#include "jeu.h"
#include "piece.h"

/*
 * Classe generique pour les fenetres OpenGl
 */
class GLView : public QGLViewer
{
  Q_OBJECT
public:
  GLView(QWidget* parent) : QGLViewer(parent) {}

  virtual void init();
  virtual void setPieces(SetOfPiece *sop) { setofpiece=sop; };

signals:
  void update();

protected:
  virtual void select(const QMouseEvent* e);
  virtual void drawWithId() {};
  virtual void applySelection(int) {};
  virtual void keyPressEvent(QKeyEvent *) {};

  SetOfPiece *setofpiece;

private:
  GLuint texture_bois;
};



// Classe fille pour la vue des pieces a selectionner
class GLViewPieces : public GLView
{
  Q_OBJECT
public:
  GLViewPieces(QWidget* parent) : GLView(parent) {}

protected:
  virtual void draw();
  virtual void init();

  virtual void drawWithId() { draw(); };
  virtual void applySelection(int);

signals:
  void changeJoueur();
};



// Classe fille pour la vue du plateau de jeu
class GLViewJeu : public GLView
{
  Q_OBJECT

public:
  GLViewJeu(QWidget* parent) : GLView(parent) {}
  ~GLViewJeu() { glDeleteLists(plateau, 1); }

  void reset() { jeu.init(); }

protected :
  virtual void draw();
  virtual void init();

  virtual void drawWithId();
  virtual void applySelection(int);

signals:
  void piecePlacee();
  void endGame();

private:
  GLuint plateau;
  Jeu jeu;

  void makePlateau();
};

#endif // GLVIEW_H
