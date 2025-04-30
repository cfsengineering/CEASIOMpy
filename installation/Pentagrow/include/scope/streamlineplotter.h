#ifndef SCOPE_STREAMLINEPLOTTER_H
#define SCOPE_STREAMLINEPLOTTER_H

#include <genua/forward.h>
#include <genua/defines.h>
#include <genua/point.h>
#include <genua/color.h>
#include <genua/propmacro.h>
#include <vector>

/** Draw a set of streamlines.
 *
 */
class StreamlinePlotter
{
public:

  /// construct empty plotter
  StreamlinePlotter();

  /// destroy buffers
  ~StreamlinePlotter();

  /// extract data from analysis object
  void assign(const SurfaceStreamlines &ssf);

  /// assemble OpenGL buffers
  void build(bool dynamicDraw = false);

  /// draw buffers
  void draw() const;

private:

  /// storage for streamline coordinates
  PointList3f m_lines;

  /// offsets in vertex buffer
  std::vector<uint> m_loffset;

  /// vertex buffer
  uint m_vbuf = NotFound;

  /// solid color to use for all streamlines
  GENUA_PROP(Color, solidColor)

  /// visibility status
  GENUA_PROP(bool, visible)
};

#endif // STREAMLINEPLOTTER_H
