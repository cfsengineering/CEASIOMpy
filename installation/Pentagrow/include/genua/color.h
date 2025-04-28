
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
 
#ifndef GENUA_COLOR_H
#define GENUA_COLOR_H

#include "defines.h"
#include "forward.h"
#include "algo.h"
#include <cstdlib>

/** Simple color class for visualization.

  This class is used to map float values to a color range, convert HSV to
  RGB color definitions and similar.

  \ingroup utility
  \sa CgMesh
  */
class Color
{
public:

  /// undefined color
  Color() {}

  /// from red, green, blue and alpha
  Color(int r, int g, int b, int a = 255) {
    assert(r >= 0 and r <= 255);
    assert(g >= 0 and g <= 255);
    assert(b >= 0 and b <= 255);
    assert(a >= 0 and a <= 255);
    assign( uint8_t(r), uint8_t(g), uint8_t(b), uint8_t(a));
  }

  /// from red, green, blue and alpha
  Color(uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255) {
    assign(r, g, b, a);
  }

  /// from red, green, blue and alpha
  Color(float r, float g, float b, float a = 1.0f) {
    assign(r, g, b, a);
  }

  /// from another color and different alpha
  Color(const Color &other, float a) {
    assign(other.col[0], other.col[1], other.col[2], uint8_t(a*255));
  }

  /// from red, green, blue and alpha
  explicit Color(float rgb[]) {
    assign(rgb[0], rgb[1], rgb[2]);
  }

  /// compare colors
  bool operator== (const Color & a) const {
    for (int k=0; k<4; ++k)
      if (col[k] != a.col[k])
        return false;
    return true;
  }

  /// compare colors
  bool operator!= (const Color & a) const {
    return !(*this == a);
  }

  /// whether color is all zero
  bool empty() const {
    return (integer() == 0);
  }

  /// access pointer to color values explicitly
  const uint8_t *pointer() const {return col;}

  /// convert channel to int
  int red() const {return ((int) col[0]);}

  /// convert channel to float
  float redf() const {return red()/255.0f;}

  /// convert channel to int
  int green() const {return ((int) col[1]);}

  /// convert channel to float
  float greenf() const {return green()/255.0f;}

  /// convert channel to int
  int blue() const {return ((int) col[2]);}

  /// convert channel to int
  float bluef() const {return blue()/255.0f;}

  /// access by index
  int operator[] (uint k) const {
    assert(k < 4);
    return (int) col[k];
  }

  /// express as integer
  uint32_t integer() const {
    uint32_t r = col[0];
    uint32_t g = col[1];
    uint32_t b = col[2];
    uint32_t a = col[3];
    return ((r << 24) | (g << 16) | (b << 8) | a);
  }

  /// change alpha channel
  void alpha(uint8_t a) {col[3] = a;}

  /// change alpha channel
  void alpha(float a) {col[3] = uint8_t(255*a);}

  /// access alpha channel
  uint8_t alpha() const {return col[3];}

  /// from red, green, blue and alpha
  void assign(uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255) {
    col[0] = r;
    col[1] = g;
    col[2] = b;
    col[3] = a;
  }

  /// from red, green, blue and alpha
  void assign(float r, float g, float b, float a = 1.0f) {
    col[0] = uint8_t( 255*r );
    col[1] = uint8_t( 255*g );
    col[2] = uint8_t( 255*b );
    col[3] = uint8_t( 255*a );
  }

  /// extract from integer
  void assign(uint32_t i) {
    col[3] = static_cast<uint8_t>(i & 0xff);
    col[2] = static_cast<uint8_t>( (i >> 8) & 0xff );
    col[1] = static_cast<uint8_t>( (i >> 16) & 0xff );
    col[0] = static_cast<uint8_t>( (i >> 24) & 0xff );
  }

  /// scale RGB channels, leave alpha alone
  void scaleRgb(float f) {
    col[0] = uint8_t( clamp(int(red()*f), 0, 255) );
    col[1] = uint8_t( clamp(int(green()*f), 0, 255) );
    col[2] = uint8_t( clamp(int(blue()*f), 0, 255) );
  }

  /// return a desaturated version of this (f = 1 yields greyscale)
  Color desaturated(float f) const { return Color::desaturate(*this, f); }

  /// convert from hsv color space
  void hsv2rgb(int ih, int is, int iv)
  {
    float h = (1.0f/360.0f) * ih;
    float s = (1.0f/255.0f) * is;
    float v = (1.0f/255.0f) * iv;
    uint8_t vb = (uint8_t) int(255*v);
    col[3] = 255;

    // catch gray
    if (s == 0) {
      col[0] = col[1] = col[2] = (uint8_t) vb;
      return;
    }

    h *= 6.0f;
    float fh = std::floor(h);
    float f = h - fh;
    uint8_t p = (uint8_t) int(255 * v * ( 1 - s ));
    uint8_t q = (uint8_t) int(255 * v * ( 1 - s * f ));
    uint8_t t = (uint8_t) int(255 * v * ( 1 - s * ( 1 - f ) ));
    switch ( int(fh) ) {
      case 0:
        col[0] = vb;
        col[1] = t;
        col[2] = p;
        break;
      case 1:
        col[0] = q;
        col[1] = vb;
        col[2] = p;
        break;
      case 2:
        col[0] = p;
        col[1] = vb;
        col[2] = t;
        break;
      case 3:
        col[0] = p;
        col[1] = q;
        col[2] = vb;
        break;
      case 4:
        col[0] = t;
        col[1] = p;
        col[2] = vb;
        break;
      case 5:
      default:
        col[0] = vb;
        col[1] = p;
        col[2] = q;
        break;
    }
  }

  /// map value v to color between vblue (low) and vred (high)
  void map(float vblue, float vred, float v, float a = 1.0f)
  {
    // determine min/max
    float vlo, vhi;
    if (vblue < vred) {
      vlo = vblue;
      vhi = vred;
    } else {
      vlo = vred;
      vhi = vblue;
    }

    // use black for NaN and white for Inf
    if ( std::isnan(v) ) {
      assign(0.0f, 0.0f, 0.0f, a);
      return;
    } else if ( not std::isfinite(v) ) {
      assign(1.0f, 1.0f, 1.0f, a);
      return;
    }

    // cutoff at color limit values
    v = std::max(vlo, std::min(vhi, v));

    // normalize value to range [0..1]
    float t = (v-vblue) / (vred-vblue);

    // compute r,g,b channels
    float rgb[3];
    if (t <= 0.25) {
      rgb[0] = 0.0f;
      rgb[1] = 4.0f*t;
      rgb[2] = 1.0f;
    } else if (t <= 0.5) {
      rgb[0] = 0.0f;
      rgb[1] = 1.0f;
      rgb[2] = 2.0f - 4.0f*t;
    } else if (t <= 0.75) {
      rgb[0] = 4.0f*t - 2.0f;
      rgb[1] = 1.0f;
      rgb[2] = 0.0f;
    } else {
      rgb[0] = 1.0f;
      rgb[1] = 4.0f - 4.0f*t;
      rgb[2] = 0.0f;
    }
    assign(rgb[0], rgb[1], rgb[2], a);
  }

  /// find values for blue/red cutoff from spread factor
  static void colorLimits(int nval, const float values[], float spread,
                          float &vblue, float &vred);

  /// generate the hex-encoded string also used in HTML
  std::string str() const {
    char tmp[8];
    const char xmap[] = "0123456789abcdef";
    for (int i=0; i<4; ++i) {
      int a = uint(col[i]) % 16;
      int b = uint(col[i]) / 16;
      tmp[2*i+0] = xmap[b];
      tmp[2*i+1] = xmap[a];
    }
    return std::string(tmp, tmp+8);
  }

  /// convert from hex-encoded string
  bool str(const std::string & w) {
    const char *s = w.c_str();
    char *tail;
    uint x = genua_strtoul(s, &tail, 16);
    if (tail == s)
      return false;
    col[0] = uint8_t( (x >> 24) & 0xff );
    col[1] = uint8_t( (x >> 16) & 0xff );
    col[2] = uint8_t( (x >> 8) & 0xff );
    col[3] = uint8_t( x & 0xff );
    return true;
  }

  /// create color from HSV
  static Color hsvColor(int hue, int sat, int val) {
    Color c;
    c.hsv2rgb(hue, sat, val);
    return c;
  }

  /// create color from IGES color number
  static Color igesColor(uint k);

  /// generate a new color with random hue
  static Color random(uint sat, uint val);

  /// generate a sequence color
  static Color sequence(uint sat, uint val, uint idx);

  /// return a desaturated version of c
  static Color desaturate(const Color &c, float f);

private:

  /// store 4 bytes (RGBA) for best alignment
  uint8_t col[4];
};

inline Color operator* (const Color &c, float f)
{
  Color a(c);
  a.scaleRgb(f);
  return a;
}

inline Color operator* (float f, const Color &c)
{
  Color a(c);
  a.scaleRgb(f);
  return a;
}

inline std::ostream & operator<< (std::ostream &os, const Color &c)
{
  os << '(' << c.red() << ',' << c.green() << ',' << c.blue()
     << ',' << (uint) c.alpha() << ')';
  return os;
}

#endif // COLOR_H
