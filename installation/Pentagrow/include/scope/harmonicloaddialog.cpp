
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
 
#include "harmonicloaddialog.h"
#include "ploaddialog.h"
#include "util.h"

using namespace std;

HarmonicLoadDialog::HarmonicLoadDialog(QWidget *parent) :
  QDialog(parent, Qt::Tool), cplDlg(0)
{
  setupUi(this);
  twFields->horizontalHeader()->setStretchLastSection(true);

  // connect buttons
  connect(pbExtract, SIGNAL(clicked()), this, SLOT(extractFields()));
  connect(pbProceed, SIGNAL(clicked()), this, SLOT(proceed()));

}

void HarmonicLoadDialog::assign(MxMeshPtr am)
{
  amesh = am;
  cpFields.clear();
  redFreq.clear();
}

void HarmonicLoadDialog::extractFields()
{
  twFields->clear();
  redFreq.clear();
  cpFields.clear();;

  bool isRe, isIm;
  string tag = str(leModeTag->text());
  const string kkey = "k = ";
  for (uint i=0; i<amesh->nfields(); ++i) {
    const string & fn( amesh->field(i).name() );
    isRe = fn.find("Re(cp)") != string::npos;
    isIm = fn.find("Im(cp)") != string::npos;
    if (not (isRe or isIm))
      continue;

    string::size_type pos = fn.find(kkey);
    if (pos == string::npos)
      continue;
    Real k = Float( fn.substr(pos + kkey.length()) );
    if (fn.find(tag) != string::npos) {
      cpFields.push_back(i);
      redFreq.push_back(k);
    }
  }

  // fill table
  const int nfield = cpFields.size();
  twFields->setRowCount( cpFields.size() );
  twFields->setColumnCount(3);
  twFields->setHorizontalHeaderItem(0, new QTableWidgetItem(tr("Index")));
  twFields->setHorizontalHeaderItem(1, new QTableWidgetItem(tr("Field")));
  twFields->setHorizontalHeaderItem(2, new QTableWidgetItem(tr("Frequency")));

  for (int i=0; i<nfield; ++i) {
    const string & fn = amesh->field(cpFields[i]).name();
    twFields->setItem(i, 0,
                      new QTableWidgetItem(QString::number(cpFields[i])));
    twFields->setItem(i, 1,
                      new QTableWidgetItem(QString::fromStdString(fn)));
    twFields->setItem(i, 2,
                      new QTableWidgetItem(QString::number(redFreq[i])));
  }

  twFields->resizeColumnsToContents();
  twFields->adjustSize();
  adjustSize();
}

void HarmonicLoadDialog::proceed()
{
  Real chord = sbRefChord->value();
  Real speed = sbRefSpeed->value();

  // frequency list must be in Hz for nastran
  const int nfr = redFreq.size() / 2;
  Vector freq(nfr);
  for (int i=0; i<nfr; ++i)
    freq[i] = speed*redFreq[2*i]/(M_PI*chord);

  if (freq.empty())
    return;

  if (cplDlg == 0)
    cplDlg = new PLoadDialog(this);

  cplDlg->harmonic(amesh, cpFields, freq);
  cplDlg->show();
}

void HarmonicLoadDialog::changeEvent(QEvent *e)
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
