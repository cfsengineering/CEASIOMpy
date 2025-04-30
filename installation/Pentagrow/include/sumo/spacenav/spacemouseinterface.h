#ifndef SPACEMOUSEINTERFACE_H
#define SPACEMOUSEINTERFACE_H

#ifndef Q_MOC_RUN
#include <genua/forward.h>
#include <boost/chrono.hpp>
#endif
#include <QObject>
#include <QMetaType>

/** Encapsulates data passed from multi-axis controller.
 *
 *  SpaceMouseMotionData is the basic object used to pass multi-axis data
 *  from a 3D mouse to the application. The meaning of the axis values,
 *  such as scaling, is device-dependent. 3D Connexion devices, for example,
 *  generate maximum axis values of 1024 at full deflection.
 *
 *  \ingroup guiapp
 *  \sa SpaceMouseInterface, SpaceMouseMotionEvent
 */
class SpaceMouseMotionData
{
public:

  /// create undefined event
  SpaceMouseMotionData() {}

  /// initialize with raw data
  SpaceMouseMotionData(const int16_t axis[], float dt = 0.0f)
    : m_elapsedTime(dt)
  {
    std::copy(axis, axis+6, m_axis);
    m_temitted = s_clock.now();
  }

  /// initialize with raw data
  SpaceMouseMotionData(short tx, short ty, short tz,
                       short rx, short ry, short rz,
                       float dt) : m_elapsedTime(dt)
  {
    m_axis[0] = tx;
    m_axis[1] = ty;
    m_axis[2] = tz;
    m_axis[3] = rx;
    m_axis[4] = ry;
    m_axis[5] = rz;
    m_temitted = s_clock.now();
  }

  /// return value of axis i as a fraction of the maximum
  float axisSpeed(size_t i) const {
    assert(i < 6);
    return int(m_axis[i]) / 1024.0f;
  }

  /// return amount of motion, interpreting navigator output as speed
  float axisPosDelta(size_t i) const {
    return m_elapsedTime*axisSpeed(i);
  }

  /// time since this event was emitted, in seconds
  double age() const {
    return (s_clock.now() - m_temitted).count() * 1e-9;
  }

private:

  /// time when this event was emitted
  boost::chrono::steady_clock::time_point m_temitted;

  /// motion controller axis positions
  int16_t m_axis[6];

  /// time elapsed since last motion event
  float m_elapsedTime;

  /// clock used for timestamping
  static boost::chrono::steady_clock s_clock;
};

Q_DECLARE_METATYPE(SpaceMouseMotionData)

/** Interface to device driver for multi-axis controller.
 *
 *  A glue layer/wrapper to provide a reasonably platform-independet interface
 *  for use of multi-axis controller devices such as the 3D Connexion
 *  SpaceNavigator series.
 *
 *  On Mac OS X, this interface makes use of the 3D Connexion driver. This means
 *  that the 3D Connexion SDK needs to be installed for compilation and that the
 *  driver must be present when running the application.
 *
 *  On Windows, the SDK is not required for compilation. Still, to connect to
 *  the device, the driver package must be installed. At least Windows XP SP1
 *  (or, better, Windows 7) is needed to use this interface.
 *
 * \ingroup guiapp
 * \sa SpaceMouseMotionData
 */
class SpaceMouseInterface : public QObject
{
Q_OBJECT

public:

  enum SpaceMouseButton { NoButton = 0x0,
                          LeftButton = 0x1,
                          RightButton = 0x2 };

  /// set event timer
  SpaceMouseInterface();

  /// try to connect to device
  static bool connectDevice(QWidget *rcv);

  /// disconnect device, call before exiting application
  static void disconnectDevice();

  /// access client ID (OS X)
  static uint16_t clientID() {return s_connection_id;}

  /// access global interface object
  static SpaceMouseInterface *globalInterface() {return s_interface;}

  /// called by the message handler (OS X)
  void motionCallback(const int16_t axis[], float dt);

  /// called by the message handler (OS X)
  void buttonCallback(uint32_t buttons);

  /// time, in seconds, since last event was handled
  double secondsSinceLastEvent() const {
    return (m_clock.now() - m_timestamp).count() * 1e-9;
  }

  /// set timestamp
  void stamp() {
    m_timestamp = m_clock.now();
  }

signals:

  /// signal emitted when a new motion event is detected w/o event receiver
  void axisMotion(const SpaceMouseMotionData &motion);

  /// emitted when any button pressed
  void buttonPressed(uint buttons);

private slots:

  /// convert data message format
  void convertMotion(short tx, short ty, short tz,
                     short rx, short ry, short rz,
                     float elapsedTime);

private:

  /// connection ID (for Mac OS X 3DConnexion driver interface)
  static uint16_t s_connection_id;

  /// global interface object
  static SpaceMouseInterface *s_interface;

  /// maximum permitted event frequency (events per second)
  static double s_maxEventFrequency;

  /// for event timing
  boost::chrono::steady_clock m_clock;

  /// seconds since last event propagated
  boost::chrono::steady_clock::time_point m_timestamp;
};

#endif // SPACEMOUSEINTERFACE_H
