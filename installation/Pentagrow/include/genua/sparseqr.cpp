
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
 
#include "sparseqr.h"

SpqrContext::SpqrContext() : CholmodContext()
{
  m_ordering = SPQR_ORDERING_DEFAULT;
  m_columnTolerance = SPQR_DEFAULT_TOL;
}

void SpqrContext::configure(const ConfigParser &cfg)
{
  CholmodContext::configure(cfg);
  m_columnTolerance = cfg.getFloat("SpqrColumnTolerance", SPQR_DEFAULT_TOL);
  if (cfg.hasKey("MatrixOrdering")) {
    std::string s = toLower(cfg["MatrixOrdering"]);
    if (s == "fixed")
      m_ordering = SPQR_ORDERING_FIXED;
    else if (s == "natural")
      m_ordering = SPQR_ORDERING_NATURAL;
    else if (s == "colamd")
      m_ordering = SPQR_ORDERING_COLAMD;
    else if (s == "cholmod")
      m_ordering = SPQR_ORDERING_CHOLMOD;
    else if (s == "amd")
      m_ordering = SPQR_ORDERING_AMD;
    else if (s == "metis")
      m_ordering = SPQR_ORDERING_METIS;
    else if (s == "default")
      m_ordering = SPQR_ORDERING_DEFAULT;
    else if (s == "best")
      m_ordering = SPQR_ORDERING_BEST;
    else if (s == "bestamd")
      m_ordering = SPQR_ORDERING_BESTAMD;
    else
      m_ordering = SPQR_ORDERING_DEFAULT;
  } else {
    m_ordering = SPQR_ORDERING_DEFAULT;
  }
}



