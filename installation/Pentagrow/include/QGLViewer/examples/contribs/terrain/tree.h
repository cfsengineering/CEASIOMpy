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

// TP OpenGL: Joerg Liebelt, Serigne Sow
//on ajoute des arbres
#ifndef __TREEBOX_H__
#define __TREEBOX_H__

#include "quadtree.h"

class TREE
{
private:
  QImage texture;
  GLuint texID;
  bool iwanttrees;
  float treeSizeFactor;
  int numTrees;
  qglviewer::Vec* treeInfo;
  //ici, je casse la beaute de mon architecture car avec la ligne suivante,
  //...TREE depend de QUADTREE et n'est plus independant de la maniere dont le terrain a ete cree. dommage..
  QUADTREE myTerrain;		//pour recuperer l'hauteur du terrain

public:
  TREE()
  {
    iwanttrees = false;
    treeSizeFactor = 0.05f;
    numTrees = 20;
  }

  bool LoadTexture(const QString& filename );

  void initTrees(QUADTREE ter, int num, float waterLevel);

  void Render();

  void switchTree() { iwanttrees = !iwanttrees; }

  bool wantTree() { return iwanttrees; }

};


#endif
