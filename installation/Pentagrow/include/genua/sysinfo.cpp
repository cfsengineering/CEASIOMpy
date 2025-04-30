
/* Copyright (C) 2016 David Eller <david@larosterna.com>
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

#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <iostream>
#include <ctime>
#include "defines.h"
//#include "macaddress.h"
#include "sysinfo.h"
#include "sse.h"
#include "programversion.h"

#include <cstdio>
#include <cstring>

#if defined(GENUA_POSIX)
#include <unistd.h>
#include <signal.h>
#endif

#if defined(GENUA_LINUX)
#include <errno.h>
#endif

#if defined(GENUA_MACOSX)
#include <sys/sysctl.h>
#include <sys/utsname.h>
#include <sys/errno.h>
#endif

#if defined(GENUA_WIN32)
#include <Windows.h>

// doesn't work as documented
//#include <ntverp.h>
//#if VER_PRODUCTBUILD >= 9600
//#include <VersionHelpers.h>
//#endif
#endif

using namespace std;

uint SysInfo::s_nthr( SysInfo::nproc() );
uint SysInfo::s_supported_isa( SysInfo::IsaUnknown );
uint SysInfo::s_mask_isa( 0xffffffff );

void SysInfo::denormalsAreZero(bool daz, bool ftz)
{
#ifdef ARCH_SSE
  unsigned int mxcsr = _mm_getcsr();
  if (ftz)
    mxcsr |= (1<<15) | (1<<11);
  if (daz)
    mxcsr |= (1<<6);
  _mm_setcsr(mxcsr);
#endif
}

#ifdef GENUA_POSIX

std::string SysInfo::username()
{
  string lgname = SysInfo::getEnv("LOGNAME");
  if (lgname.empty())
    return std::string( ::getlogin() );
  else
    return lgname;
}

std::string SysInfo::hostname()
{
  const size_t len = 256;
  char buffer[len];
  memset(buffer, 0, sizeof(buffer));
  if ( ::gethostname(buffer, len) == 0 )
    return std::string(buffer);
  else
    return std::string();
}

int SysInfo::physMemory() 
{
#if defined(GENUA_MACOSX)

  int mib[2];
  uint64_t memsize;
  size_t len;

  mib[0] = CTL_HW;
  mib[1] = HW_MEMSIZE; /*uint64_t: physical ram size */
  len = sizeof(memsize);
  sysctl(mib, 2, &memsize, &len, NULL, 0);
  return memsize/(1024*1024);
#else
  // pagesize in kB
  long int ps = sysconf(_SC_PAGESIZE) / 1024;
  // pages of physical memory
  long int pp = sysconf(_SC_PHYS_PAGES);
  return ps*pp/1024;
#endif
}

int SysInfo::availMemory() 
{
#if defined(GENUA_MACOSX)	
  int mib[2];
  uint64_t memsize;
  size_t len;

  mib[0] = CTL_HW;
  mib[1] = HW_USERMEM; /* RAM available to user */
  len = sizeof(memsize);
  sysctl(mib, 2, &memsize, &len, NULL, 0);
  return memsize/1024;
#else 
  // pagesize in kB
  long int ps = sysconf(_SC_PAGESIZE) / 1024;
  // pages of memory available
  long int pp = sysconf(_SC_AVPHYS_PAGES);
  return ps*pp/1024;
#endif
}

string SysInfo::getEnv(const string & name)
{
  // read environment variable
  char *val = getenv(name.c_str());
  string s;
  if (val == 0)
    s = "";
  else
    s = string(val);
  return s;
}

void SysInfo::setEnv(const string & name, const string & value, bool replace)
{
  // set environment variable
  if (replace)
    setenv(name.c_str(), value.c_str(), 1);
  else
    setenv(name.c_str(), value.c_str(), 0);
}

uint SysInfo::nproc() 
{
  return sysconf(_SC_NPROCESSORS_ONLN);
}

#elif defined(GENUA_WIN32)

uint SysInfo::nproc() 
{
  uint np(1);
  SYSTEM_INFO sinfo;
  GetSystemInfo(&sinfo);
  np = sinfo.dwNumberOfProcessors;
  return np;
}

int SysInfo::physMemory() 
{
  MEMORYSTATUS mstat;
  mstat.dwLength = sizeof(mstat);
  GlobalMemoryStatus(&mstat);
  return int(mstat.dwTotalPhys / 1048576);
}

int SysInfo::availMemory() 
{
  MEMORYSTATUS mstat;
  mstat.dwLength = sizeof(mstat);
  GlobalMemoryStatus(&mstat);
  return int(mstat.dwAvailPhys / 1048576);
}

static string lptstr2str(LPTSTR lpt)
{
#ifdef UNICODE
  std::string un;
  int cch = WideCharToMultiByte(CP_UTF8, 0, lpt, -1, 0, 0, NULL, NULL);
  un.resize(cch);
  WideCharToMultiByte(CP_UTF8, 0, lpt, -1, &un[0], cch, NULL, NULL);
  return un;
#else
  return std::string(lpt);
#endif
}

std::string SysInfo::username()
{
  DWORD len = 255;
  TCHAR buffer[256];
  memset(buffer, 0, sizeof(TCHAR)*256);
  if (GetUserName(buffer, &len))
    return lptstr2str(buffer);
  else
    return string();
}

std::string SysInfo::hostname()
{
  DWORD len = 255;
  TCHAR buffer[256];
  memset(buffer, 0, sizeof(TCHAR)*256);
  if (GetComputerName(buffer, &len))
    return lptstr2str(buffer);
  else
    return string();
}

#endif

uint SysInfo::nthread()
{
  return s_nthr;
}

void SysInfo::nthread(uint n)
{
  s_nthr = n;
}

void SysInfo::localTime(int & year, int & month, int & day, 
                        int & hour, int & minu, int & sec)
{
  time_t tsimple;
  tsimple = time(0);
  const tm *ptm = localtime( &tsimple );
  if (ptm == 0)
    return;

  year = 1900 + ptm->tm_year;
  month = ptm->tm_mon + 1;
  day = ptm->tm_mday;
  hour = ptm->tm_hour;
  minu = ptm->tm_min;
  sec = ptm->tm_sec;
}

//int SysInfo::primaryHardwareAddress(int hwa[6])
//{
//  return primary_mac_address(hwa);
//}

//std::string SysInfo::primaryHardwareAddress()
//{
//  int hwa[6];
//  for (int i=0; i<6; ++i)
//    hwa[i] = 0;
//  int stat = primaryHardwareAddress(hwa);

//  // this does it nicely, but MSVC doesn't support snprintf()
//  // which is std C99.
//  //
//  //    char tmp[] = "00:00:00:00:00:00";
//  //    snprintf(tmp, sizeof(tmp), "%.02x:%02x:%.02x:%02x:%.02x:%02x",
//  //             hwa[0],hwa[1],hwa[2],hwa[3],hwa[4],hwa[5]);

//  char tmp[] = "00:00:00:00:00:00";
//  if (stat == 0) {
//    char *base = tmp;
//    const char xmap[] = "0123456789abcdef";
//    for (int i=0; i<6; ++i) {
//      int a = hwa[i] % 16;
//      int b = hwa[i] / 16;
//      base[0] = xmap[b];
//      base[1] = xmap[a];
//      base += 3;
//    }
//  }

//  return string(tmp);
//}

// ---------------- CPU feature detection ----------------------------

#undef HAVE_CPUID

#ifdef GENUA_WIN32

//  Windows
#define HAVE_CPUID
#define genua_cpuid    __cpuid

#elif defined(GENUA_GCC) || defined(GENUA_CLANG)

#if  ( (__x86_64__ || __i386__) )

#define HAVE_CPUID

#include <cpuid.h>

static void genua_cpuid(int cpuInfo[4], int function_id)
{
  memset(cpuInfo, 0, 4*sizeof(int));

  uint *eax = (uint *) &cpuInfo[0];
  uint *ebx = (uint *) &cpuInfo[1];
  uint *ecx = (uint *) &cpuInfo[2];
  uint *edx = (uint *) &cpuInfo[3];
  __get_cpuid(function_id, eax, ebx, ecx, edx);
}

#else // not x86/x64

#undef HAVE_CPUID

#endif

#endif

// this looks too nice in the documentation, but it crashes on older processors

//#ifdef __INTEL_COMPILER

//void SysInfo::init()
//{
//  const int core_avx2_features = (_FEATURE_AVX2 | _FEATURE_FMA |_FEATURE_BMI |
//                                  _FEATURE_LZCNT | _FEATURE_MOVBE);

//  s_supported_isa = IsaGeneric;
//  if ( _may_i_use_cpu_feature( core_avx2_features ) )
//    s_supported_isa = IsaAVX2;
//  else if ( _may_i_use_cpu_feature( _FEATURE_AVX | _FEATURE_POPCNT ) )
//    s_supported_isa = IsaAVX1;
//  else if ( _may_i_use_cpu_feature( _FEATURE_SSE4_2 | _FEATURE_POPCNT ) )
//    s_supported_isa = IsaSSE42;
//  else if ( _may_i_use_cpu_feature( _FEATURE_SSE4_1 ) )
//    s_supported_isa = IsaSSE41;
//  else if ( _may_i_use_cpu_feature( _FEATURE_SSE3 ) )
//    s_supported_isa = IsaSSE3;
//  else if ( _may_i_use_cpu_feature( _FEATURE_SSE2 ) )
//    s_supported_isa = IsaSSE2;
//  else if ( _may_i_use_cpu_feature( _FEATURE_SSE ) )
//    s_supported_isa = IsaSSE1;
//}

//#elif defined(HAVE_CPUID)

#if defined(GENUA_GCC) && ( (__GNUC__ > 4) || ( (__GNUC__ == 4) && (__GNUC_MINOR__ > 7) ) )

void SysInfo::init()
{
  s_supported_isa = IsaGeneric;
  __builtin_cpu_init();
  if (__builtin_cpu_supports("sse") > 0)
    s_supported_isa |= IsaSSE1;
  if (__builtin_cpu_supports("sse2") > 0)
    s_supported_isa |= IsaSSE2;
  if (__builtin_cpu_supports("sse3") > 0)
    s_supported_isa |= IsaSSE3;
  if (__builtin_cpu_supports("sse4.1") > 0)
    s_supported_isa |= IsaSSE41;
  if (__builtin_cpu_supports("sse4.2") > 0)
    s_supported_isa |= IsaSSE42;
  if (__builtin_cpu_supports("avx") > 0)
    s_supported_isa |= IsaAVX1;
  if (__builtin_cpu_supports("avx2") > 0)
    s_supported_isa |= IsaAVX2;
}

#elif defined(HAVE_CPUID)

void SysInfo::init()
{
  int info[4];
  genua_cpuid(info, 0);
  uint nids = info[0];
  s_supported_isa = IsaGeneric;
  if (nids >= 1) {
    genua_cpuid(info, 0x00000001);
    if ((info[3] & (1 << 25)) != 0)
      s_supported_isa |= IsaSSE1;
    if ((info[3] & (1 << 26)) != 0)
      s_supported_isa |= IsaSSE2;
    if ((info[2] & (1 << 0)) != 0)
      s_supported_isa |= IsaSSE3;
    if ((info[2] & (1 << 19)) != 0)
      s_supported_isa |= IsaSSE41;
    if ((info[2] & (1 << 20)) != 0)
      s_supported_isa |= IsaSSE42;

    const int avx_bits = (1 << 28) | 0x04000000 | 0x08000000;
    if ((info[2] & avx_bits) == avx_bits)
      s_supported_isa |= IsaAVX1;

    const int avx2_bits = (1 << 12) | 0x04000000 | 0x08000000;
    if ((info[2] & avx2_bits) == avx2_bits)
      s_supported_isa |= IsaAVX2;
  }

#ifdef _MSC_VER

  // check for OS support of AVX only if cpuid returned AVX support in CPU
  // since _xgetbv intrinsic can only be called on cpus which support it
  if ( (s_supported_isa & IsaAVX1) == IsaAVX1 ) {

#if (defined(_MSC_FULL_VER) && defined(_XCR_XFEATURE_ENABLED_MASK))
    bool no_xsave = ((info[2] & (1 << 27)) == 0);
    if (no_xsave) {
      s_supported_isa = IsaSSE42;
    } else {
      unsigned long long xcrFeatureMask = _xgetbv(_XCR_XFEATURE_ENABLED_MASK);
      if ((xcrFeatureMask & 0x6) != 0x6)
        s_supported_isa = IsaSSE42;
    }
#else  // meaning compiler does not have _xgetbv, cannot use AVX
    s_supported_isa = IsaSSE42;
#endif

  } // cpuid indicates AVX1 support
#endif // MSVC

  // set thread affinity for MKL (experimental)
#ifdef HAVE_MKL
  setEnv("KMP_AFFINITY", "granularity=fine,compact,1,0", false);
#endif
}

#else // not intel compiler, no cpuid - generic code only

void SysInfo::init()
{
  s_supported_isa = IsaGeneric;
}

#endif

std::string SysInfo::isaName()
{
  if ( supported(IsaAVX2) )
    return std::string("AVX-2 (Haswell)");
  else if ( supported(IsaAVX1) )
    return std::string("AVX-1 (Sandy-Bridge)");
  else if ( supported(IsaSSE42) )
    return std::string("SSE4.2 (Nehalem)");
  else if ( supported(IsaSSE41) )
    return std::string("SSE4.1 (Penryn)");
  else if ( supported(IsaSSE3) )
    return std::string("SSE3");
  else if ( supported(IsaSSE2) )
    return std::string("SSE2");
  else if ( supported(IsaSSE1) )
    return std::string("SSE");
  else
    return std::string("Generic");
}

uint SysInfo::osversion()
{
#ifdef GENUA_MACOSX
  struct utsname name;
  int stat = uname(&name);
  if (stat != 0)
    return 0;

  const char *s = name.release;
  char *tail;
  uint darwinMajor = strtol(s, &tail, 10);
  uint osxMinor = darwinMajor - 4;
  s = tail + 1;
  uint darwinMinor = strtol(s, &tail, 10);
  // s = tail + 1;
  // uint darwinPatch = strtol(s, &tail, 10);

  uint version = (10 << 16) | (osxMinor << 8) | darwinMinor;
  return version;

#elif defined(GENUA_WIN32)

  //#if VER_PRODUCTBUILD >= 9600

  //  if (IsWindows10OrGreater())
  //    return SysInfo::Win10;
  //  else if (IsWindows8OrGreater())
  //    return SysInfo::Win8;
  //  else if (IsWindows7OrGreater())
  //    return SysInfo::Win7;
  //  else
  //    return SysInfo::WinXp;

  //#else

  // this is deprecated, but the alternative is not working
  OSVERSIONINFO osvi;
  ZeroMemory(&osvi, sizeof(OSVERSIONINFO));
  osvi.dwOSVersionInfoSize = sizeof(OSVERSIONINFO);
  GetVersionEx(&osvi);
  uint osMajor = osvi.dwMajorVersion;
  uint osMinor = osvi.dwMinorVersion;
  return (osMajor << 16) | (osMinor << 8);

  // #endif

#endif
  return 0;
}

bool SysInfo::killProcess(uint64_t pid)
{
#ifdef GENUA_POSIX
  if (pid < 1)
    return false;
  int stat = kill(pid, SIGHUP);
  return (stat == 0);
#elif defined(GENUA_WIN32)
  HANDLE ph = OpenProcess(PROCESS_TERMINATE, FALSE, (DWORD) pid);
  if (ph == NULL)
    return false;
  return (TerminateProcess(ph, -1) == TRUE);
#endif
  return false;
}

string SysInfo::lastError()
{
#if defined(GENUA_WIN32)
  DWORD errorMessageID = GetLastError();
  if (errorMessageID == 0)
    return std::string();

  LPSTR messageBuffer = nullptr;
  size_t size;
  size = FormatMessageA(FORMAT_MESSAGE_ALLOCATE_BUFFER |
                        FORMAT_MESSAGE_FROM_SYSTEM |
                        FORMAT_MESSAGE_IGNORE_INSERTS,
                        NULL, errorMessageID,
                        MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
                        (LPSTR)&messageBuffer, 0, NULL);

  std::string message(messageBuffer, size);

  //Free the buffer.
  LocalFree(messageBuffer);

  if (not message.empty())
    return message;
  else
    return std::string("OS Error code: ") + std::to_string(errorMessageID);
#elif defined(GENUA_POSIX)
  char tmp[256];
  memset(tmp, 0, sizeof(tmp));
  strerror_r(errno, tmp, sizeof(tmp));
  return std::string(tmp);
#else
  return std::string();
#endif
}

