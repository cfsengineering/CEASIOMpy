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

#include <QGLViewer/qglviewer.h>

class Luxo
{
public :
  Luxo();

  void draw(bool names=false);

  qglviewer::ManipulatedFrame* frame(unsigned short i) { return frame_[i]; }
  void setSelectedFrameNumber(unsigned short nb) { selected = nb; }

private :
  // The four articulations of the lamp
  qglviewer::ManipulatedFrame* frame_[4];
  // Used to draw the selected element in a different color
  unsigned short selected;

  void drawCone(float zMin, float zMax, float r1, float r2, int nbSub);
  void drawBase();
  void drawArm();
  void drawCylinder();
  void setColor(unsigned short nb);
  void drawHead();
};


class Viewer : public QGLViewer
{
protected :
  virtual void draw();
  virtual void init();
  virtual void drawWithNames();
  virtual void postSelection(const QPoint& point);
  virtual QString helpString() const;

  void initSpotLight();

private :
  Luxo luxo;
};

