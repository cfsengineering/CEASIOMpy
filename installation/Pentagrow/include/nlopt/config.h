/* config.h.  Generated from config.h.in by configure.  */
/* config.h.in.  Generated from configure.ac by autoheader.  */

/* Bugfix version number. */
#define BUGFIX_VERSION 2

/* Define to enable extra debugging code. */
/* #undef DEBUG */

/* Define to 1 if you have the `BSDgettimeofday' function. */
/* #undef HAVE_BSDGETTIMEOFDAY */

/* Define to the sub-directory in which libtool stores uninstalled libraries.
   */
#define LT_OBJDIR ".libs/"

/* Major version number. */
#define MAJOR_VERSION 2

/* Minor version number. */
#define MINOR_VERSION 4

/* Name of package */
#define PACKAGE "nlopt"

/* Define to the address where bug reports for this package should be sent. */
#define PACKAGE_BUGREPORT "stevenj@alum.mit.edu"

/* Define to the full name of this package. */
#define PACKAGE_NAME "nlopt"

/* Define to the full name and version of this package. */
#define PACKAGE_STRING "nlopt 2.4.2"

/* Define to the one symbol short name of this package. */
#define PACKAGE_TARNAME "nlopt"

/* Define to the home page for this package. */
#define PACKAGE_URL ""

/* Define to the version of this package. */
#define PACKAGE_VERSION "2.4.2"

/* replacement for broken HUGE_VAL macro, if needed */
/* #undef REPLACEMENT_HUGE_VAL */

/* The size of `unsigned int', as computed by sizeof. */
#define SIZEOF_UNSIGNED_INT 4

/* The size of `unsigned long', as computed by sizeof. */
#define SIZEOF_UNSIGNED_LONG 8

/* Define to 1 if you have the ANSI C header files. */
#define STDC_HEADERS 1

/* Version number of package */
#define VERSION "2.4.2"

/* Define if compiled including C++-based routines */
#define WITH_CXX 1

/* Define to empty if `const' does not conform to ANSI C. */
/* #undef const */

/* Platform-specific  */
#ifdef __APPLE__

/* Define to C thread-local keyword, or to nothing if this is not supported in
   your compiler. */
#define THREADLOCAL __thread

/* Define if the copysign function/macro is available. */
#define HAVE_COPYSIGN 1

/* Define to 1 if you have the <dlfcn.h> header file. */
#define HAVE_DLFCN_H 1

/* Define to 1 if you have the <getopt.h> header file. */
#define HAVE_GETOPT_H 1

/* Define to 1 if you have the `getpid' function. */
#define HAVE_GETPID 1

/* Define if syscall(SYS_gettid) available. */
#define HAVE_GETTID_SYSCALL 1

/* Define to 1 if you have the `gettimeofday' function. */
#define HAVE_GETTIMEOFDAY 1

/* Define to 1 if you have the <inttypes.h> header file. */
#define HAVE_INTTYPES_H 1

/* Define if the isinf() function/macro is available. */
#define HAVE_ISINF 1

/* Define if the isnan() function/macro is available. */
#define HAVE_ISNAN 1

/* Define to 1 if you have the `m' library (-lm). */
#define HAVE_LIBM 1

/* Define to 1 if you have the <memory.h> header file. */
#define HAVE_MEMORY_H 1

/* Define to 1 if you have the `qsort_r' function. */
#define HAVE_QSORT_R 1

/* Define to 1 if you have the <stdint.h> header file. */
#define HAVE_STDINT_H 1

/* Define to 1 if you have the <stdlib.h> header file. */
#define HAVE_STDLIB_H 1

/* Define to 1 if you have the <strings.h> header file. */
#define HAVE_STRINGS_H 1

/* Define to 1 if you have the <string.h> header file. */
#define HAVE_STRING_H 1

/* Define to 1 if you have the <sys/stat.h> header file. */
#define HAVE_SYS_STAT_H 1

/* Define to 1 if you have the <sys/types.h> header file. */
#define HAVE_SYS_TYPES_H 1

/* Define to 1 if you have the `time' function. */
#define HAVE_TIME 1

/* Define to 1 if the system has the type `uint32_t'. */
#define HAVE_UINT32_T 1

/* Define to 1 if you have the <unistd.h> header file. */
#define HAVE_UNISTD_H 1



#elif __linux__


/* Define to C thread-local keyword, or to nothing if this is not supported in
   your compiler. */
#define THREADLOCAL __thread

/* Define if the copysign function/macro is available. */
#define HAVE_COPYSIGN 1

/* Define to 1 if you have the <dlfcn.h> header file. */
#define HAVE_DLFCN_H 1

/* Define to 1 if you have the <getopt.h> header file. */
#define HAVE_GETOPT_H 1

/* Define to 1 if you have the `getpid' function. */
#define HAVE_GETPID 1

/* Define if syscall(SYS_gettid) available. */
#define HAVE_GETTID_SYSCALL 1

/* Define to 1 if you have the `gettimeofday' function. */
#define HAVE_GETTIMEOFDAY 1

/* Define to 1 if you have the <inttypes.h> header file. */
#define HAVE_INTTYPES_H 1

/* Define if the isinf() function/macro is available. */
#define HAVE_ISINF 1

/* Define if the isnan() function/macro is available. */
#define HAVE_ISNAN 1

/* Define to 1 if you have the `m' library (-lm). */
#define HAVE_LIBM 1

/* Define to 1 if you have the <memory.h> header file. */
#define HAVE_MEMORY_H 1

/* Define to 1 if you have the `qsort_r' function. */
#define HAVE_QSORT_R 1

/* Define to 1 if you have the <stdint.h> header file. */
#define HAVE_STDINT_H 1

/* Define to 1 if you have the <stdlib.h> header file. */
#define HAVE_STDLIB_H 1

/* Define to 1 if you have the <strings.h> header file. */
#define HAVE_STRINGS_H 1

/* Define to 1 if you have the <string.h> header file. */
#define HAVE_STRING_H 1

/* Define to 1 if you have the <sys/stat.h> header file. */
#define HAVE_SYS_STAT_H 1

/* Define to 1 if you have the <sys/types.h> header file. */
#define HAVE_SYS_TYPES_H 1

/* Define to 1 if you have the `time' function. */
#define HAVE_TIME 1

/* Define to 1 if the system has the type `uint32_t'. */
#define HAVE_UINT32_T 1

/* Define to 1 if you have the <unistd.h> header file. */
#define HAVE_UNISTD_H 1



#elif _WIN32


/* Define to 1 if you have the <sys/stat.h> header file. */
#define HAVE_SYS_STAT_H 0

/* Define to 1 if you have the <sys/types.h> header file. */
#define HAVE_SYS_TYPES_H 0

/* Define to 1 if you have the `time' function. */
#define HAVE_TIME 0

/* Define to 1 if you have the <unistd.h> header file. */
#define HAVE_UNISTD_H 0

/* Define to 1 if you can safely include both <sys/time.h> and <time.h>. */
#define TIME_WITH_SYS_TIME 0


#define THREADLOCAL __declspec( thread )

#endif /* platform-specific */



/* Define to `__inline__' or `__inline' if that's what the C compiler
   calls it, or to nothing if 'inline' is not supported under any name.  */
#ifndef __cplusplus
/* #undef inline */
#endif
