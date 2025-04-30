
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
 
#include <genua/configparser.h>
#include <genua/strutils.h>
#include "cfgeditor.h"
#include "util.h"
#include "ui_cfgeditor.h"

using namespace std;

CfgEditor::CfgEditor(QWidget *parent, ConfigParser & c) :
    QDialog(parent, Qt::Tool), cfg(c), m_ui(new Ui::CfgEditor)
{
  m_ui->setupUi(this);

  connect(m_ui->pbNewKey, SIGNAL(clicked()), this, SLOT(newKey()) );

  int row(0);
  ConfigParser::iterator itr, last(cfg.end());
  m_ui->table->setRowCount( std::distance(cfg.begin(), last) );
  for (itr = cfg.begin(); itr != last; ++itr) {
    QString key = QString::fromStdString(itr->first);
    QString val = QString::fromStdString(itr->second);
    if (key.isEmpty())
      continue;
    m_ui->table->setItem(row, 0, new QTableWidgetItem(key));
    m_ui->table->setItem(row, 1, new QTableWidgetItem(val));
    ++row;
  }

  m_ui->table->resizeColumnsToContents();

}

CfgEditor::~CfgEditor()
{
    delete m_ui;
}

void CfgEditor::newKey()
{
  m_ui->table->insertRow( m_ui->table->currentRow() );
}

void CfgEditor::apply()
{
  const int nrows = m_ui->table->rowCount();
  for (int i=0; i<nrows; ++i) {
    const QTableWidgetItem *ikey = m_ui->table->item(i, 0);
    const QTableWidgetItem *ival = m_ui->table->item(i, 1);
    if (ikey == 0 or ival == 0)
      continue;

    string key = strip(str(ikey->text()));
    string val = strip(str(ival->text()));
    if (not key.empty())
      cfg[key] = val;
  }
}

void CfgEditor::changeEvent(QEvent *e)
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
