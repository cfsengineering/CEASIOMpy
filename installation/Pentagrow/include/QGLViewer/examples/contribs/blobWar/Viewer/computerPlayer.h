/****************************************************************************

 Copyright (C) 2002-2008 Gilles Debunne. All rights reserved.

 This file is part of the QGLViewer library version 2.3.1.

 http://www.libqglviewer.com - contact@libqglviewer.com

 This file may be used under the terms of the GNU General Public License 
 versions 2.0 or 3.0 as published by the Free Software Foundation and
 appearing in the LICENSE file included in the packaging of this file.
 In addition, as a special exception, Gilles Debunne gives you certain 
 additional rights, described in the file GPL_EXCEPTION in this package.

 libQGLViewer uses dual licensing. Commercial/proprietary software must
 purchase a libQGLViewer Commercial License.

 This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
 WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.

*****************************************************************************/

#ifndef COMPUTER_PLAYER_H
#define COMPUTER_PLAYER_H

#include "qobject.h"
#include "qstring.h"

class ComputerPlayerInterface;
class QProcess;

class ComputerPlayer : public QObject
{
  Q_OBJECT
  
public:
  ComputerPlayer();
  ~ComputerPlayer();
  
  bool isActive() const { return isActive_; }
  void setIsActive(bool on);
  
  int allowedTime() const;
  void setAllowedTime(int time);

  QString programFileName() const;
  void setProgramFileName(const QString& name);

  void configure();

  void play(bool blue, const QString& stateFileName);

public:
  signals:
  void moveMade(QString move, int duration);
 
private slots:
  void selectProgram();
  void readFromStdout();
  
private:
  bool isActive_;
  ComputerPlayerInterface* interface_;
  QProcess* process_;
};

#endif // COMPUTER_PLAYER_H
