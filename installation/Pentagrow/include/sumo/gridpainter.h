
/* ------------------------------------------------------------------------
 * file:       gridpainter.h
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Draw a grid of quads using OpenGL
 * ------------------------------------------------------------------------ */

#ifndef SUMO_GRIDPAINTER_H
#define SUMO_GRIDPAINTER_H

#include <genua/point.h>
#include <genua/smatrix.h>

/** Draw a grid of quads using OpenGL.

  GridPainter is a specialized renderer which exclusively
  draws quadrilateral grids with vertex-based normals and
  colors. It is/will be used to draw the current geometry
  by employing one GridPainter per surface.

  */
class GridPainter
{
  public:

    /// create empty painter, does nothing
    GridPainter();

    /// free resources
    ~GridPainter();

    /// issue OpenGL drawing commands
    void draw();

    /// change view transformation
    void setTransform(const Mtx44f & m) {vtf = m;}

    /// change color to use
    void setColor(const Vct4f & c) {clr = c;}

    /// use another grid
    void use(const PointGrid<3> & vtx, const PointGrid<3> & nrm);

  private:

    /// initialize vertex buffers
    void initBuffers();

    /// initialize display list
    void initDisplayList();

    /// draw using VBOs
    void drawBuffers();

  private:

    /// stores converted point data
    PointList<3,float> vf, nf;

    /// strip data
    Indices strips;

    /// pointer offsets for use with MultiDrawElements
    std::vector<const char*> poff;

    /// pointer offsets for use with MultiDrawElements
    std::vector<int> pcount;

    /// vertex buffer objects
    uint vbo[3];

    /// display list to use in fallback mode
    uint idispl;

    /// additional model view transformation
    Mtx44f vtf;

    /// color to use for all quads
    Vct4f clr;

    /// number of strips and length of strips
    int nstrips, striplen;

    /// use vertex buffer objects or not?
    bool useVbo, init;
};

#endif // GRIDPAINTER_H
