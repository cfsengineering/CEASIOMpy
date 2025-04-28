
#
# qmake project file for boost components needed by libgenua/libsurf etc.
#

TEMPLATE     = lib
TARGET       = boost_components
CONFIG      += staticlib thread no-tbb
CONFIG      -= qt
INCLUDEPATH += . $$PWD/.libs/boost/libs/math/src/tr1

# add boost_math_sf when TR1 special functions are required
CONFIG      += boost_thread boost_regex
DEFINES     += _REENTRANT

include(../config/rootconfig.pri)
DESTDIR      = $$TARGET_LIB_DIR
CONFIG(debug, debug|release):TARGET = $$join(TARGET,,,_debug)

win32-msvc2005|win32-msvc2008|win32-msvc2010|win32-msvc2012 {

    # No standard math available in MSVC before VS2013
    CONFIG += boost_math
}

# atomic, system, random, chrono, timer, exception,
# filesystem, program_options, serialization

SOURCES  += libs/atomic/src/lockpool.cpp \
libs/container/src/dlmalloc.cpp \
libs/container/src/global_resource.cpp \
libs/container/src/monotonic_buffer_resource.cpp \
libs/container/src/pool_resource.cpp \
libs/container/src/synchronized_pool_resource.cpp \
libs/container/src/unsynchronized_pool_resource.cpp \
libs/date_time/src/gregorian/date_generators.cpp \
libs/date_time/src/gregorian/greg_month.cpp \
libs/date_time/src/gregorian/greg_weekday.cpp \
libs/exception/src/clone_current_exception_non_intrusive.cpp \
libs/libsystem/src/error_code.cpp \
libs/filesystem/src/codecvt_error_category.cpp \
libs/filesystem/src/operations.cpp \
libs/filesystem/src/path.cpp \
libs/filesystem/src/path_traits.cpp \
libs/filesystem/src/portability.cpp \
libs/filesystem/src/unique_path.cpp \
libs/filesystem/src/unique_path.cpp \
libs/filesystem/src/filesystem_utf8_codecvt_facet.cpp \
libs/chrono/src/chrono.cpp \
libs/chrono/src/process_cpu_clocks.cpp \
libs/chrono/src/thread_clock.cpp \
libs/program_options/src/cmdline.cpp \
libs/program_options/src/config_file.cpp \
libs/program_options/src/convert.cpp \
libs/program_options/src/options_description.cpp \
libs/program_options/src/parsers.cpp \
libs/program_options/src/positional_options.cpp \
libs/program_options/src/split.cpp \
libs/program_options/src/value_semantic.cpp \
libs/program_options/src/variables_map.cpp \
libs/program_options/src/progopt_utf8_codecvt_facet.cpp

win32 {
  SOURCES += libs/filesystem/src/windows_file_codecvt.cpp \
             libs/program_options/src/winmain.cpp
}

# boost thread

boost_thread { 

   DEFINES += BOOST_THREAD_PROVIDES_FUTURE
   DEFINES += BOOST_THREAD_VERSION=4

   SOURCES +=  \
              libs/thread/src/future.cpp

  unix | macx {
    SOURCES +=  libs/thread/src/pthread/once.cpp \
                libs/thread/src/pthread/once_atomic.cpp \
                libs/thread/src/pthread/thread.cpp
  }

  win32 {
    DEFINES += BOOST_THREAD_BUILD_LIB
    SOURCES +=  libs/thread/src/tss_null.cpp \
                libs/thread/src/win32/thread.cpp \
                libs/thread/src/win32/tss_dll.cpp \
                libs/thread/src/win32/tss_pe.cpp \
  }
}

boost_regex {
  SOURCES += libs/regex/src/c_regex_traits.cpp \
libs/regex/src/cpp_regex_traits.cpp \
libs/regex/src/cregex.cpp \
libs/regex/src/fileiter.cpp \
# libs/regex/src/icu.cpp \
libs/regex/src/instances.cpp \
libs/regex/src/posix_api.cpp \
libs/regex/src/regex.cpp \
libs/regex/src/regex_raw_buffer.cpp \
libs/regex/src/regex_traits_defaults.cpp \
libs/regex/src/static_mutex.cpp \
libs/regex/src/wc_regex_traits.cpp \
libs/regex/src/wide_posix_api.cpp \
libs/regex/src/winstances.cpp

win32 {
  SOURCES +=  libs/regex/src/usinstances.cpp \
              libs/regex/src/w32_regex_traits.cpp
}

}

boost_math {
  SOURCES += libs/math/src/tr1/acosh.cpp \
libs/math/src/tr1/acoshf.cpp \
libs/math/src/tr1/acoshl.cpp \
libs/math/src/tr1/asinh.cpp \
libs/math/src/tr1/asinhf.cpp \
libs/math/src/tr1/asinhl.cpp \
libs/math/src/tr1/atanh.cpp \
libs/math/src/tr1/atanhf.cpp \
libs/math/src/tr1/atanhl.cpp \
libs/math/src/tr1/beta.cpp \
libs/math/src/tr1/betaf.cpp \
libs/math/src/tr1/betal.cpp \
libs/math/src/tr1/cbrt.cpp \
libs/math/src/tr1/cbrtf.cpp \
libs/math/src/tr1/cbrtl.cpp \
libs/math/src/tr1/copysign.cpp \
libs/math/src/tr1/copysignf.cpp \
libs/math/src/tr1/copysignl.cpp \
libs/math/src/tr1/expint.cpp \
libs/math/src/tr1/expintf.cpp \
libs/math/src/tr1/expintl.cpp \
libs/math/src/tr1/expm1.cpp \
libs/math/src/tr1/expm1f.cpp \
libs/math/src/tr1/expm1l.cpp \
libs/math/src/tr1/fmax.cpp \
libs/math/src/tr1/fmaxf.cpp \
libs/math/src/tr1/fmaxl.cpp \
libs/math/src/tr1/fmin.cpp \
libs/math/src/tr1/fminf.cpp \
libs/math/src/tr1/fminl.cpp \
libs/math/src/tr1/fpclassify.cpp \
libs/math/src/tr1/fpclassifyf.cpp \
libs/math/src/tr1/fpclassifyl.cpp \
libs/math/src/tr1/hypot.cpp \
libs/math/src/tr1/hypotf.cpp \
libs/math/src/tr1/hypotl.cpp \
libs/math/src/tr1/llround.cpp \
libs/math/src/tr1/llroundf.cpp \
libs/math/src/tr1/llroundl.cpp \
libs/math/src/tr1/log1p.cpp \
libs/math/src/tr1/log1pf.cpp \
libs/math/src/tr1/log1pl.cpp \
libs/math/src/tr1/lround.cpp \
libs/math/src/tr1/lroundf.cpp \
libs/math/src/tr1/lroundl.cpp \
libs/math/src/tr1/nextafter.cpp \
libs/math/src/tr1/nextafterf.cpp \
libs/math/src/tr1/nextafterl.cpp \
libs/math/src/tr1/nexttoward.cpp \
libs/math/src/tr1/nexttowardf.cpp \
libs/math/src/tr1/nexttowardl.cpp \
libs/math/src/tr1/round.cpp \
libs/math/src/tr1/roundf.cpp \
libs/math/src/tr1/roundl.cpp \
libs/math/src/tr1/trunc.cpp \
libs/math/src/tr1/truncf.cpp \
libs/math/src/tr1/truncl.cpp \
libs/math/src/tr1/erf.cpp \
libs/math/src/tr1/erfc.cpp \
libs/math/src/tr1/erfcf.cpp \
libs/math/src/tr1/erfcl.cpp \
libs/math/src/tr1/erff.cpp \
libs/math/src/tr1/erfl.cpp \
libs/math/src/tr1/tgamma.cpp \
libs/math/src/tr1/tgammaf.cpp \
libs/math/src/tr1/tgammal.cpp \
libs/math/src/tr1/lgamma.cpp \
libs/math/src/tr1/lgammaf.cpp \
libs/math/src/tr1/lgammal.cpp
}

boost_math_sf {
SOURCES += libs/math/src/tr1/assoc_laguerre.cpp \
libs/math/src/tr1/assoc_laguerref.cpp \
libs/math/src/tr1/assoc_laguerrel.cpp \
libs/math/src/tr1/assoc_legendre.cpp \
libs/math/src/tr1/assoc_legendref.cpp \
libs/math/src/tr1/assoc_legendrel.cpp \
libs/math/src/tr1/comp_ellint_1.cpp \
libs/math/src/tr1/comp_ellint_1f.cpp \
libs/math/src/tr1/comp_ellint_1l.cpp \
libs/math/src/tr1/comp_ellint_2.cpp \
libs/math/src/tr1/comp_ellint_2f.cpp \
libs/math/src/tr1/comp_ellint_2l.cpp \
libs/math/src/tr1/comp_ellint_3.cpp \
libs/math/src/tr1/comp_ellint_3f.cpp \
libs/math/src/tr1/comp_ellint_3l.cpp \
libs/math/src/tr1/cyl_bessel_i.cpp \
libs/math/src/tr1/cyl_bessel_if.cpp \
libs/math/src/tr1/cyl_bessel_il.cpp \
libs/math/src/tr1/cyl_bessel_j.cpp \
libs/math/src/tr1/cyl_bessel_jf.cpp \
libs/math/src/tr1/cyl_bessel_jl.cpp \
libs/math/src/tr1/cyl_bessel_k.cpp \
libs/math/src/tr1/cyl_bessel_kf.cpp \
libs/math/src/tr1/cyl_bessel_kl.cpp \
libs/math/src/tr1/cyl_neumann.cpp \
libs/math/src/tr1/cyl_neumannf.cpp \
libs/math/src/tr1/cyl_neumannl.cpp \
libs/math/src/tr1/ellint_1.cpp \
libs/math/src/tr1/ellint_1f.cpp \
libs/math/src/tr1/ellint_1l.cpp \
libs/math/src/tr1/ellint_2.cpp \
libs/math/src/tr1/ellint_2f.cpp \
libs/math/src/tr1/ellint_2l.cpp \
libs/math/src/tr1/ellint_3.cpp \
libs/math/src/tr1/ellint_3f.cpp \
libs/math/src/tr1/ellint_3l.cpp \
libs/math/src/tr1/hermite.cpp \
libs/math/src/tr1/hermitef.cpp \
libs/math/src/tr1/hermitel.cpp \
libs/math/src/tr1/laguerre.cpp \
libs/math/src/tr1/laguerref.cpp \
libs/math/src/tr1/laguerrel.cpp \
libs/math/src/tr1/legendre.cpp \
libs/math/src/tr1/legendref.cpp \
libs/math/src/tr1/legendrel.cpp \
libs/math/src/tr1/riemann_zeta.cpp \
libs/math/src/tr1/riemann_zetaf.cpp \
libs/math/src/tr1/riemann_zetal.cpp \
libs/math/src/tr1/sph_bessel.cpp \
libs/math/src/tr1/sph_besself.cpp \
libs/math/src/tr1/sph_bessell.cpp \
libs/math/src/tr1/sph_legendre.cpp \
libs/math/src/tr1/sph_legendref.cpp \
libs/math/src/tr1/sph_legendrel.cpp \
libs/math/src/tr1/sph_neumann.cpp \
libs/math/src/tr1/sph_neumannf.cpp \
libs/math/src/tr1/sph_neumannl.cpp
}

boost_sp_debug {
  DEFINES += BOOST_SP_ENABLE_DEBUG_HOOKS
  SOURCES +=  libs/smart_ptr/src/sp_collector.cpp \
              libs/smart_ptr/src/sp_debug_hooks.cpp
}
