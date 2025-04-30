
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       macaddress.h
 * begin:      January 2009
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Determine MAC address of primary ethernet interface 
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#ifndef GENUA_MACADDRESS_H
#define GENUA_MACADDRESS_H

#if defined(__linux)

int linux_hardware_address(const char ifname[], int hwa[]);

inline int primary_mac_address(int hwa[6])
{
  return linux_hardware_address("eth0", hwa);
}

#elif defined(__APPLE__)

int macosx_primary_address(int hwa[6]);

inline int primary_mac_address(int hwa[6])
{
  return macosx_primary_address(hwa);
}

#elif defined(_WIN32)

int win_primary_address(int hwa[6]);

inline int primary_mac_address(int hwa[6])
{
  return win_primary_address(hwa);
}

#endif

#endif
