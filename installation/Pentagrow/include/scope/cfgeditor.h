
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
 
#ifndef CFGEDITOR_H
#define CFGEDITOR_H

#include <QDialog>

class ConfigParser;

namespace Ui {class CfgEditor;}

/** Allows to set property/value pairs in cfg files

  */
class CfgEditor : public QDialog
{
  Q_OBJECT

  public:

    /// copy settings from parent cfg
    CfgEditor(QWidget *parent, ConfigParser & c);

    /// destroy dialog
    ~CfgEditor();

    /// set configuration values from form
    void apply();

  private slots:

    /// insert new key row
    void newKey();

  protected:

    /// change language etc
    void changeEvent(QEvent *e);

  private:

    /// configuration to change
    ConfigParser & cfg;

    /// generated widgets
    Ui::CfgEditor *m_ui;
};

#endif // CFGEDITOR_H
