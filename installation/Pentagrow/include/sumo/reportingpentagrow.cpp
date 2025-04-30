
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
 
#include <QString>

#include "reportingpentagrow.h"

void LogReporter::log(const std::string &s)
{
  emit logMessage( QString::fromStdString(s) );
}

ReportingPentaGrow::ReportingPentaGrow(const TriMesh &m) : PentaGrow(m)
{
  m_reporter = new LogReporter;
}

ReportingPentaGrow::~ReportingPentaGrow()
{
  delete m_reporter;
}

void ReportingPentaGrow::log(const std::string &s) const
{
  m_reporter->log(s);
}
