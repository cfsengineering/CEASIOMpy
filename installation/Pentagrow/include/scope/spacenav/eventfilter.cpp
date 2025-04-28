#include "eventfilter.h"
#include "Mouse3DInput.h"
#include <Windows.h>

EventFilter::EventFilter(Mouse3DInput *gm)
  : QAbstractNativeEventFilter(), gMouseInput(gm)
{
}

bool EventFilter::nativeEventFilter(const QByteArray &,
                                    void * message, long * result)
{
  MSG *wmsg = (MSG *) message;
  if (gMouseInput == 0)
    return false;

  if (wmsg->message == WM_INPUT) {
    HRAWINPUT hRawInput = reinterpret_cast<HRAWINPUT>(wmsg->lParam);
    gMouseInput->OnRawInput(RIM_INPUT, hRawInput);
    if (result != 0)  {
      result = 0;
    }
    return true;
  }

  return false;
}
