
/* ------------------------------------------------------------------------
 * project:    Scope
 * file:       main.cpp
 * copyright:  (c) 2007 by david.eller@gmx.net
 * ------------------------------------------------------------------------
 * main program for mesh data vizualization tool
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */

#include "scope.h"
#include "version.h"
#include <genua/xcept.h>
#include <genua/sysinfo.h>
#include <QApplication>
#include <QGLFormat>
#include <QDebug>
#include <QSysInfo>
#include <QSettings>
#include <iostream>

using namespace std;

class ScopeApp : public QApplication
{
public:

  ScopeApp(int &argc, char *argv[]) : QApplication(argc, argv) {}

  bool notify(QObject *receiver, QEvent *event) {
    try {
      return QApplication::notify(receiver, event);
    } catch (Error & xcp) {
      cerr << xcp.what();
      return false;
    } catch (std::exception & e) {
      cerr << e.what();
      return false;
    }
    return false;
  }
};

int main( int argc, char ** argv )
{

  Q_INIT_RESOURCE(icons);

#ifdef Q_OS_MACX
  // https://bugreports.qt-project.org/browse/QTBUG-32789
  if ( QSysInfo::MacintoshVersion > QSysInfo::MV_10_8 )
    QFont::insertSubstitution(".Lucida Grande UI", "Lucida Grande");
#elif defined(Q_OS_LINUX)
  // set c-runtime locale to default; otherwise, string-to-number conversions
  // will try to use the system language settings which will break e.g. NASTRAN
  // bulk and punch data import
  SysInfo::setEnv("LANG", "C");
  SysInfo::setEnv("LANGUAGE", "en");
  SysInfo::setEnv("LC_CTYPE", "en_US.UTF-8");
  SysInfo::setEnv("LC_NUMERIC", "C");
  SysInfo::setEnv("LC_IDENTIFICATION", "C");
  SysInfo::setEnv("LC_ALL", "");
  unsetenv("QT_QPA_PLATFORMTHEME");
#endif

  try {

    ScopeApp a( argc, argv );
    a.setApplicationName("dwfscope");
    a.setApplicationVersion(_scope_qversion);
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
    if (appSettings.value("scope-enable-fsaa",
                          enable_fsaa).toBool()) {
      QGLFormat f = QGLFormat::defaultFormat();
      f.setSampleBuffers(true);
      f.setSamples(4);
      if (f.sampleBuffers())
        qDebug("FSAA enabled, %dx multisampling.", f.samples());
      else
        qDebug("Multisampling anti-alisiasing not supported.");
    }
    QGLFormat::setDefaultFormat(f);

    Scope *mw = new Scope();
    mw->setWindowTitle( QString("scope ") + _scope_qversion );
    if (appSettings.value("scope-mainwindow-maximized", false).toBool())
      mw->showMaximized();
    else
      mw->show();

    a.connect( &a, SIGNAL(lastWindowClosed()), &a, SLOT(quit()) );

    // allow for data files as command line arguments
    QStringList args = a.arguments();
    if (args.size() > 1) {
      mw->load( args.at(1) );
    }
    
    return a.exec();

  } catch (Error & xcp) {
    cerr << xcp.what();
    return EXIT_FAILURE;
  }
  
  return EXIT_SUCCESS;
}
