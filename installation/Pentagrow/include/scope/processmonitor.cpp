
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
 
#include <iostream>
#include <QProcess>
#include <QFile>
#include <genua/defines.h>

#include "processmonitor.h"
#include "ui_processmonitor.h"

using namespace std;

ProcessMonitor::ProcessMonitor(QWidget *parent, QProcess *p) :
    QDialog(parent, Qt::Tool), proc(p),
    m_ui(new Ui::ProcessMonitor)
{
  m_ui->setupUi(this);

  // append stdout to buffer
  connect(proc, SIGNAL(readyReadStandardOutput()), this, SLOT(appendOutput()) );
  connect(proc, SIGNAL(readyReadStandardError()), this, SLOT(appendLog()) );

  // show log file when requested
  connect(m_ui->pbViewLog, SIGNAL(clicked()), this, SLOT(showLog()) );

  // kill process on widget close
  connect(m_ui->pbClose, SIGNAL(clicked()), this, SLOT(kill()) );
  connect(m_ui->pbInterrupt, SIGNAL(clicked()), this, SLOT(kill()) );

  bLogDisplay = false;
}

ProcessMonitor::~ProcessMonitor()
{
  delete m_ui;
}

void ProcessMonitor::clearDisplay()
{
  plog.clear();
  pout.clear();
  m_ui->textBrowser->clear();
}

void ProcessMonitor::appendOutput(const QString & s)
{
  pout.append(s);
  if (not bLogDisplay)
    m_ui->textBrowser->setPlainText( pout );
}

void ProcessMonitor::appendLog(const QString & s)
{
  plog.append(s);
  if (bLogDisplay)
    m_ui->textBrowser->setPlainText( plog );
}

void ProcessMonitor::appendOutput()
{
  pout.append(proc->readAllStandardOutput());
  if (not bLogDisplay)
    m_ui->textBrowser->setPlainText( pout );
}

void ProcessMonitor::appendLog()
{
  plog.append(proc->readAllStandardError());
  if (bLogDisplay)
    m_ui->textBrowser->setPlainText( plog );
}

void ProcessMonitor::kill()
{
  proc->kill();
  m_ui->pbInterrupt->setEnabled(false);
}

void ProcessMonitor::showLog()
{
  if (bLogDisplay) {
    m_ui->textBrowser->setPlainText( pout );
    bLogDisplay = false;
    m_ui->pbViewLog->setText(tr("&View log"));
  } else {
    m_ui->textBrowser->setPlainText( plog );
    bLogDisplay = true;
    m_ui->pbViewLog->setText(tr("&View output"));
  }
}

void ProcessMonitor::dumpLog(const QString & fname)
{
  QFile file(fname);
  if (file.open(QIODevice::WriteOnly)) {
    file.write(plog.toUtf8());
  }
}

void ProcessMonitor::changeEvent(QEvent *e)
{
  QDialog::changeEvent(e);
  switch (e->type()) {
      case QEvent::LanguageChange:
    m_ui->retranslateUi(this);
    break;
      default:
    break;
  }
}
