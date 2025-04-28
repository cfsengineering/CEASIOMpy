/* This code is in the Public Domain. */

#ifndef GENUA_FLOATCOMPRESSOR_H
#define GENUA_FLOATCOMPRESSOR_H

#include <cstdint>

/** Encodes 32bit floats to 16bit, with loss of range and precision.
 *
 * The IEEE-754 half-float format has a 5bit exponent and 11 bit significand.
 * Relative accuracy is about 1e-3; the maximum representable value is 65504.
 *
 * Only use this format instead of linearized quantization if logarithmic
 * resolution is needed, that is, the relative error of represented values
 * should remain constant for all values. Fixed-point representation is better
 * if the absolute error is of interest.
 *
 * \ingroup numerics, io
 */
class FloatCompressor
{
public:

  static uint16_t compress(float value)
  {
    Bits v, s;
    v.f = value;
    uint32_t sign = v.si & s_signN;
    v.si ^= sign;
    sign >>= s_shiftSign; // logical shift
    s.si = s_mulN;
    s.si = s.f * v.f; // correct subnormals
    v.si ^= (s.si ^ v.si) & -(s_minN > v.si);
    v.si ^= (s_infN ^ v.si) & -((s_infN > v.si) & (v.si > s_maxN));
    v.si ^= (s_nanN ^ v.si) & -((s_nanN > v.si) & (v.si > s_infN));
    v.ui >>= s_shift; // logical shift
    v.si ^= ((v.si - s_maxD) ^ v.si) & -(v.si > s_maxC);
    v.si ^= ((v.si - s_minD) ^ v.si) & -(v.si > s_subC);
    return v.ui | sign;
  }

  static float decompress(uint16_t value)
  {
    Bits v;
    v.ui = value;
    int32_t sign = v.si & s_signC;
    v.si ^= sign;
    sign <<= s_shiftSign;
    v.si ^= ((v.si + s_minD) ^ v.si) & -(v.si > s_subC);
    v.si ^= ((v.si + s_maxD) ^ v.si) & -(v.si > s_maxC);
    Bits s;
    s.si = s_mulC;
    s.f *= v.si;
    int32_t mask = -(s_norC > v.si);
    v.si <<= s_shift;
    v.si ^= (s.si ^ v.si) & mask;
    v.si |= sign;
    return v.f;
  }

private:

  union Bits
  {
    float f;
    int32_t si;
    uint32_t ui;
  };

  static int const s_shift = 13;
  static int const s_shiftSign = 16;

  static int32_t const s_infN = 0x7F800000; // flt32 infinity
  static int32_t const s_maxN = 0x477FE000; // max flt16 normal as a flt32
  static int32_t const s_minN = 0x38800000; // min flt16 normal as a flt32
  static int32_t const s_signN = 0x80000000; // flt32 sign bit

  static int32_t const s_infC = s_infN >> s_shift;
  static int32_t const s_nanN = (s_infC + 1) << s_shift; // minimum flt16 nan as a flt32
  static int32_t const s_maxC = s_maxN >> s_shift;
  static int32_t const s_minC = s_minN >> s_shift;
  static int32_t const s_signC = s_signN >> s_shiftSign; // flt16 sign bit

  static int32_t const s_mulN = 0x52000000; // (1 << 23) / minN
  static int32_t const s_mulC = 0x33800000; // minN / (1 << (23 - shift))

  static int32_t const s_subC = 0x003FF; // max flt32 subnormal down shifted
  static int32_t const s_norC = 0x00400; // min flt32 normal down shifted

  static int32_t const s_maxD = s_infC - s_maxC - 1;
  static int32_t const s_minD = s_minC - s_subC - 1;
};

#endif // FLOATCOMPRESSOR_H

