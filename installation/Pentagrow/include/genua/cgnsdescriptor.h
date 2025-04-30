
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
 
#ifndef GENUA_CGNSDESCRIPTOR_H
#define GENUA_CGNSDESCRIPTOR_H

#include <string>

/** Adds a Descriptor_t node at the current location in CGNS file.
  *
  * \ingroup mesh
  * \sa CgnsFile
  */
class CgnsDescriptor
{
  public:
    
    /// empty user data (before reading)
    CgnsDescriptor() { std::fill(dname, dname+sizeof(dname), 0); }
    
    /// create a named Descriptor_t node 
    CgnsDescriptor(const std::string & id) {rename(id);}
    
    /// number of descriptor nodes available at path
    uint nnodes(int fn, const std::string & path) const;
    
    /// read descriptor d at the current location
    void read(int d);
    
    /// write node 
    void write(int fn, const std::string & path);
    
    /// add an annotation string
    void text(const std::string & s) {txt = s;}
    
    /// retrieve annotation string
    const std::string & text() const {return txt;}
    
    /// access node name
    std::string name() const {return std::string(dname);}
    
    /// change node name
    void rename(const std::string & s);
    
  private:
    
    /// node name (short)
    char dname[40];
    
    /// node description/annotation
    std::string txt; 
};

#endif
