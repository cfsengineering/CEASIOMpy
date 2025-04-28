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
// generation d'eau: calcul vitesses,normales,reflections
#ifndef __WATER_H__
#define __WATER_H__

#include <QGLViewer/qglviewer.h>
#include <math.h>
#include <qcolor.h>

#define WATER_RESOLUTION 60
#define SQR( number )		( number*number )

using namespace qglviewer;		//classe VEC

class WATER
{
private:
  Vec vertArray[SQR( WATER_RESOLUTION )];		//champ de vertex
  Vec normalArray[SQR( WATER_RESOLUTION )];	//champ des normales de vertex
  float forceArray[SQR( WATER_RESOLUTION )];	//champ des forces influencant un vertex d'eau
  float velArray[SQR( WATER_RESOLUTION )];	//champ de vitesses des vagues
  int polyIndexArray[SQR( ( WATER_RESOLUTION-1 ) )*6];	//champ des indices des polygones (pour updates..)

  float worldSize;

  bool iwantwater;

  int numIndices;
  int numVertices;

  QColor color;

  unsigned int refmapID;

public:
  WATER()
  {
    SetColor(QColor("white"));
    iwantwater = false;
  }

  void Init(float myWorldSize, float scaleHeight);

  void Update(float delta);
  void CalcNormals();
  void Render();

  void switchWater() { iwantwater = !iwantwater; }

  bool wantWater() { return iwantwater; }

  void LoadReflectionMap(const QString& filename);

  void SetColor(const QColor& col) { color = col; }
};


#endif	//__WATER_H__
