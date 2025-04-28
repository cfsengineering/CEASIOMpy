
#ifndef _EXPAT_CONFIG_INCLUDED
#define _EXPAT_CONFIG_INCLUDED

#if defined(COMPILED_FROM_DSP) || defined(_WIN32)
#include "winconfig.h"
#elif defined(MACOS_CLASSIC)
#include "macconfig.h"
#elif defined(__amigaos4__)
#include "amigaconfig.h"
#elif defined(__WATCOMC__)
#include "watcomconfig.h"
#else
#include <unixconfig.h>
#endif

#endif
