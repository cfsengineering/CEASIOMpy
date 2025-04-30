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

#ifndef PIECE_H
#define PIECE_H

#include <qgl.h>
#include <math.h>
#include <iostream>

/*
 * Classe decrivant une piece
 */
class Piece {
private:
  int id;
  bool selected;
  bool fenetre;
  bool couleur;
  bool taille;
  bool forme;
  bool trou;
  double x_pos, y_pos;
  GLfloat amb_diff[3];
  GLfloat specular[3];
  GLfloat shininess;
  GLuint texture;

  void drawRectangle();
  void drawCylinder();
  void drawBoite();
  void drawBoule();

public:
  Piece(int, bool, bool, bool, bool, double, double);
  ~Piece() {}
  void paint(bool);
  void setSelected(bool s) { selected=s; }
  void setFenetre(bool f) { fenetre=f; }
  void setPos(double x, double y) { x_pos=x; y_pos=y; }
  void setTexture( GLuint t) { texture=t; }
  bool getTaille() { return taille; }
  bool getCouleur() { return couleur; }
  bool getForme() { return forme; }
  bool getTrou() { return trou; }
};

/*
 * Ensemble des pieces du jeu
 */
class SetOfPiece {
private:
  Piece* tab[16];
  int selected;

public:
  SetOfPiece();
  ~SetOfPiece() {
    for(int i=0; i<16; i++)
      delete(tab[i]);
  }
  void init();
  void paint(bool);
  void setSelected(int);
  void setTexture(GLuint);
  void placeSelectedPiece(int);
  Piece* getPiece() { return tab[selected]; }
};

#endif // PIECE_H
