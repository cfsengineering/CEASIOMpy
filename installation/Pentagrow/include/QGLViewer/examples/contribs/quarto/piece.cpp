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

#include "piece.h"

SetOfPiece::SetOfPiece()
{
  selected=-1;
  // on cr�e et place chaque piece
  for(int i=0; i<16; i++)
    tab[i]=new Piece(i, i/8, (i/4)%2, (i/2)%2, i%2, (i%4)*4.5, (i/4)*4.5 );
}

void SetOfPiece::paint(bool fenetre)
{
  /* activation de la texture */
  glEnable( GL_TEXTURE_2D );
  for(int i=0; i<16; i++)
    tab[i]->paint(fenetre);
  glDisable( GL_TEXTURE_2D );
}

void SetOfPiece::init()
{
  for(int i=0; i<16; i++) {
    tab[i]->setFenetre(false);
    tab[i]->setSelected(false);
    tab[i]->setPos( (i%4)*4.5, (i/4)*4.5 );
  }
}

void SetOfPiece::setTexture(GLuint texture)
{
  for(int i=0; i<16; i++)
    tab[i]->setTexture(texture);
}

void SetOfPiece::placeSelectedPiece(int select)
{
  // Si aucun objet n'est selectionn�, on ne fait rien
  if(selected==-1) return;
  tab[selected]->setFenetre(true);
  tab[selected]->setPos((select%4)*3.5+3.7, (select/4)*3.5+3.7);
}

void SetOfPiece::setSelected(int select)
{
  if(selected!=-1)
    tab[selected]->setSelected(false);
  selected=select;
  tab[selected]->setSelected(true);
}

Piece::Piece(int i, bool c, bool s, bool f, bool t, double x, double y) : id(i), couleur(c), taille(s), forme(f), trou(t), x_pos(x), y_pos(y)
{
  // La fenetre est au debut, celle de selection
  fenetre=false;
  // La piece n'est pas selectionn�e
  selected=false;
  // On initialise les parametres de couleur
    for (int i=0; i<3; ++i)
      {
	amb_diff[i]=(couleur ? (0.4-0.05*i) : (1.0-0.1*i));
	specular[i]=(couleur ? 0.2 : 0.4);
      }
  shininess=120.;
}

void Piece::paint(bool fen)
{
  // Si l'objet ne doit pas etre affich� dans la fenetre, on sort
  if(fenetre!=fen) return;
  // On place l'objet au bon endroit
  glPushMatrix();
  glTranslatef( x_pos, y_pos, 0.5 );
  // on lui donne un nom
  glLoadName(id);
  // On l'affiche
  glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, amb_diff);
  glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, specular);
  glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess);

  // On dessine la piece en fonction de sa forme
  if(forme) drawRectangle();
  else drawCylinder();
  // Si la piece est selectionnee et que l'on est dans la bonne fenetre, on place une boite autour
  if(selected && !fenetre) drawBoite();
  glPopMatrix();
}

void Piece::drawBoite()
{
  int t=3+2*taille;
  glDisable(GL_LIGHTING);
  glDisable( GL_TEXTURE_2D );
  glLineWidth(2.);
  glColor3f(0.75, 0.75, 0.75);
  glPushMatrix();
  glTranslatef(-1.5, -1.5, -0.5);
  for(int i=0; i<2; i++) {
    glBegin(GL_LINE_LOOP);
    glVertex3i(0, 0, (t+1)*i); glVertex3i(3, 0, (t+1)*i);
    glVertex3i(3, 3, (t+1)*i); glVertex3i(0, 3, (t+1)*i);
    glEnd();
  }
  for(int i=0; i<4; i++) {
    glBegin(GL_LINES);
    glVertex3i((i/2)*3, (i%2)*3, 0);
    glVertex3i((i/2)*3, (i%2)*3, t+1);
    glEnd();
  }
  glPopMatrix();
  glEnable(GL_LIGHTING);
  glEnable( GL_TEXTURE_2D );
}

void Piece::drawBoule()
{
  float hauteur=3.1+2*taille;
  static GLUquadricObj *obj = gluNewQuadric();
  gluQuadricDrawStyle(obj, GLU_FILL);
  gluQuadricNormals(obj, GLU_SMOOTH);
  gluQuadricTexture(obj, GLU_TRUE);
  glBindTexture(GL_TEXTURE_2D, texture );

  glPushMatrix();
  glTranslatef(0., 0., hauteur);
  gluSphere(obj, 0.8, 20, 20);
  glPopMatrix();
}

void Piece::drawRectangle()
{
  int hauteur=3+2*taille;
  if(trou) drawBoule();

  glPushMatrix();
  glTranslatef(-1.0,-1.0,0.0);
  // orientation des polygones pour cull face
  glFrontFace(GL_CW);
  // dessous de la piece
  glNormal3d(0, 0, -1);
  glBegin(GL_QUAD_STRIP);
  glTexCoord2i(0, 0 ); glVertex3i( 0, 0, 0 );
  glTexCoord2i(1, 0 ); glVertex3i( 2, 0, 0 );
  glTexCoord2i(0, 1 ); glVertex3i( 0, 2, 0 );
  glTexCoord2i(1, 1 ); glVertex3i( 2, 2, 0 );
  glEnd();
  // cote droit
  glNormal3d(0, 1, 0);
  glBegin(GL_QUAD_STRIP);
  glTexCoord2f(0, 0 ); glVertex3i( 0, 2, 0 );
  glTexCoord2f(0.25, 0 ); glVertex3i( 2, 2, 0 );
  glTexCoord2f(0, 1 ); glVertex3i( 0, 2, hauteur );
  glTexCoord2f(0.25, 1 ); glVertex3i( 2, 2, hauteur );
  glEnd();
  // derriere
  glNormal3d(-1, 0, 0);
  glBegin(GL_QUAD_STRIP);
  glTexCoord2f(0.75, 0 ); glVertex3i( 0, 0, 0 );
  glTexCoord2f(1, 0 ); glVertex3i( 0, 2, 0 );
  glTexCoord2f(0.75, 1 ); glVertex3i( 0, 0, hauteur );
  glTexCoord2f(1, 1 ); glVertex3i( 0, 2, hauteur );
  glEnd();

  // orientation des polygones pour cull face
  glFrontFace(GL_CCW);
  // dessus de la piece
  glNormal3d(0, 0, 1);
  glBegin(GL_QUAD_STRIP);
  glTexCoord2f(0, 0 ); glVertex3i( 0, 0, hauteur );
  glTexCoord2f(1, 0 ); glVertex3i( 2, 0, hauteur );
  glTexCoord2f(0, 1 ); glVertex3i( 0, 2, hauteur );
  glTexCoord2f(1, 1 ); glVertex3i( 2, 2, hauteur );
  glEnd();
  // cote gauche
  glNormal3d(0, -1, 0);
  glBegin(GL_QUAD_STRIP);
  glTexCoord2f(0.25, 0 ); glVertex3i( 0, 0, 0 );
  glTexCoord2f(0.5, 0 ); glVertex3i( 2, 0, 0 );
  glTexCoord2f(0.25, 1 ); glVertex3i( 0, 0, hauteur );
  glTexCoord2f(0.5, 1 ); glVertex3i( 2, 0, hauteur );
  glEnd();
  // devant
  glNormal3d(1, 0, 0);
  glBegin(GL_QUAD_STRIP);
  glTexCoord2f(0.5, 0 ); glVertex3i( 2, 0, 0 );
  glTexCoord2f(0.75, 0 ); glVertex3i( 2, 2, 0 );
  glTexCoord2f(0.5, 1 ); glVertex3i( 2, 0, hauteur );
  glTexCoord2f(0.75, 1 ); glVertex3i( 2, 2, hauteur );
  glEnd();

  glPopMatrix();
}

void Piece::drawCylinder()
{
  int hauteur=3+2*taille;
  if(trou) drawBoule();

  GLUquadricObj *obj;
  obj = gluNewQuadric();
  gluQuadricDrawStyle(obj, GLU_FILL);
  gluQuadricNormals(obj, GLU_SMOOTH);
  gluQuadricTexture(obj, GLU_TRUE);
  glBindTexture(GL_TEXTURE_2D, texture );

  // Corps du cylindre
  gluCylinder(obj, 1., 1., hauteur, 20, 1);
  // Disque inferieur
  gluQuadricOrientation(obj, GLU_INSIDE);
  gluDisk(obj, 0., 1., 20, 1);
  // Disque superieur
  glPushMatrix();
  glTranslatef(0., 0., hauteur);
  gluQuadricOrientation(obj, GLU_OUTSIDE);
  gluDisk(obj, 0., 1., 20, 1);
  glPopMatrix();
  gluDeleteQuadric(obj);
}
