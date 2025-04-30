
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
 
#include "abstractuvcurve.h"
#include "surface.h"
#include "dcmeshcrit.h"
#include <genua/pattern.h>
#include <genua/dbprint.h>

#include <iostream>
using namespace std;

Vct3 AbstractUvCurve::eval(Real t) const
{
  assert(m_psf);
  Vct2 q = uveval(t);
  return m_psf->eval(q[0], q[1]);
}

Vct3 AbstractUvCurve::derive(Real t, uint k) const
{
  assert(m_psf);
  assert(k < 2);
  Vct2 q = uveval(t);
  Vct2 qd = uvderive(t, k);
  Vct3 Suk = m_psf->derive(q[0], q[1], k, 0);
  Vct3 Svk = m_psf->derive(q[0], q[1], 0, k);
  return Suk*qd[0] + Svk*qd[1];
}

void AbstractUvCurve::tgline(Real t, Vct3 &c, Vct3 &dc) const
{
  Vct2 q, qd;
  uvtgline(t, q, qd);
  Vct3 Su, Sv;
  m_psf->plane(q[0], q[1], c, Su, Sv);
  dc = Su*qd[0] + Sv*qd[1];
}

void AbstractUvCurve::uvtgline(Real t, Vct2 &q, Vct2 &dq) const
{
  q = uveval(t);
  dq = uvderive(t, 1);
}

void AbstractUvCurve::apply()
{
  // do nothing - this transformation is most likely meaningless for
  // curves in parameter space.
}

uint AbstractUvCurve::discretize(const DcMeshCritBase &mcrit, Vector &t) const
{
  uint nmin(4);
  if (t.empty()) {
    t = equi_pattern(nmin);
  } else {
    insert_once(t, 0.0);
    insert_once(t, 1.0);
  }

  // prescribed points
  Vector tpre(t);

  // debug
  // uint iter = 0;

  Vector tin, tmp;
  do {

    tin.clear();
    const int np = t.size();
    for (int i=1; i<np; ++i) {
      if ( mcrit.splitEdge(*this, t[i-1], t[i]) ) {
        Real tmid = 0.5*(t[i] + t[i-1]);
        tin.push_back(tmid);
        continue;
      }
    }

    if (not tin.empty()) {
      tmp.resize(t.size() + tin.size());
      std::merge(t.begin(), t.end(), tin.begin(), tin.end(), tmp.begin());

      // smooth point distribution a little
      const Real omega = 0.3;
      const int ntp = tmp.size();
      t.resize(ntp);
      t.front() = tmp.front();
      t.back() = tmp.back();
      for (int i=1; i<ntp-1; ++i) {
        if (binary_search(tpre.begin(), tpre.end(), tmp[i]))
          t[i] = tmp[i];
        else
          t[i] = (1.0-omega)*tmp[i] + 0.5*omega*(tmp[i-1] + tmp[i+1]);
      }
    }

//    ++iter;
//    cout << "Curve " << this << " iter "
//         << iter << " insert " << tin.size() << endl;

  } while (not tin.empty());

  return t.size();
}
