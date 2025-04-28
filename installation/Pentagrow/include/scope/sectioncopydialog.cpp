
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
 
#include "sectioncopydialog.h"
#include <genua/mxmesh.h>
#include <genua/plane.h>

#include <QCheckBox>
#include <QMessageBox>

SectionCopyDialog::SectionCopyDialog(QWidget *parent) : QDialog(parent)
{
  setupUi(this);
#ifdef Q_OS_MACX
  gbSelectSections->setFlat(true);
  gbMirrorPlane->setFlat(true);
#endif

  m_mergeThreshold->setValue( gmepsilon );
  connect( m_apply, SIGNAL(clicked()), this, SLOT(apply()) );
}

void SectionCopyDialog::assign(MxMeshPtr pmx)
{
  m_pmx = pmx;

  if (not m_pmx)
    return;

  // remove existing checkboxes
  for (int i=0; i<m_boxes.size(); ++i)
    m_sectionLayout->removeWidget( m_boxes[i] );
  qDeleteAll(m_boxes);
  m_boxes.clear();

  // create new check boxes
  for (uint i=0; i<m_pmx->nsections(); ++i) {
    QCheckBox *box = new QCheckBox(this);
    box->setText( QString::fromStdString(m_pmx->section(i).name()) );
    m_boxes.append(box);
    m_sectionLayout->addWidget( box );
  }

  adjustSize();
}

void SectionCopyDialog::apply()
{
  if (not m_pmx)
    return;

  Vct3 nrm, pivot;
  nrm[0] = sbNrmX->value();
  nrm[1] = sbNrmY->value();
  nrm[2] = sbNrmZ->value();
  if (sq(nrm) == 0.0) {
    QString title = tr("Invalid data");
    QString text = tr("Normal vector for mirror plane must "
                      "have non-zero length.");
    QMessageBox::warning(this, title, text);
    return;
  }

  normalize(nrm);
  pivot[0] = sbCtrX->value();
  pivot[1] = sbCtrY->value();
  pivot[2] = sbCtrZ->value();
  Plane pln( nrm, dot(nrm, pivot));

  Indices snodes, mcs;
  bool bMerge = m_mergeSection->isChecked();
  for (int i=0; i<m_boxes.size(); ++i) {
    Indices tmp;
    if (m_boxes[i]->isChecked()) {
      m_stage->setText(tr("Creating mirror copy for section %1...")
                       .arg(m_boxes[i]->text()));
      // uint icp = m_pmx->mirrorCopySection( i, pln, bMerge );
      // if (not bMerge)
      //  m_pmx->section(icp).rename( m_pmx->section(i).name() + "-MirrorCopy" );
      mcs.push_back(i);
      tmp.clear();
      m_pmx->section(i).usedNodes(tmp);
      if (snodes.empty()) {
        snodes = tmp;
      } else {
        size_t mid = snodes.size();
        snodes.insert(snodes.end(), tmp.begin(), tmp.end());
        std::inplace_merge(snodes.begin(), snodes.begin()+mid, snodes.end());
      }
    }
  }

  m_stage->setText(tr("Creating mirror copies for all used nodes."));
  uint voff = m_pmx->mirrorCopyNodes(snodes, pln);
  for (uint i=0; i<mcs.size(); ++i) {
    m_stage->setText(tr("Creating mirror copy for section %1...")
                     .arg(m_boxes[mcs[i]]->text()));
    uint icp = m_pmx->mirrorCopySection(mcs[i], voff, snodes, bMerge);
    if (not bMerge)
      m_pmx->section(icp).rename( m_pmx->section(mcs[i]).name()
                                  + "-MirrorCopy" );
  }

  m_stage->setText(tr("Done."));

  if (m_mergeNodes->isChecked()) {
    Real thr = m_mergeThreshold->value();
    m_stage->setText(tr("Merging duplicate vertices..."));
    m_pmx->mergeNodes( thr );
    m_stage->setText(tr("Dropping unused vertices..."));
    m_pmx->dropUnusedNodes();
  }

  emit meshChanged();
}

void SectionCopyDialog::changeEvent(QEvent *e)
{
  QDialog::changeEvent(e);
  switch (e->type()) {
  case QEvent::LanguageChange:
    retranslateUi(this);
    break;
  default:
    break;
  }
}
