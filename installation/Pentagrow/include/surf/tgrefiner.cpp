
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

#include "tgrefiner.h"
#include <genua/mxmesh.h>
#include <genua/configparser.h>
#include <genua/ioglue.h>
#include <genua/xcept.h>
#include <genua/parallel_loop.h>

uint TgRefiner::appendBox(const Vct3 &plo, const Vct3 &phi, Real len)
{
  m_boxes.push_back(Dop3d3<Real>(plo.pointer(), phi.pointer()));
  m_lbox.push_back(len);
  return m_lbox.size() - 1;
}

void TgRefiner::configure(const ConfigParser &cfg)
{
  // global edge length smoothing options
  m_fgrowth = cfg.getFloat("TetGrowthFactor", m_fgrowth);
  m_nsiter = cfg.getInt("TetEdgeSmoothing", m_nsiter);
  m_ndistrib = cfg.getInt("TetEdgeDistrib", m_ndistrib);

  // definition of refinement boxes
  m_boxes.clear();
  m_lbox.clear();
  const int nbox = cfg.getInt("RefineBoxCount", 0);
  if (nbox > 0)
  {

    Vector xlim(2 * nbox), ylim(2 * nbox), zlim(2 * nbox), lb(nbox);
    fromString(cfg["RefineBoxXLimits"], xlim);
    fromString(cfg["RefineBoxYLimits"], ylim);
    fromString(cfg["RefineBoxZLimits"], zlim);
    fromString(cfg["RefineBoxEdgeLength"], lb);

    for (int i = 0; i < nbox; ++i)
    {
      Vct3 plo(xlim[2 * i], ylim[2 * i], zlim[2 * i]);
      Vct3 phi(xlim[2 * i + 1], ylim[2 * i + 1], zlim[2 * i + 1]);
      appendBox(plo, phi, lb[i]);
    }
  }

  cout << m_lbox.size() << " refinement boxes configured." << endl;
}

const Vector &TgRefiner::edgeLengths(MxMesh &msh)
{
  ConnectMap map;
  msh.fixate();
  msh.v2vMap(map);

  const int nv = msh.nnodes();
  std::vector<bool> onBound(nv, false);
  for (uint i = 0; i < msh.nsections(); ++i)
  {
    if (msh.section(i).surfaceElements())
    {
      const Indices &nds = msh.section(i).nodes();
      const uint nns = nds.size();
      for (uint j = 0; j < nns; ++j)
        onBound[nds[j]] = true;
    }
  }
  m_ledg.allocate(nv);

  // #pragma omp parallel for schedule(static, 1024)
  BEGIN_PARLOOP_CHUNK(0, nv, 1024)
  for (int i = a; i < b; ++i)
  {
    m_ledg[i] = maxBoxedLength(msh.node(i));
    ConnectMap::const_iterator itr, last = map.end(i);
    int nnb = map.size(i);
    if (nnb > 1)
    {
      Real len(0);
      for (itr = map.begin(i); itr != last; ++itr)
        len += norm(msh.node(*itr) - msh.node(i));
      len /= (nnb - 1);
      m_ledg[i] = std::min(m_ledg[i], len);
    }
  }
  END_PARLOOP_CHUNK
  Vector av(m_ledg), bv(nv);
  for (int j = 0; j < m_nsiter; ++j)
  {

    // #pragma omp parallel for schedule(static, 1024)
    BEGIN_PARLOOP_CHUNK(0, nv, 1024)
    for (int i = a; i < b; ++i)
    {
      Real ai = av[i];
      bv[i] = 0.5 * ai;
      ConnectMap::const_iterator itr, last = map.end(i);
      Real sum = 0;
      for (itr = map.begin(i); itr != last; ++itr)
        sum += std::min(ai, m_fgrowth * av[*itr]);
      bv[i] += 0.5 * sum / map.size(i);
    }
    END_PARLOOP_CHUNK
    av.swap(bv);
  }

  for (int j = 0; j < m_ndistrib; ++j)
  {
    BEGIN_PARLOOP_CHUNK(0, nv, 1024)
    for (int i = a; i < b; ++i)
    {
      if (onBound[i])
        continue;
      Real ai = av[i];
      bv[i] = 0.5 * ai;
      ConnectMap::const_iterator itr, last = map.end(i);
      Real sum = 0;
      for (itr = map.begin(i); itr != last; ++itr)
        sum += av[*itr];
      bv[i] += 0.5 * sum / map.size(i);
    }
    END_PARLOOP_CHUNK
    av.swap(bv);
  }

  m_ledg.swap(av);
  return m_ledg;
}

void TgRefiner::writeMetricFile(const std::string &fname) const
{
  const size_t nv = m_ledg.size();
  ofstream os(fname.c_str());
  os << nv << " 1" << endl;
  for (size_t i = 0; i < nv; ++i)
    os << m_ledg[i] << endl;
}
