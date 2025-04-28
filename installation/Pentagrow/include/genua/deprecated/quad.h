
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       quad.h
 * begin:      Oct 2004
 * copyright:  (c) 2004 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * simple datastructure quadrilateral mesh element
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */
 
#ifndef GENUA_QUAD
#define GENUA_QUAD

#include "svector.h"

class QuadMesh;

/** Quadrilateral mesh face.
  */
class Quad
{
  public:
    
    /// undefined construction
    Quad() : srf(0) {}
    
    /// defined construction
    Quad(const QuadMesh *m, uint v1, uint v2, uint v3, uint v4);
    
    /// alternative form of defined construction
    Quad(const QuadMesh *m, uint vi[4]);

    /// define an ordering
    bool operator< (const Quad & a) const;
    
    /// equivalence
    bool operator== (const Quad & a) const;
    
    /// copy vertex indices
    void getVertices(uint vi[4]) const;
    
    /// compute area center
    Vct3 center() const;
    
    /// compute area
    Real area() const;
    
    /// compute averaged normal vector (normalized!)
    Vct3 normal() const;
    
    /// flip face
    void reverse();
    
  protected:
    
    /// initialize - sort indices correctly
    void init(uint v1, uint v2, uint v3, uint v4);
  
  private:
    
    /// pointer to parent mesh
    const QuadMesh *srf;
    
    /// four node inices
    uint v[4];  
};

#endif
