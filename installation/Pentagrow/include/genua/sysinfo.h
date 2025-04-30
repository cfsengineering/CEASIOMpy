
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
 
#ifndef GENUA_SYSINFO_H
#define GENUA_SYSINFO_H

#include <string>
#include "defines.h"

/** System information.
  */
class SysInfo
{
public:

  /// ISA extensions
  enum SimdIsa { IsaUnknown = 0,
                 IsaGeneric = 1,
                 IsaSSE1    = 3,
                 IsaSSE2    = 7,
                 IsaSSE3    = 15,
                 IsaSSE41   = 31,
                 IsaSSE42   = 63,
                 IsaAVX1    = 127,
                 IsaAVX2    = 255,
                 IsaAVX512  = 511};

  /// OSX version tags
  enum OsxVersion { OSX_1060  = (10 << 16) | (6 << 8),
                    OSX_1070  = (10 << 16) | (7 << 8),
                    OSX_1080  = (10 << 16) | (8 << 8),
                    OSX_1090  = (10 << 16) | (9 << 8),
                    OSX_10100 = (10 << 16) | (10 << 8),
                    OSX_10110 = (10 << 16) | (11 << 8),
                    OSX_10120 = (10 << 16) | (12 << 8),};

  /// windows version tags
  enum WindowsVersion { WinXp = (5 << 16) | (1 << 8),         // 32bit
                        WinServer2003 = (5 << 16) | (2 << 8), // XP 64bit
                        WinVista = (6 << 16),
                        Win7 = (6 << 16) | (1 << 8),
                        Win8 = (6 << 16) | (2 << 8),
                        WinServer2012 = (6 << 16) | (3 << 8),  // and 8.1
                        Win10 = (10 << 16),
                      };

  /// initialize, check processor support
  static void init();

#ifdef GENUA_POSIX    

  /// read environment variable (empty if variable does not exist)
  static std::string getEnv(const std::string & name);

  /// set environment variable
  static void setEnv(const std::string & name, const std::string & value,
                     bool replace=true);

#endif

  /// return current user name
  static std::string username();

  /// return host name
  static std::string hostname();

  /// treat denormal floating point numbers as zeros
  static void denormalsAreZero(bool daz=true, bool ftz=true);

  /// physical memory present in system (in megabyte)
  static int physMemory();

  /// memory available (free, in megabyte)
  static int availMemory();

  /// number of processors online
  static uint nproc();

  /// number of threads to use (application configured)
  static uint nthread();

  /// configure number of simultaneous threads
  static void nthread(uint n);

  /// retrieve date and time
  static void localTime(int & year, int & month, int & day,
                        int & hour, int & minu, int & sec);

  /// test whether ISA extension is supported
  static bool supported(SimdIsa isa) {
    return (((s_supported_isa & s_mask_isa) & isa) == uint(isa));
  }

  /// assemble string containing the highest supported SIMD ISA
  static std::string isaName();

  /// dynamically change the reported ISA support by applying a mask
  static void maskIsa(uint mask) {s_mask_isa = mask;}

  /// switch back to reporting detected ISA
  static void unmaskIsa() {s_mask_isa = 0xffffffff;}

  /// operating system version triple (major << 16 | minor << 8 | patch)
  static uint osversion();

  /// kill process by PID, if possible
  static bool killProcess(uint64_t pid);

  /// retrieve OS's last error message, if any
  static std::string lastError();

private:

  /// number of threads used by application
  static uint s_nthr;

  /// isa extension found during initialization
  static uint s_supported_isa;

  /// user-specified mask for the highest ISA which is to be used dynamically
  static uint s_mask_isa;
};

#endif

