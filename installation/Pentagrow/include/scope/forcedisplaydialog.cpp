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

#include "forcedisplaydialog.h"
#include "util.h"
#include <genua/mxmesh.h>
#include <QFileDialog>
#include <fstream>

ForceDisplayDialog::ForceDisplayDialog(QWidget *parent) : QDialog(parent)
{
  setupUi(this);
  twDisplay->resizeColumnsToContents();
  twDisplay->setAlternatingRowColors(true);
  twDisplay->setShowGrid(false);
#if (QT_VERSION >= QT_VERSION_CHECK(5, 0, 0))
  QHeaderView* header = twDisplay->horizontalHeader();
  header->setSectionResizeMode(QHeaderView::Stretch);
#endif

  connect(cbSelectField, SIGNAL(currentIndexChanged(int)),
          this, SLOT(computeForces()));
  connect(sbRefX, SIGNAL(editingFinished()),
          this, SLOT(computeForces()));
  connect(sbRefY, SIGNAL(editingFinished()),
          this, SLOT(computeForces()));
  connect(sbRefZ, SIGNAL(editingFinished()),
          this, SLOT(computeForces()));
  connect(pbExport, SIGNAL(clicked()),
          this, SLOT(exportTable()));
}

void ForceDisplayDialog::assign(MxMeshPtr pmx)
{
  m_initializing = true;
  m_pmx = pmx;
  if (m_pmx == nullptr)
    return;

  m_isections.clear();
  for (size_t i=0; i<m_pmx->nsections(); ++i) {
    if (m_pmx->section(i).surfaceElements()) {
      m_isections.push_back(i);
    }
  }
  twDisplay->setRowCount(m_isections.size()+1);

  m_ifields.clear();
  cbSelectField->clear();
  int cpfield = -1;
  for (size_t i=0; i<m_pmx->nfields(); ++i) {
    const MxMeshField &f = m_pmx->field(i);
    if (f.nodal() and f.realField() and f.ndimension() == 1) {
      m_ifields.push_back(i);
      cbSelectField->addItem(qstr(f.name()));
      if (f.name() == "CoefPressure" or f.name() == "pressure_coef"
          or f.name() == "pressure")
        cpfield = (m_ifields.size()-1);
    }
  }

  m_initializing = false;
  if (cpfield != -1)
    cbSelectField->setCurrentIndex(cpfield);

  twDisplay->resizeColumnsToContents();
  adjustSize();
}

void ForceDisplayDialog::selectField(int fix)
{
  uint idx = sorted_index(m_ifields, (uint) fix);
  if (idx != NotFound) {
    cbSelectField->setCurrentIndex(idx);
  }
}

void ForceDisplayDialog::computeForces()
{
  if (m_initializing)
    return;

  int idx = cbSelectField->currentIndex();
  if (idx < 0 or size_t(idx) >= m_ifields.size())
    return;
  if (m_pmx == nullptr)
    return;

  uint fix = m_ifields[idx];
  if (fix >= m_pmx->nfields())
    return;

  const MxMeshField &pfield( m_pmx->field(fix) );

  Vct3 pref;
  pref[0] = sbRefX->value();
  pref[1] = sbRefY->value();
  pref[2] = sbRefZ->value();

  const size_t nsec = m_isections.size();
  m_fm.resize(nsec+1, 6);

  Vct6 ftot;
  for (size_t i=0; i<m_isections.size(); ++i) {
    const MxMeshSection &sec = m_pmx->section(m_isections[i]);
    Vct6 fm = sec.integratePressure(pfield, pref);
    ftot += fm;
    for (int k=0; k<6; ++k)
      m_fm(i,k) = fm[k];

    twDisplay->setItem(i, 0, new QTableWidgetItem(qstr(sec.name())));
    for (int k=0; k<6; ++k)
      twDisplay->setItem(i, k+1,
                         new QTableWidgetItem(QString::number(fm[k], 'e', 3)));
  }

  for (int k=0; k<6; ++k)
    m_fm(nsec,k) = ftot[k];

  int n = m_isections.size();
  twDisplay->setItem(n, 0, new QTableWidgetItem(tr("Total")));
  for (int k=0; k<6; ++k)
    twDisplay->setItem(n, k+1,
                       new QTableWidgetItem(QString::number(ftot[k], 'e', 3)));
}

void ForceDisplayDialog::exportTable()
{
  if (m_pmx == nullptr)
    return;

  QString fn;
  fn = QFileDialog::getSaveFileName(this, tr("Save table to file"), lastDirectory(),
                                    tr("Text files (*.txt *.dat);; All files (*)"));

  if (fn.isEmpty())
    return;

  std::ofstream os(str(fn));
  os << "# Section    Fx    Fy    Fz    Mx    My    Mz" << std::endl;
  const int nrows = m_fm.nrows();
  for (int i=0; i<nrows; ++i) {
    if (uint(i) < m_isections.size())
      os << m_pmx->section(m_isections[i]).name() << "  ";
    else
      os << "Total      ";
    for (int k=0; k<6; ++k)
      os << m_fm(i, k) << "  ";
    os << std::endl;
  }

  lastDirectory(QFileInfo(fn).path());
}
