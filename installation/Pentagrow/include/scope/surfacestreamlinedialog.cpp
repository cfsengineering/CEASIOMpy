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

#include "surfacestreamlinedialog.h"
#include "ui_surfacestreamlinedialog.h"
#include "util.h"
#include <genua/mxmesh.h>
#include <genua/rng.h>
#include <QFileDialog>
#include <fstream>

SurfaceStreamlineDialog::SurfaceStreamlineDialog(QWidget *parent) :
  QDialog(parent),
  m_ui(new Ui::SurfaceStreamlineDialog)
{
  m_ui->setupUi(this);

  connect(m_ui->pbApply, SIGNAL(clicked()),
          this, SLOT(apply()) );
  connect(m_ui->pbExport, SIGNAL(clicked()),
          this, SLOT(exportLines()) );
  connect(m_ui->pbLineColor, SIGNAL(clicked()),
          this, SIGNAL(requestColorChange()));
  connect(m_ui->cbShowStreamlines, SIGNAL(toggled(bool)),
          this, SIGNAL(streamlinesChanged(bool)));

  m_ui->pbExport->setEnabled(false);
}

SurfaceStreamlineDialog::~SurfaceStreamlineDialog()
{
  qDeleteAll(m_box);
  m_box.clear();
  delete m_ui;

  // TODO: save UI settings
}

void SurfaceStreamlineDialog::assign(MxMeshPtr pmx)
{
  m_dirty &= (pmx.get() != m_pmx.get());
  m_pmx = pmx;
  if (m_pmx == nullptr)
    return;

  qDeleteAll(m_box);
  m_box.clear();

  m_ivf.clear();
  m_ui->cbSelectField->clear();
  for (uint i=0; i<m_pmx->nfields(); ++i) {
    const MxMeshField &f(m_pmx->field(i));
    if (f.nodal() and f.ndimension() == 3) {
      m_ivf.push_back(i);
      m_ui->cbSelectField->addItem(qstr(f.name()));
    }
  }

  const int nitem = m_ui->sectionLayout->count();
  for (int i=0; i<nitem; ++i)
    m_ui->sectionLayout->removeItem(  m_ui->sectionLayout->itemAt(i)  );

  for (uint i=0; i<m_pmx->nsections(); ++i) {
    const MxMeshSection &s(m_pmx->section(i));
    if (s.surfaceElements()) {
      QPointer<QCheckBox> box = new QCheckBox(this);
      box->setText(qstr(s.name()));
      m_box.append(box);
      m_ui->sectionLayout->addWidget(box);
    }
  }


}

void SurfaceStreamlineDialog::apply()
{
  if (m_pmx == nullptr)
    return;

  uint nedges = 0;
  if (m_ui->cbUseAllSurfaces->isChecked()) {
    nedges = m_ssf.surfacesFromMesh(*m_pmx);
  } else {
    for (int i=0; i<m_box.size(); ++i) {
      if (m_box[i]->isChecked()) {
        uint isec = m_pmx->findSection(str(m_box[i]->text()));
        if (isec != NotFound)
          m_ssf.addSection(m_pmx->section(isec));
      }
    }
    nedges = m_ssf.fixate(*m_pmx);
  }

  if (nedges == 0)
    return;

  int fix = m_ui->cbSelectField->currentIndex();
  if (fix < 0)
    return;
  m_ssf.extractField( m_pmx->field(m_ivf[fix]) );
  m_ssf.permittedCrossings( m_ui->sbPermittedCrossings->value() );
  uint nlines = m_ui->sbNumberOfLines->value();
  uint minlen = m_ui->sbMinPointCount->value();
  m_ssf.storeRandomLines(nlines, minlen);

  emit postStatusMessage(tr("%1 streamlines computed.").arg(m_ssf.size()));
  emit streamlinesChanged(m_ui->cbShowStreamlines->isChecked());
  m_ui->pbExport->setEnabled( m_ssf.size() > 0 );
}

void SurfaceStreamlineDialog::exportLines()
{
  QString fn = QFileDialog::getSaveFileName(this, tr("Select base name"));
  if (fn.isEmpty())
    return;

  std::string bname = str(fn);
  const int nlines = m_ssf.size();
  for (int i=0; i<nlines; ++i) {
    std::ofstream os(bname + str(i+1) + ".txt");
    os << m_ssf[i];
    os.close();
  }
}


