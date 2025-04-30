
/* Copyright (C) 2015 David Eller <david@larosterna.com>
 * 
 * Commercial License Usage
 * Licensees holding valid commercial licenses may use this file in accordance
 * with the terms contained in their respective non-exclusive license agreement.
 * For further information contact david@larosterna.com .
 *
 * GNU General Public License Usage
 * Alternatively, this file may be used under the terms of the GNU General
 * Public License version 3.0 as published by the Free Software Foundation and
 * appearing in the file gpl.txt included in the packaging of this file.
 */
 
#ifndef SURF_DNBOXADAPTOR_H
#define SURF_DNBOXADAPTOR_H

#include <genua/bounds.h>
#include "dnrefine.h"

/** Adapts mesh generation criterion.
 *
 * \ingroup meshgen
 * \sa DnMesh
 */
class DnBoxAdaptor : public DnRefineCriterion
{
  public:
    
    /// use criterion c inside
    DnBoxAdaptor(const DnRefineCriterion & c) : DnRefineCriterion(c), crit(c) {}
    
    /// bind to mesh object
    virtual void bind(const DnMesh *pm) const;
    
    /// register a refinement box around these points 
    void addBox(const BndRect & br);
    
    /// register a refinement box around these points 
    void addBox(const PointList<2> & pts);
    
    /// evaluate criterion 
    virtual Real eval(const uint *vi) const;
    
    /// clone object 
    virtual DnBoxAdaptor *clone() const;
  
  private:
    
    /// criterion to use inside the boxes
    const DnRefineCriterion & crit;
    
    /// set of bounding boxes in which to ally c
    std::vector<BndRect> boxes;
};

#endif
