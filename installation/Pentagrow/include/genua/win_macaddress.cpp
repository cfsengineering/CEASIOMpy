
/* ------------------------------------------------------------------------
 * project:    Genua
 * file:       win_macaddress.cpp
 * begin:      January 2009
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Determine MAC address on windows 
 *
 * See the file license.txt for copyright and licensing information.
 * ------------------------------------------------------------------------ */

//#ifdef _MSC_VER
//
//#include <winsock2.h>
//#include <iphlpapi.h>
//#include <cstdlib>
//
//int win_primary_address(int hwa[6])
//{
//  PIP_ADAPTER_ADDRESSES pAddress = NULL;
//  PIP_ADAPTER_ADDRESSES pAddrIterator = NULL;
//  ULONG Family;
//  ULONG Flags;
//  ULONG Size, Stat;
//  BYTE *bMAC;
//  
//  Family = AF_UNSPEC;
//  Flags = 0;
//  Size = 0;
//  
//  // determine size to allocate
//  Size = sizeof(IP_ADAPTER_ADDRESSES);
//  pAddress = (IP_ADAPTER_ADDRESSES *) malloc(Size);
//  Stat = GetAdaptersAddresses(Family, Flags, NULL, 
//                              pAddress, &Size);
//  
//  if (Stat == ERROR_BUFFER_OVERFLOW) {
//    free(pAddress);
//    pAddress = (IP_ADAPTER_ADDRESSES *) malloc(Size);
//    Stat = GetAdaptersAddresses(Family, Flags, NULL, 
//                                pAddress, &Size);
//  }
//  
//  if (Stat == NO_ERROR) {
//    for (pAddrIterator = pAddress; 
//         pAddrIterator != NULL; 
//         pAddrIterator = pAddrIterator->next) {
//           
//           Size = pAddrIterator->PhysicalAddressLength;
//           bMAC = pAddrIterator->PhysicalAddress;
//           if (Size >= 6) {
//             for (int i=0; i<6; ++i)
//               hwa[i] = (int) bMAC[i];
//             
//             free(pAddress);
//             return 0;
//           }
//         }
//  }
//  
//  free(pAddress);
//  return 1;
//}
//
//#else

#include <winsock2.h>
#include <IPHlpApi.h>
#include <cstdlib>

#pragma comment(lib, "IPHLPAPI.lib")

int win_primary_address(int hwa[6])
{
  DWORD dwStatus;
  ULONG ulSize = 0;
  IP_ADAPTER_INFO *pAdapterInfo = NULL; 
  IP_ADAPTER_INFO *pItr = NULL;   
  
  // request allocation size 
  dwStatus = GetAdaptersInfo(pAdapterInfo, &ulSize);
  if (dwStatus != ERROR_BUFFER_OVERFLOW)
    return 1;
  
  pAdapterInfo = (IP_ADAPTER_INFO *) malloc(ulSize);
  dwStatus = GetAdaptersInfo(pAdapterInfo, &ulSize);
  if (dwStatus == NO_ERROR) {
    for (pItr = pAdapterInfo; pItr != NULL; pItr = pItr->Next) {
      UINT len = pItr->AddressLength;
      if (len >= 6) {
        BYTE *bMac = pItr->Address;
        for (int i=0; i<6; ++i)
          hwa[i] = (int) bMac[i];
        
        free(pAdapterInfo);
        return 0;
      }
    }
  }
  
  free(pAdapterInfo);
  return 1;
}

// #endif

