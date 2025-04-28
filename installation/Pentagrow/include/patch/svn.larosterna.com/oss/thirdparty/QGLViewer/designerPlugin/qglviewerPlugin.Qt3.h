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

#include <qwidgetplugin.h>

class QGLViewerPlugin : public QWidgetPlugin
{
public:
  QStringList keys() const;
  QWidget *create(const QString& key, QWidget *parent, const char *name);
  QString group(const QString& key) const;
  QIconSet iconSet(const QString&) const;
  QString includeFile(const QString& key) const;
  QString toolTip(const QString& key) const;
  QString whatsThis(const QString& key) const;
  bool isContainer(const QString&) const;
};
