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

#include <QGLViewer/camera.h>

class CullingCamera;

// An Axis Aligned Bounding Box octree hierarchy element.
class Box
{
public:
  Box(const qglviewer::Vec& P1, const qglviewer::Vec& P2) : p1(P1), p2(P2) {};

  void draw() const;
  void drawIfAllChildrenAreVisible(const CullingCamera* camera) const;
  void buildBoxHierarchy(int l);

  // Lazy static member, so that it is shared by viewers
  static Box* Root;
  
private:
  qglviewer::Vec p1, p2;
  Box* child[8];
  int level;
};
