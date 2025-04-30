
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
 
#ifndef SCOPE_VERSION_H
#define SCOPE_VERSION_H

#include <genua/programversion.h>

#define SCOPE_VERSION     _UINT_VERSION(2, 2, 10)
#define _scope_version    version_string(SCOPE_VERSION)
#define _scope_qversion   QString::fromStdString(_scope_version)

#endif // VERSION_H
