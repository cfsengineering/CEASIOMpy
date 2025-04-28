//
// project:      scope
// file:         planegrid.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// Draw reference grid overlay

#ifndef SCOPE_PLANEGRID_H
#define SCOPE_PLANEGRID_H

#include <genua/point.h>

class PlaneGrid
{
  public:

    /// undefined grid
    PlaneGrid() : nstrip(0), bVisible(false) {}

    /// create grid normal to pn, edges at hi,low
    void create(const Vct3f & pn, float offs,
                const Vct3f & clo, const Vct3f & chi);

    /// draw grid strips
    void glDraw() const;

    /// switch on/off
    void toggle(bool flag) {bVisible = flag;}

    /// currently enabled?
    bool visible() const {return bVisible;}

    /// offset from origin
    float offset() const {return fOffset;}

    /// update for changed bounding box
    void rescale(const Vct3f & clo, const Vct3f & chi);

  private:

    /// grid vertices (quad strips)
    PointList<3,float> vtx;

    /// plane normal
    Vct3f vNormal;

    /// plane offset
    float fOffset;

    /// number of strips to draw (quad columns)
    uint nstrip;

    /// switch on/off
    bool bVisible;
};

#endif // PLANEGRID_H
