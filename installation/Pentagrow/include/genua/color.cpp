
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
 
#include "color.h"
#include "rng.h"
#include "bitfiddle.h"

void Color::colorLimits(int nval, const float values[], float spread,
                        float &vblue, float &vred)
{
  float vmin = std::numeric_limits<float>::max();
  float vmax = -vmin;
  float vmean = 0.0f;
  for (int i=0; i<nval; ++i) {
    vmin = std::min( vmin, values[i] );
    vmax = std::max( vmax, values[i] );
    vmean += values[i];
  }
  vmean /= float(nval);

  float t = 1.0f - sq(spread);
  vblue = (1.0f - t)*vmin + t*vmean;
  vred = (1.0f - t)*vmax + t*vmean;
}

Color Color::igesColor(uint k)
{
  switch (k) {
  case 0:
  case 1:
    return Color(0.0f, 0.0f, 0.0f); // black
  case 2:
    return Color(1.0f, 0.0f, 0.0f); // red
  case 3:
    return Color(0.0f, 1.0f, 0.0f); // green
  case 4:
    return Color(0.0f, 0.0f, 1.0f); // blue
  case 5:
    return Color(1.0f, 1.0f, 0.0f); // yellow
  case 6:
    return Color(1.0f, 0.0f, 1.0f); // magenta
  case 7:
    return Color(0.0f, 1.0f, 1.0f); // cyan
  case 8:
    return Color(1.0f, 1.0f, 1.0f); // white
  }
  return Color();
}

Color Color::random(uint sat, uint val)
{
  // set random color
  IntRng rng(0, 360);
  rng.timeSeed();
  Color c;
  c.hsv2rgb(rng(), sat, val);
  c.alpha( uint8_t(255) );

  return c;
}

Color Color::sequence(uint sat, uint val, uint idx)
{
  Color c;

  uint32_t ri = reverse_bits((uint32_t) idx);
  float r = 0.712f + std::ldexp( float(ri), -32 );
  c.hsv2rgb( int(360*r)%360, sat, val );
  c.alpha( uint8_t(255) );

  return c;
}

Color Color::desaturate(const Color &c, float f)
{
  float grey = 0.3f*c.red() + 0.59f*c.green() + 0.11f*c.blue();
  uint8_t r = (uint8_t) ( f*grey + (1.0f - f)*c.red() );
  uint8_t g = (uint8_t) ( f*grey + (1.0f - f)*c.green() );
  uint8_t b = (uint8_t) ( f*grey + (1.0f - f)*c.blue() );
  return Color(r, g, b, c.alpha());
}
