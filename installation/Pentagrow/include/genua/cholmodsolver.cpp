
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

#include "cholmodsolver.h"
#include "configparser.h"

CholmodContext::CholmodContext()
{
  cholmod_l_start(&m_common);
  cholmod_l_defaults(&m_common);
}

CholmodContext::~CholmodContext()
{
  release();
  cholmod_l_finish(&m_common);
}

const char *CholmodContext::lastMessage() const
{
  static const char *msg[9] = {"Cholmod: All is well.",
                               "Cholmod: Method not installed.",
                               "Cholmod: Out of memory.",
                               "Cholmod: Integer overflow.",
                               "Cholmod: Invalid input.",
                               "Cholmod: GPU fatal error",
                               "Cholmod: Not positive definite.",
                               "Cholmod: Tiny diagonal value.",
                               "Cholmod: Unknown error code."};

  switch (m_common.status) {
  case CHOLMOD_OK:
    return msg[0];
  case CHOLMOD_NOT_INSTALLED:
    return msg[1];
  case CHOLMOD_OUT_OF_MEMORY:
    return msg[2];
  case CHOLMOD_TOO_LARGE:
    return msg[3];
  case CHOLMOD_INVALID:
    return msg[4];
  case CHOLMOD_GPU_PROBLEM:
    return msg[5];
  case CHOLMOD_NOT_POSDEF:
    return msg[6];
  case CHOLMOD_DSMALL:
    return msg[7];
  default:
    return msg[8];
  }
}

void CholmodContext::release()
{
  if (m_psparse != nullptr)
    cholmod_l_free_sparse(&m_psparse, &m_common);
  m_psparse = nullptr;
}

void CholmodContext::configure(const ConfigParser &cfg)
{
  if (cfg.hasKey("MatrixOrdering")) {
    m_common.nmethods = 1;
    std::string m = toLower( cfg["MatrixOrdering"] );
    if (m == "natural")
      m_common.method[0].ordering = CHOLMOD_NATURAL;
    else if (m == "metis")
      m_common.method[0].ordering = CHOLMOD_METIS;
    else if (m == "amd")
      m_common.method[0].ordering = CHOLMOD_AMD;
    else if (m == "colamd")
      m_common.method[0].ordering = CHOLMOD_COLAMD;
    else if (m == "nesdis")
      m_common.method[0].ordering = CHOLMOD_NESDIS;
    else
      m_common.method[0].ordering = CHOLMOD_METIS;
  }
}



