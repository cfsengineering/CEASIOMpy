
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       hashfunctions.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * hashing functions for hashed containers
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef GENUA_HASHFUNCTIONS_H
#define GENUA_HASHFUNCTIONS_H

#include "defines.h"

#define JENKINS_ROT(x,k) (((x)<<(k)) | ((x)>>(32-(k))))

#define JENKINS_MIX(a,b,c) \
{ \
  a -= c;  a ^= JENKINS_ROT(c, 4);  c += b; \
  b -= a;  b ^= JENKINS_ROT(a, 6);  a += c; \
  c -= b;  c ^= JENKINS_ROT(b, 8);  b += a; \
  a -= c;  a ^= JENKINS_ROT(c,16);  c += b; \
  b -= a;  b ^= JENKINS_ROT(a,19);  a += c; \
  c -= b;  c ^= JENKINS_ROT(b, 4);  b += a; \
}

#define JENKINS_FINAL(a,b,c) \
{ \
  c ^= b; c -= JENKINS_ROT(b,14); \
  a ^= c; a -= JENKINS_ROT(c,11); \
  b ^= a; b -= JENKINS_ROT(a,25); \
  c ^= b; c -= JENKINS_ROT(b,16); \
  a ^= c; a -= JENKINS_ROT(c,4);  \
  b ^= a; b -= JENKINS_ROT(a,14); \
  c ^= b; c -= JENKINS_ROT(b,24); \
}

#define JENKINS_MIX64(a,b,c) \
{ \
  a -= b; a -= c; a ^= (c>>43); \
  b -= c; b -= a; b ^= (a<<9); \
  c -= a; c -= b; c ^= (b>>8); \
  a -= b; a -= c; a ^= (c>>38); \
  b -= c; b -= a; b ^= (a<<23); \
  c -= a; c -= b; c ^= (b>>5); \
  a -= b; a -= c; a ^= (c>>35); \
  b -= c; b -= a; b ^= (a<<49); \
  c -= a; c -= b; c ^= (b>>11); \
  a -= b; a -= c; a ^= (c>>12); \
  b -= c; b -= a; b ^= (a<<18); \
  c -= a; c -= b; c ^= (b>>22); \
}

/** Array version of Robert Jenkins' hash function 
    http://burtleburtle.net/bob/c/lookup3.c */
inline uint32_t jenkins_hash(const uint32_t *k, uint32_t length, 
                             uint32_t initval = 0xf98e143d)
{
  uint32_t a,b,c;
  a = b = c = 0xdeadbeef + (((uint32_t)length)<<2) + initval;
  while (length > 3) {
    a += k[0];
    b += k[1];
    c += k[2];
    JENKINS_MIX(a,b,c);
    length -= 3;
    k += 3;
  }

  switch(length) { 
    case 3: 
      c += k[2];
    case 2: 
      b += k[1];
    case 1: 
      a += k[0];
      JENKINS_FINAL(a,b,c);
    case 0:     
      break;
  }
  return c;
}

/** Array version of Robert Jenkins' hash function 
    http://burtleburtle.net/bob/c/lookup8.c */
inline uint64_t jenkins_hash(const uint64_t *k, uint64_t length,
                             uint64_t level = UINT64_LITERAL(0x9e3f98e143da7c13))
{
  uint64_t a,b,c,len(length);
  a = b = level;
  c = UINT64_LITERAL(0x9e3779b97f4a7c13); 
  
  while (len >= 3) {
    a += k[0];
    b += k[1];
    c += k[2];
    JENKINS_MIX64(a,b,c);
    k += 3; 
    len -= 3;
  }
  
  c += (length<<3);
  switch(len) {
    case 2: 
      b += k[1];
    case 1: 
      a += k[0];
  }
  
  JENKINS_MIX64(a,b,c);
  return c;
}

/** Three-integer version of Robert Jenkins' hashing function */
inline uint32_t jenkins_hash(uint32_t a, uint32_t b, uint32_t c)
{
  JENKINS_MIX(a, b, c);
  JENKINS_FINAL(a, b, c);
  return c;
}

/** Four-integer version of Robert Jenkins' hashing function */
inline uint32_t jenkins_hash(uint32_t a, uint32_t b, uint32_t c, uint32_t d)
{
  JENKINS_MIX(a, b, c);
  a += d;
  JENKINS_FINAL(a, b, c);
  return c;
}

/** Three-integer version of Robert Jenkins' hashing function */
inline uint64_t jenkins_hash(uint64_t a, uint64_t b, uint64_t c)
{
  JENKINS_MIX64(a, b, c);
  return c;
}

/** Four-integer version of Robert Jenkins' hashing function */
inline uint64_t jenkins_hash(uint64_t a, uint64_t b, uint64_t c, uint64_t d)
{
  JENKINS_MIX64(a,b,c);
  a += d;
  JENKINS_MIX64(a,b,c);
  return c;
}

inline uint32_t jenkins_hash(uint32_t a)
{
   a = (a + 0x7ed55d16) + (a<<12);
   a = (a ^ 0xc761c23c) ^ (a>>19);
   a = (a + 0x165667b1) + (a<<5);
   a = (a + 0xd3a2646c) ^ (a<<9);
   a = (a + 0xfd7046c5) + (a<<3);
   a = (a ^ 0xb55a4f09) ^ (a>>16);
   return a;
}

inline uint64_t wang_hash(uint64_t key)
{
  key = (~key) + (key << 21);
  key = key ^ (key >> 24);
  key = (key + (key << 3)) + (key << 8); 
  key = key ^ (key >> 14);
  key = (key + (key << 2)) + (key << 4);
  key = key ^ (key >> 28);
  key = key + (key << 31);
  return key;
}

#define HSIEH_GET16BITS(d) ((((uint32_t)(((const uint8_t *)(d))[1])) << 8) \
                              +(uint32_t)(((const uint8_t *)(d))[0]) )

/** Paul Hsieh's hash function 
    http://www.azillionmonkeys.com/qed/hash.html */ 
inline uint32_t hsieh_hash(const char * data, int len) 
{
  uint32_t hash(len), tmp;
  int rem;

  if (len <= 0 or data == 0) 
    return 0;

  rem = len & 3;
  len >>= 2;

  for (;len > 0; len--) {
      hash  += HSIEH_GET16BITS(data);
      tmp    = (HSIEH_GET16BITS(data+2) << 11) ^ hash;
      hash   = (hash << 16) ^ tmp;
      data  += 2*sizeof (uint16_t);
      hash  += hash >> 11;
  }

  switch (rem) {
    case 3: 
      hash += HSIEH_GET16BITS (data);
      hash ^= hash << 16;
      hash ^= data[sizeof (uint16_t)] << 18;
      hash += hash >> 11;
      break;
    case 2: 
      hash += HSIEH_GET16BITS (data);
      hash ^= hash << 11;
      hash += hash >> 17;
      break;
    case 1: 
      hash += *data;
      hash ^= hash << 10;
      hash += hash >> 1;
  }
  
  hash ^= hash << 3;
  hash += hash >> 5;
  hash ^= hash << 4;
  hash += hash >> 17;
  hash ^= hash << 25;
  hash += hash >> 6;

  return hash;
}

// manual overloads because apple gcc doesn't get this right
#if defined(GENUA_MACOSX)
  #if defined(GENUA_64BIT)
  inline size_t jenkins_hash(size_t a, size_t b, size_t c) 
  {
    return jenkins_hash((uint64_t) a, (uint64_t) b, (uint64_t) c);
  }
  inline size_t jenkins_hash(size_t a, size_t b, size_t c, size_t d) 
  {
    return jenkins_hash((uint64_t) a, (uint64_t) b, (uint64_t) c, (uint64_t) d);
  }
  #else
  inline size_t jenkins_hash(size_t a, size_t b, size_t c) 
  {
    return jenkins_hash((uint32_t) a, (uint32_t) b, (uint32_t) c);
  }
  inline size_t jenkins_hash(size_t a, size_t b, size_t c, size_t d) 
  {
    return jenkins_hash((uint32_t) a, (uint32_t) b, (uint32_t) c, (uint32_t) d);
  }
  #endif
#endif

#endif
