#ifndef EVENTFILTER_H
#define EVENTFILTER_H

#include <QAbstractNativeEventFilter>

class Mouse3DInput;

class EventFilter : public QAbstractNativeEventFilter
{
public:

  explicit EventFilter(Mouse3DInput *gm);

  bool nativeEventFilter(const QByteArray & eventType,
                         void * message, long * result);

private:

  Mouse3DInput *gMouseInput;

};

#endif // EVENTFILTER_H
