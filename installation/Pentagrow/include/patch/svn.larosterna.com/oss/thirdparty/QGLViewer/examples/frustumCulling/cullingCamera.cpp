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

#include "cullingCamera.h"

using namespace qglviewer;

float CullingCamera::distanceToFrustumPlane(int index, const Vec& pos) const
{
  return pos * Vec(planeCoefficients[index]) - planeCoefficients[index][3];
}

bool CullingCamera::sphereIsVisible(const Vec& center, float radius) const
{
  for (int i=0; i<6; ++i)
    if (distanceToFrustumPlane(i, center) > radius)
      return false;
  return true;
}

bool CullingCamera::aaBoxIsVisible(const Vec& p1, const Vec& p2, bool* entirely) const
{
  bool allInForAllPlanes = true;
  for (int i=0; i<6; ++i)
    {
      bool allOut = true;
      for (unsigned int c=0; c<8; ++c)
	{
	  const Vec pos((c&4)?p1.x:p2.x, (c&2)?p1.y:p2.y, (c&1)?p1.z:p2.z);
	  if (distanceToFrustumPlane(i, pos) > 0.0)
	    allInForAllPlanes = false;
	  else
	    allOut = false;
	}

      // The eight points are on the outside side of this plane
      if (allOut)
	return false;
    }

  if (entirely)
    // Entirely visible : the eight points are on the inside side of the 6 planes
    *entirely = allInForAllPlanes;

  // Too conservative, but tangent cases are too expensive to detect
  return true;
}
