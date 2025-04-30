
/* Copyright (C) 2015 David Eller <david@larosterna.com>
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
 
#ifndef PROCESSMONITOR_H
#define PROCESSMONITOR_H

#include <QDialog>

class QProcess;
class QFileSystemWatcher;

namespace Ui {class ProcessMonitor;}

/** Simple text viewer which shows program's stdout



  */
class ProcessMonitor : public QDialog
{
  Q_OBJECT

  public:

    /// create monitor for process p
    ProcessMonitor(QWidget *parent, QProcess *p);

    /// destroy UI, don't touch process
    ~ProcessMonitor();

    /// write logfile to file fname
    void dumpLog(const QString & fname);

  public slots:

    /// clear display
    void clearDisplay();

    /// append display to text browser
    void appendOutput(const QString & s);

    /// append display to text browser
    void appendLog(const QString & s);

    /// kill process
    void kill();

    /// view log file
    void showLog();

  private slots:

    /// receive output from program
    void appendOutput();

    /// receive execution log from program
    void appendLog();

  protected:

    /// change language
    void changeEvent(QEvent *e);

  private:

    /// process to watch
    QProcess *proc;

    /// store program output and log
    QString pout, plog;

    /// which output is active
    bool bLogDisplay;

    /// generated UI
    Ui::ProcessMonitor *m_ui;
};

#endif // PROCESSMONITOR_H
