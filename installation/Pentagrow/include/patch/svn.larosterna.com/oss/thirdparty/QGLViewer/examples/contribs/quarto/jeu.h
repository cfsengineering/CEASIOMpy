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

#ifndef JEU_H
#define JEU_H

#include "piece.h"

struct cell{
  bool empty;
  Piece *piece;
};

class Jeu {
protected:
  struct cell tab[16];

public:
  Jeu() {}
  ~Jeu() {}

  void init() {
    for(int i=0; i<16; i++) {
      tab[i].empty=true;
      tab[i].piece=NULL;
    }
  }
  bool needDrawing(int);
  void placePiece(int, Piece *);
  bool caracCommune(Piece* pieces[4]);
  bool analyze();
};

#endif //JEU_H
