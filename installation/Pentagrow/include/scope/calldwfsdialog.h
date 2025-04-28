
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
 
#ifndef CALLDWFSDIALOG_H
#define CALLDWFSDIALOG_H

#include <QtGui/QDialog>
#include <genua/defines.h>
#include <genua/configparser.h>

class QProcess;
class MxMesh;
class ProcessMonitor;

namespace Ui {
    class CallDwfsDialog;
}

/** Simple frontend for calling dwfs.
  */
class CallDwfsDialog : public QDialog
{
  Q_OBJECT
  public:

    /// create dialog
    CallDwfsDialog(QWidget *parent, MxMesh *mesh);

    /// destroy dialog
    ~CallDwfsDialog();

    /// register location of the original mesh file
    void meshFile(const QString & mf);

    /// change working directory for dwfs
    void workDir(const QString & wd);

    /// dialog already visible ?
    static bool shown() {return bShown;}

  signals:

    /// emitted when solver generated result file
    void solverFinished(const QString & wd);

  private slots:

    /// browse work directory
    void browseWorkDir();

    /// update work directory when edited
    void changeWorkdir();

    /// browse for solver executable
    void changeSolver();

    /// start dwfs
    void startProcess();

    /// load configuration from file
    void loadConfig();

    /// edit configuration file
    void editConfig();

    /// load result file when finished
    void finished();

  protected:

    /// change language
    void changeEvent(QEvent *e);

    /// locate solver executable
    bool locateSolver();

    /// set form values from configuration object
    void fillForm();

    /// transfer settings from form to configuration
    void buildConfig();

    /// assemble path for filename f
    QString workFile(const QString & f);

    /// assemble path for filename f
    QString workFile(const std::string & f) {
      return workFile(QString::fromStdString(f));
    }

  private:

    /// display mesh object
    MxMesh *pmesh;

    /// dwfs process started
    QProcess *solverproc;

    /// monitor widget
    ProcessMonitor *pmoni;

    /// configuration object
    ConfigParser cfg;

    /// path to mesh file and dwfs executable
    QString mshfile, execpath;

    /// translated names of simulation types
    QStringList simnames;

    /// map dwfs simulation types to indices
    StringArray simpos;

    /// generated UI object
    Ui::CallDwfsDialog *m_ui;

    /// working directory for dwfs
    static QString workdir;

    /// true if dialog is already shown
    static bool bShown;
};

#endif // CALLDWFSDIALOG_H
