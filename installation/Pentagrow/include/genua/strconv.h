
// string-to-float conversion functions
// which do not call strlen() as the win32 versions do

#ifndef SANOS_STRCONV_H
#define SANOS_STRCONV_H

#ifdef __cplusplus
extern "C" {
#endif

// strtod.c
double sanos_atof(const char *str);
double sanos_strtod(const char *str, char **endptr);

#ifdef __cplusplus
}
#endif

#endif
