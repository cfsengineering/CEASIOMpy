
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
 
#include "wingsectionfitdlg.h"
#include "assembly.h"
#include "fitindicator.h"

WingSectionFitDlg::WingSectionFitDlg(QWidget *parent) :
  QDialog(parent, Qt::Tool)
{
  setupUi(this);
  connect( pbApply, SIGNAL(clicked()), this, SLOT(apply()) );
  connect( cbSelectSkeleton, SIGNAL(currentIndexChanged(int)),
           this, SLOT(showSections(int)) );

  connect( rbFitAllSurfaces, SIGNAL(clicked()),
           this, SLOT(updateIndicator()) );
  connect( cbSelectSkeleton, SIGNAL(currentIndexChanged(int)),
           this, SLOT(updateIndicator()) );
  connect( cbFitSingleSection, SIGNAL(clicked()),
           this, SLOT(updateIndicator()) );
  connect( cbSelectSection, SIGNAL(currentIndexChanged(int)),
           this, SLOT(updateIndicator()) );
  connect( sbCatchChord, SIGNAL(editingFinished()),
           this, SLOT(updateIndicator()) );
  connect( sbCatchThickness, SIGNAL(editingFinished()),
           this, SLOT(updateIndicator()) );
  connect( this, SIGNAL(rejected()),
           this, SLOT(clearIndicator()) );
}

void WingSectionFitDlg::assign(AssemblyPtr pa, FrameProjectorPtr pf,
                               FitIndicatorPtr indic)
{
  pasy = pa;
  fpj = pf;
  findic = indic;
  if (not pasy)
    return;

  cbSelectSkeleton->clear();
  const int nw = pasy->nwings();
  for (int i=0; i<nw; ++i) {
    QString s = QString::fromStdString(pasy->wing(i)->name());
    cbSelectSkeleton->addItem(s);
  }

  updateIndicator();
}

void WingSectionFitDlg::showSections(int iwing)
{
  if (not pasy)
    return;
  if (uint(iwing) > pasy->nwings())
    return;

  cbSelectSection->clear();
  WingSkeletonPtr pwng = pasy->wing(iwing);
  for (uint i=0; i<pwng->nsections(); ++i) {
    QString s = QString::fromStdString( pwng->section(i)->name() );
    cbSelectSection->addItem(s);
  }
}

void WingSectionFitDlg::selectSection(int iwing, int jsection)
{
  if (not pasy)
    return;
  else if (uint(iwing) > pasy->nwings())
    return;

  rbFitSingleSkeleton->setChecked(true);
  cbSelectSkeleton->setCurrentIndex(iwing);

  WingSkeletonPtr pwng = pasy->wing(iwing);
  if (uint(jsection) < pwng->nsections()) {
    cbFitSingleSection->setChecked(true);
    cbSelectSection->setCurrentIndex(jsection);
  } else {
    cbFitSingleSection->setChecked(false);
  }
}

void WingSectionFitDlg::apply()
{
  if (not pasy)
    return;
  if (not fpj)
    return;

  Real rChord = sbCatchChord->value();
  Real rThick = sbCatchThickness->value();

  if ( rbFitAllSurfaces->isChecked() ) {
    const int nw = pasy->nwings();
    for (int i=0; i<nw; ++i)
      pasy->wing(i)->fitSections( *fpj, rChord, rThick );
  } else {
    int iwing = cbSelectSkeleton->currentIndex();
    if (uint(iwing) > pasy->nwings())
      return;
    if (cbFitSingleSection->isChecked()) {
      int jsection = cbSelectSection->currentIndex();
      pasy->wing(iwing)->fitSection( jsection, *fpj, rChord, rThick );
    } else {
      pasy->wing(iwing)->fitSections( *fpj, rChord, rThick );
    }
  }

  emit geometryChanged();
}

void WingSectionFitDlg::updateIndicator()
{
  findic->clear();

  uint iwing = NotFound;
  uint isection = NotFound;

  if (rbFitSingleSkeleton->isChecked()) {
    iwing = cbSelectSkeleton->currentIndex();
    if (cbFitSingleSection->isChecked())
      isection = cbSelectSection->currentIndex();
  }

  Real rChord = sbCatchChord->value();
  Real rThick = sbCatchThickness->value();

  findic->markWingSection( iwing, isection, rChord, rThick );
  emit indicatorChanged();
}

void WingSectionFitDlg::clearIndicator()
{
  findic->clear();
}

void WingSectionFitDlg::changeEvent(QEvent *e)
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
