
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
 
#ifndef SURF_IGESLINE_H
#define SURF_IGESLINE_H

#include <genua/defines.h>

#include <cstring>
#include <iostream>
#include <cstdio>
#include <cassert>

inline void iges_insert(char a[], int len, int x)
{
  int neg = 0;
  if (x == 0) {
    a[len-1] = '0';
    return;
  } else if (x < 0) {
    neg = 1;
    x = -x;
  }

  int i = len-1;
  while (x != 0 and i >= 0) {
    int d = x%10;
    a[i] = '0' + d;
    x /= 10;
    --i;
  }

  if (neg and i >= 0)
    a[i] = '-';
}

/** Insert integer into static buffer.

  This function is used to assemble lines for the IGES file
  export facility. It takes a static buffer and its length
  and writes the integer x right-justified into the field.

  The C99 function snprintf() does the same and more,
  but is not available on Windows.

  \sa IgesFile
 */
inline void iges_insert(char a[], int len, int x, char pad)
{
  for (int k=0; k<len; ++k)
    a[k] = pad;
  iges_insert(a, len, x);
}

/** Line in IGES file

  Inline-only implementation of fixed-length lines in IGES files. Allowed
  section letters are 'S' (start section), 'G' (general), 'D' (directory),
  'P' (parameter) or 'T' (terminate).

  \ingroup interop
  \sa IgesFile
*/
class IgesLine
{
  public:
      
    /// create an undefined line
    IgesLine() {erase();}
    
    /// erase line, fill with blanks 
    void erase() {
      memset(ms, ' ', 80);
      ms[80] = '\0';
    }
    
    /// pointer to start of data block (72 chars long)
    const char *content() const {return ms;}
    
    /// pointer to start of data block (72 chars long)
    char *content() {return ms;}
    
    /// copy character data into data block (max 72 bytes)
    uint copyContent(uint n, const char *src) {
      int nc = std::min(72u, n);
      memcpy(ms, src, nc);
      return nc;
    }
    
    /// put an integer v in position i of a fixed format line  
    void fixedNumber(int i, int v) {
      assert(i < 9);
      iges_insert(&ms[8*i], 8, v, ' ');
    } 

    /// convert fixed-format field i to integer
    int fixedInteger(int i) const {
      assert(i < 9);
      const char *pos = &ms[8*i];
      if (pos[7] == ' ')
        return 0;
      char *tail;
      int v;
      v = strtol(pos, &tail, 10);
      assert(pos != tail);
      return v;
    }
    
    /// assemble a status code for the directory section 
    void statusCode(uint blank, uint subswitch, uint useflag, uint hierarchy) {
      assert(blank < 100);
      assert(subswitch < 100);
      assert(useflag < 100);
      assert(hierarchy < 100);
      iges_insert(&ms[64], 4, 100*blank + subswitch, '0');
      iges_insert(&ms[68], 4, 100*useflag + hierarchy, '0');
    }
    
    /// set section letter 
    void section(char sl) { 
      assert(sl == 'S' or sl == 'G' or sl == 'D' or sl == 'P' or sl == 'T');
      ms[72] = sl; 
    }

    /// retrieve section letter 
    char section() const {return ms[72];}
    
    /// set line number 
    void number(uint ln) {
      assert(ln < 9999999);
      iges_insert(&ms[73], 7, ln, ' ');
    }
    
    /// retrieve line number 
    uint number() const {
      return atoi(&ms[73]);
    } 
    
    /// write line to stream 
    void write(std::ostream & os) const {
      // make sure that the the string is terminated
      char *pms = const_cast<char*>(ms);
      pms[80] = '\0';
      os << pms << std::endl;
    }
    
    /// read from stream 
    void read(std::istream & is) {
      std::string line;
      std::getline(is, line);
      int n = std::min(line.length(), size_t(80));
      memcpy(ms, line.c_str(), n);
      ms[80] = '\0';
    }

  private:
    
    /// line string 
    char ms[81];
};

typedef std::vector<IgesLine> IgesLineArray;

#endif
