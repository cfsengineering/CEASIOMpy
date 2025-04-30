#include "spacemouseinterface.h"

#include <qglobal.h>
#include <QCoreApplication>
#include <QDebug>

boost::chrono::steady_clock SpaceMouseMotionData::s_clock;

uint16_t SpaceMouseInterface::s_connection_id = 0;
SpaceMouseInterface *SpaceMouseInterface::s_interface = 0;
double SpaceMouseInterface::s_maxEventFrequency = 30.0;

SpaceMouseInterface::SpaceMouseInterface()
{
  m_timestamp = m_clock.now();
}

void SpaceMouseInterface::motionCallback(const int16_t axis[], float dt)
{
  SpaceMouseMotionData mdata(axis, dt);
  emit axisMotion(mdata);
}

void SpaceMouseInterface::buttonCallback(uint32_t buttons)
{
  emit buttonPressed(buttons);
}

void SpaceMouseInterface::convertMotion(short tx, short ty, short tz,
                                        short rx, short ry, short rz,
                                        float elapsedTime)
{
  // limit event firing frequency
  if ( s_maxEventFrequency*secondsSinceLastEvent() > 1.0 ) {
    SpaceMouseMotionData md(tx, ty, tz, rx, ry, rz, elapsedTime);
    emit axisMotion(md);
    stamp();
  }
}

#if defined(Q_OS_MACX) && defined(HAVE_SPACENAV)

#include <ConnexionClientAPI.h>

//extern int16_t InstallConnexionHandlers(ConnexionMessageHandlerProc messageHandler,
//                                        ConnexionAddedHandlerProc addedHandler,
//                                        ConnexionRemovedHandlerProc removedHandler)
//__attribute__((weak_import));

extern int16_t SetConnexionHandlers(ConnexionMessageHandlerProc messageHandler,
                                    ConnexionAddedHandlerProc addedHandler,
                                    ConnexionRemovedHandlerProc removedHandler,
                                    bool useSeparateThread) __attribute__((weak_import));

// callback function
void  space_navigator_callback(unsigned int,
                               unsigned int messageType,
                               void *messageArgument)
{
  const double maxEventFrequency = 30.0; // per second
  static ConnexionDeviceState	lastState;
  ConnexionDeviceState		*state;

  switch(messageType)
  {
  case kConnexionMsgDeviceState:

    state = (ConnexionDeviceState*) messageArgument;
    if (state->client == SpaceMouseInterface::clientID())
    {
      // decipher what command/event is being reported by the driver
      bool anyChange = false;
      SpaceMouseInterface *gif = SpaceMouseInterface::globalInterface();
      assert(gif != 0);

      // ignore all events which come in too soon after the last one
      if (gif->secondsSinceLastEvent()*maxEventFrequency < 1.0)
        return;

      switch (state->command)
      {
      case kConnexionCmdHandleAxis:
        for (int i=0; i<6; ++i)
          anyChange |= (lastState.axis[i] != state->axis[i]);
        if (anyChange) {
          uint64_t dt = state->time - lastState.time;
          gif->motionCallback( state->axis, dt );
          gif->stamp();
        }
        break;

      case kConnexionCmdHandleButtons:
        if (state->buttons != lastState.buttons)
          gif->buttonCallback( state->buttons );
        break;
      }

      memmove(&lastState, state, sizeof(ConnexionDeviceState));
    }
    break;

  default:
    // other messageTypes can happen and should be ignored
    break;
  }
}

bool SpaceMouseInterface::connectDevice(QWidget *)
{
  if (s_interface == 0) {
    s_interface = new SpaceMouseInterface;
    qRegisterMetaType<SpaceMouseMotionData>("SpaceMouseMotionData");
  }

  if (&SetConnexionHandlers != NULL) {
    int16_t error = SetConnexionHandlers(space_navigator_callback, 0L, 0L, true);
    if (error != 0)
      return false;

    // query application name
    QCoreApplication *app = QCoreApplication::instance();
    QByteArray a = app->applicationName().toUtf8();
    std::string appname( a.constData() );
#ifndef NDEBUG
    appname += "_debug";
#endif
    qDebug("Registering appName = [%s] with Connexion driver.",
           appname.c_str());

    // must pass application name as pascal string
    uint32_t signature = 0;
    char pp = (char) appname.length();
    appname.insert(appname.begin(), pp);
    s_connection_id = RegisterConnexionClient( signature,
                                               (uint8_t*) &appname[0],
        kConnexionClientModeTakeOver,
        kConnexionMaskAll);

    qDebug("Connection to SpaceNavigator driver established, id = %d",
           s_connection_id);
    return true;
  }

  qDebug("Failed to connect to SpaceNavigator driver.");
  return false;
}

void SpaceMouseInterface::disconnectDevice()
{
  if(&InstallConnexionHandlers != NULL){
    if (s_connection_id)
      UnregisterConnexionClient(s_connection_id);
    CleanupConnexionHandlers();
    s_connection_id = 0;
  }
}

#elif defined(Q_OS_WIN) && defined(HAVE_SPACENAV)

#include "Mouse3DInput.h"

Mouse3DInput *g_m3d_adapter = 0;

bool SpaceMouseInterface::connectDevice(QWidget *rcv)
{
  // create static interface object
  if (s_interface == 0) {
    s_interface = new SpaceMouseInterface;
    qRegisterMetaType<SpaceMouseMotionData>("SpaceMouseMotionData");
  }

  // create a new adapter object which catches raw input events
  if ( g_m3d_adapter == 0 ) {
    g_m3d_adapter = new Mouse3DInput(rcv);
    connect( g_m3d_adapter, SIGNAL(RawMotion3d(short,short,short,short,short,short,float)),
             s_interface, SLOT(convertMotion(short,short,short,short,short,short,float)) );
  }

  return true;
}

void SpaceMouseInterface::disconnectDevice() {}

#else

// interface not implemented for this OS
bool SpaceMouseInterface::connectDevice(QWidget *)
{
  s_interface = new SpaceMouseInterface;
  return false;
}

void SpaceMouseInterface::disconnectDevice() {}

#endif
