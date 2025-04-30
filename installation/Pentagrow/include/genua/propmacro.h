
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
 
#ifndef GENUA_PROPMACRO_H
#define GENUA_PROPMACRO_H

/** \file propmacro.h
 *
 *  Macros to declare properties with named accessor functions. These are
 *  mostly used for objects which need to interface with user interface
 *  elements.
 *
 *  \verbatim
 *  GENUA_PROP_INI(float, length, 0.0f)
 *  \endverbatim
 *
 *  expands to
 *  \verbatim
 *  public:
 *    const float &length() const {return m_length;}
 *    void length(const float &x) {m_length = x;}
 *  private:
 *    float m_length = 0.0f;
 *  \endverbatim
 *
 * \ingroup utility
 **/

#define GENUA_PROP(type, name) \
public: \
const type& name() const {return m_ ## name;} \
void name(const type &x) {m_ ## name = x;} \
private: \
type m_ ## name;

#define GENUA_PROP_INI(type, name, ini) \
public: \
const type& name() const {return m_ ## name;} \
void name(const type &x) {m_ ## name = x;} \
private: \
type m_ ## name = ini;

#define GENUA_PXSTR(s) GENUA_PSTR(s)
#define GENUA_PSTR(s) #s

#define GENUA_PROP2XML(name) \
  xe[ GENUA_PSTR(name) ] = str( m_ ## name );

#define GENUA_XML2PROP(name) \
  xe.fromAttribute(GENUA_PSTR(name), name);

#endif // PROPMACRO_H

