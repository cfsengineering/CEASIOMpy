
/* ------------------------------------------------------------------------
 * file:       main.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Surface modeler : main program
 * ------------------------------------------------------------------------ */

#include "sumo.h"
#include "version.h"
#include "pool.h"
#include "batchrun.h"
#include "componentlibrary.h"

#include <genua/xcept.h>
#include <genua/sysinfo.h>
#include <surf/skinsurf.h>
#include <surf/splinecapsurf.h>

#include <QApplication>
#include <QGLFormat>
#include <QSettings>
#include <QDebug>
#include <iostream>

/** Workaround compiler problem with Visual Studio 2010 */
#if defined(_MSC_VER) && (_MSC_VER == 1600)
#include <new>
namespace std { const nothrow_t nothrow = nothrow_t(); }
#endif

using namespace std;

int main(int argc, char *argv[])
{

#ifdef Q_OS_MACX
  // https://bugreports.qt-project.org/browse/QTBUG-32789
  if ( QSysInfo::MacintoshVersion > QSysInfo::MV_10_8 )
    QFont::insertSubstitution(".Lucida Grande UI", "Lucida Grande");
#elif defined(Q_OS_LINUX)
  // set c-runtime locale to default; otherwise, string-to-number conversions
  // will try to use the system language settings
  SysInfo::setEnv("LANG", "C");
  SysInfo::setEnv("LANGUAGE", "en");
  SysInfo::setEnv("LC_CTYPE", "en_US.UTF-8");
  SysInfo::setEnv("LC_NUMERIC", "C");
  SysInfo::setEnv("LC_IDENTIFICATION", "C");
  SysInfo::setEnv("LC_ALL", "");
  unsetenv("QT_QPA_PLATFORMTHEME");
#endif

  try {
    
    // initialize thread pool
    // SysInfo::nthread(1);
    cout << "Using " << SysInfo::nthread() << " threads." << endl;
    SumoPool::start(SysInfo::nthread());

    // initialize global component library 
    SumoComponentLib.loadPredefined();
    
    // skinned surfaces in libsurf must be limited to 101+p knots 
    // if we want to be able to export to CAD via IGES, simply because
    // most CAD systems are too stupid to import surfaces with more knots 
    //SkinSurf::limitUKnotCount(103);
    //SplineCapSurf::limitUKnotCount(103);
    
    // initialize Qt
    QApplication a( argc, argv );
    a.setApplicationName("dwfsumo");
    a.setApplicationVersion(_sumo_qversion);
    a.setOrganizationDomain("larosterna.com");
    a.setOrganizationName("larosterna");
    a.setAttribute(Qt::AA_DontCreateNativeWidgetSiblings);
#if (QT_VERSION >= QT_VERSION_CHECK(5, 2, 0))
    a.setAttribute(Qt::AA_UseHighDpiPixmaps);
#endif
#if defined(Q_OS_WIN32)
    a.addLibraryPath(QCoreApplication::applicationDirPath());
#elif defined(Q_OS_LINUX)
    a.addLibraryPath(QCoreApplication::applicationDirPath() + "/../lib");
    for (const QString &s : QCoreApplication::libraryPaths()) {
      qDebug() << s;
    }
#endif

    // start in batch mode if requested
    if ( BatchRun::run(argc, argv) )
      return EXIT_SUCCESS;
    
    QSettings appSettings;

    // enable full-scene antialiasing
#if QT_VERSION >= QT_VERSION_CHECK(5,0,0)
    bool enable_fsaa = (a.devicePixelRatio() <= 1.0);
#else
    bool enable_fsaa = true;
#endif

    QGLFormat f = QGLFormat::defaultFormat();
#ifdef Q_OS_LINUX
  f.setSwapInterval(0);
#endif
    if (appSettings.value("sumo-enable-fsaa",
                          enable_fsaa).toBool()) {
      QGLFormat f = QGLFormat::defaultFormat();
      f.setSampleBuffers(true);
      f.setSamples(4);
      qDebug("FSAA enabled.");
    }
    QGLFormat::setDefaultFormat(f);

    // start graphical application
    SumoMain *mw = new SumoMain();
    QString title("sumo ");
    title += _sumo_qversion;
    mw->setWindowTitle(title);
    if (appSettings.value("sumo-show-maximized", false).toBool())
      mw->showMaximized();
    else
      mw->show();
    a.connect( &a, SIGNAL(lastWindowClosed()), &a, SLOT(quit()) );

    if (a.arguments().size() > 1) {
      QString fname(a.arguments().at(1));
      if (fname.endsWith(".smx"))
        mw->load(fname);
      else if (fname.endsWith(".xml"))
        mw->loadCsm(fname);
      else
        mw->newAssembly();
    } else {
      mw->newAssembly();
    }

    return a.exec();
    
  } catch (Error & xcp) {
    
    clog << xcp.what() << endl;
    return EXIT_FAILURE;
  }
}
