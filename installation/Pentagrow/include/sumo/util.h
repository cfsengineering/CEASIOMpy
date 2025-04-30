
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
 
#ifndef SUMO_UTIL_H
#define SUMO_UTIL_H

#include <genua/strutils.h>
#include <QString>
#include <QByteArray>
#include <string>

inline std::string str(const QString &s)
{
  // keep the temporary QByteArray
  QByteArray a = s.toUtf8();
  return std::string( a.constData() );
}

#ifdef _MSC_VER

inline std::wstring asPath(const QString &s)
{
  return std::wstring( (const wchar_t*) s.utf16() );
}

#else

inline std::string asPath(const QString &s)
{
  return str(s);
}

#endif

inline QString qstr(const std::string &s)
{
  return QString::fromUtf8( s.c_str() );
}

inline QString qstr(const char *s)
{
  return QString::fromUtf8( s );
}

inline std::string append_suffix(const QString &s, const char *sfx)
{
  // make sure the compiler picks append_suffix(string, string)
  QByteArray a = s.toUtf8();
  return append_suffix( std::string(a.constData()), std::string(sfx) );
}

#endif // UTIL_H
