
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
 
#ifndef SECTIONCOPYDIALOG_H
#define SECTIONCOPYDIALOG_H

#include "ui_sectioncopydialog.h"
#include "forward.h"
#include <QList>

class QCheckBox;

/** Enable creating copies of existing mesh sections
 *
 *  In its initial implementation, this will allow to create a mirror
 *  copy of an existing section. Later, other operations, such as grid
 *  copies, might be implemented when needed.
 *
 */
class SectionCopyDialog : public QDialog, private Ui::SectionCopyDialog
{
  Q_OBJECT
  
public:

  /// create dialog
  explicit SectionCopyDialog(QWidget *parent = 0);
  
  /// assign to mesh
  void assign(MxMeshPtr pmx);

signals:

  /// mesh topology, structure and geometry can have changed
  void meshChanged();

private slots:

  /// perform copy operations
  void apply();

protected:

  /// runtime language change etc.
  void changeEvent(QEvent *e);

private:

  /// pointer to mesh
  MxMeshPtr m_pmx;

  /// check boxes inserted into the dialog dynamically
  QList<QCheckBox*> m_boxes;
};

#endif // SECTIONCOPYDIALOG_H
