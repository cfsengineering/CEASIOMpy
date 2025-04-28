
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
 
#ifndef SURF_TGREFINER_H
#define SURF_TGREFINER_H

#include <genua/forward.h>
#include <genua/defines.h>
#include <genua/kdop.h>
#include <genua/dvector.h>

/** Auxilliary data for tet mesh refinement using tetgen.
 *
 * TgRefiner is used to write the metric files used by TetGen in order to
 * refine an existing tetrahedral mesh so that it complies with criteria which
 * cannot be expressed inside TetGen. In the present form, this class writes
 * mtr files which approximately enforce an edge growth ratio limit.
 *
 * \ingroup meshgen
 * \sa PentaGrow, MxMesh
 */
class TgRefiner
{
public:

  /// set default values
  TgRefiner() : m_fgrowth(1.4), m_nsiter(64), m_ndistrib(0) {}

  /// add another refinement box
  uint appendBox(const Vct3& plo, const Vct3 &phi, Real len);

  /// read refinement box specification from config file
  void configure(const ConfigParser &cfg);

  /// determine target edge lengths
  const Vector & edgeLengths(MxMesh &msh);

  /// write nodal edge lengths to .mtr file
  void writeMetricFile(const std::string &fname) const;

private:

  /// determine maximum permitted edge length due to boxes
  Real maxBoxedLength(const Vct3 &p) const {
    Real len = std::numeric_limits<Real>::max();
    const int nbox = m_boxes.size();
    for (int i=0; i<nbox; ++i) {
      if (m_boxes[i].inside(p.pointer()))
        len = std::min(len, m_lbox[i]);
    }
    return len;
  }

private:

  /// desired edge length growth factor
  Real m_fgrowth;

  /// number of edge length smoothing iterations
  int m_nsiter, m_ndistrib;

  /// nodal size field to be written to .mtr file
  Vector m_ledg;

  /// refinement boxes
  std::vector< Dop3d3<Real> > m_boxes;

  /// maximum permitted edge length within boxes
  Vector m_lbox;
};

#endif // TGREFINER_H
