
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       linux_macaddress.cpp
 * begin:      January 2009
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Determine MAC address on Linux
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

#include <cstring>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

#define   _HWA_SUCCESS        0
#define   _HWA_NO_SOCKET     -1
#define   _HWA_IOCTL_ERROR   -2

int linux_hardware_address(const char *ifname, int hwa[])
{
  int fd = socket(PF_INET, SOCK_STREAM, 0);
  if (fd == -1)
    return _HWA_NO_SOCKET;
  
  struct ifreq ifr;
  strncpy(ifr.ifr_name, ifname, sizeof(ifr.ifr_name));
  int stat = ::ioctl(fd, SIOCGIFHWADDR, &ifr);
  if (stat < 0)
    return _HWA_IOCTL_ERROR;
  
  char *addr = (char *) ifr.ifr_hwaddr.sa_data;
  for (int i=0; i<6; ++i) {
    hwa[i] = *((unsigned char *) addr);
    ++addr;
  }
  
  return _HWA_SUCCESS;
}

