
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
 
#include "splitridgedialog.h"
#include "ui_splitridgedialog.h"
#include <genua/defines.h>
#include <genua/trigo.h>

SplitRidgeDialog::SplitRidgeDialog(QWidget *parent) :
  QDialog(parent),
  ui(new Ui::SplitRidgeDialog)
{
  ui->setupUi(this);
  ui->m_sbMergeThreshold->setValue(1e-12);
}

SplitRidgeDialog::~SplitRidgeDialog()
{
  delete ui;
}

double SplitRidgeDialog::featureAngle() const
{
  double angle = ui->m_sbFeatureAngle->value();
  if (ui->m_cbSplitRidges->isChecked())
    return rad(angle);
  else
    return -PI;
}

double SplitRidgeDialog::mergeThreshold() const
{
  return ui->m_sbMergeThreshold->value();
}
