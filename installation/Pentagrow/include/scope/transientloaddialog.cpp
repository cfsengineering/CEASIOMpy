
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
 
#include "transientloaddialog.h"
#include "ploaddialog.h"
#include "util.h"
#include <genua/xmlelement.h>
#include <QTextStream>
#include <QFileDialog>
#include <QFileInfo>
#include <QFile>
#include <sstream>

using namespace std;

TransientLoadDialog::TransientLoadDialog(QWidget *parent) :
  QDialog(parent), cplDlg(0)
{
  setupUi(this);

  // connect buttons
  connect(pbProceed, SIGNAL(clicked()), this, SLOT(proceed()));
  connect(pbBrowseHistory, SIGNAL(clicked()), this, SLOT(browseHistory()));
  connect(pbLoadSettings, SIGNAL(clicked()), this, SLOT(loadSettings()));
  connect(pbStoreSettings, SIGNAL(clicked()), this, SLOT(storeSettings()));

  // UI elements
  connect(sbStateIndex, SIGNAL(valueChanged(int)),
          this, SLOT(stateSelectionChanged(int)));
  connect(cbSelectField, SIGNAL(currentIndexChanged(int)),
          this, SLOT(fieldSelectionChanged(int)));
}

void TransientLoadDialog::assign(MxMeshPtr am)
{
  timeSteps.clear();
  rawHistory.clear();
  stateMap.clear();

  amesh = am;
  if (not amesh)
    return;

  bool dwfsSolution = false;

  cbSelectField->clear();
  cbSelectField->addItem(tr("Not mapped"));
  cpCandFields.clear();
  for (uint i=0; i<amesh->nfields(); ++i) {
    const MxMeshField & f( amesh->field(i) );
    if (not f.nodal())
      continue;
    if ( (not f.realField()) or (f.ndimension() != 1))
      continue;

    // detect dwfs solution, reduce number of fields shown
    const string & fn(f.name());
    if (fn.find("Re(cp) mode ") != string::npos)
      dwfsSolution = true;

    if ( dwfsSolution and
         (fn.find("Re(cp) mode") == string::npos
           or fn.find("k = 0 ") == string::npos) )
      continue;

    cpCandFields.push_back(i);
    cbSelectField->addItem(QString::fromStdString(f.name()));
  }
  cbSelectField->setCurrentIndex(0);

  sbStateIndex->setEnabled(false);
}

void TransientLoadDialog::browseHistory()
{
  QString fn, filter;
  filter = tr("Plain text files (*.txt *.dat);;"
              "All files (*)");
  fn = QFileDialog::getOpenFileName(this, tr("Open state history file"),
                                    lastdir, filter);
  if (fn.isEmpty())
    return;
  lastdir = QFileInfo(fn).absolutePath();
  leHistoryFile->setText(fn);

  parseHistory();
}

void TransientLoadDialog::parseHistory()
{
  QString fname = leHistoryFile->text();
  if (fname.isEmpty())
    return;

  // extract time steps and raw history
  timeSteps.clear();
  rawHistory.clear();

  Real t;
  Vector tmp;
  QString line;
  QFile file(fname);
  file.open( QIODevice::ReadOnly );
  QTextStream stream(&file);
  while (not stream.atEnd()) {
    line = stream.readLine();
    stringstream ss;
    ss.str( str(line) );
    ss >> t;
    timeSteps.push_back(t);
    tmp.clear();
    while (ss >> t)
      tmp.push_back( t );
    rawHistory.push_back(tmp);
  }

  sbStateIndex->setEnabled( nstate() > 0 );
  sbStateIndex->setMinimum(1);
  sbStateIndex->setMaximum( nstate() );
  sbStateIndex->setValue(1);

  stateMap.resize(nstate(), NotFound);

  // update status display
  lbTimeSteps->setText( QString::number(timeSteps.size()) );
  lbStates->setText( QString::number(nstate()) );
}

void TransientLoadDialog::proceed()
{
  if (timeSteps.empty() or nstate() == 0)
    return;

  // fields to use
  Indices ifields, iuse;

  const int nraw = stateMap.size();
  for (int i=0; i<nraw; ++i) {
    if (stateMap[i] != NotFound) {
      iuse.push_back(i);
      ifields.push_back( cpCandFields[stateMap[i]] );
    }
  }

  // dynamic pressure
  Real q = sbDynamicPressure->value();

  const int ntime = timeSteps.size();
  const int nuse = ifields.size();
  if (nuse == 0)
    return;

  VectorArray xt( ntime );
  Vector tmp(nuse);
  for (int i=0; i<ntime; ++i) {
    for (int j=0; j<nuse; ++j)
      tmp[j] = q*rawHistory[i][iuse[j]];
    xt[i] = tmp;
  }

  // open pressure mapping dialog
  if (cplDlg == 0)
    cplDlg = new PLoadDialog(this);

  cplDlg->defaultDirectory( lastdir );
  cplDlg->assign(amesh, ifields, timeSteps, xt);
  cplDlg->show();
}

void TransientLoadDialog::stateSelectionChanged(int istate)
{
  if (istate < 0 or istate >= (int) stateMap.size())
    return;

  uint ifield = stateMap[istate];
  if (ifield == NotFound)
    cbSelectField->setCurrentIndex(0);
  else
    cbSelectField->setCurrentIndex( ifield+1 );
}

void TransientLoadDialog::fieldSelectionChanged(int ifield)
{
  if (ifield < 0 or ifield-1 >= (int) cpCandFields.size())
    return;

  int istate = sbStateIndex->value();
  if (istate < 0 or istate >= (int) stateMap.size())
    return;

  if (ifield == 0)
    stateMap[istate] = NotFound;
  else
    stateMap[istate] = ifield-1;
}

void TransientLoadDialog::storeSettings()
{
  QString filter = tr("Settings (*.xml);; All files (*)");
  QString fn = QFileDialog::getSaveFileName(this, tr("Save settings to..."),
                                            lastdir, filter);
  if (fn.isEmpty())
    return;

  lastdir = QFileInfo(fn).absolutePath();

  XmlElement xe("StateFieldMapping");
  if (not cpCandFields.size()) {
    XmlElement xf("CpFieldIndex");
    xf["count"] = cpCandFields.size();
    xf.asBinary(cpCandFields.size(), &cpCandFields[0], true);
    xe.append(xf);
  }
  if (not stateMap.empty()) {
    XmlElement xf("StateMap");
    xf["count"] = stateMap.size();
    xf.asBinary(stateMap.size(), &stateMap[0], true);
    xe.append(xf);
  }

  xe.write( str(fn), XmlElement::PlainText );
}

void TransientLoadDialog::loadSettings()
{
  if (not amesh)
    return;

  QString filter = tr("Settings (*.xml);; All files (*)");
  QString fn = QFileDialog::getOpenFileName(this, tr("Load settings from..."),
                                            lastdir, filter);
  if (fn.isEmpty())
    return;

  lastdir = QFileInfo(fn).absolutePath();

  XmlElement xe;
  xe.read( str(fn) );

  if (xe.name() != "StateFieldMapping")
    return;

  stateMap.clear();
  cpCandFields.clear();

  XmlElement::const_iterator itr;
  itr = xe.findChild("CpFieldIndex");
  if (itr != xe.end()) {
    cpCandFields.resize( Int(itr->attribute("count")) );
    itr->fetch(cpCandFields.size(), &cpCandFields[0]);
  }

  // check whether this makes sense
  for (uint i=0; i<cpCandFields.size(); ++i) {
    if (cpCandFields[i] >= amesh->nfields()) {
      cpCandFields.clear();
      return;
    }
  }

  itr = xe.findChild("StateMap");
  if (itr != xe.end()) {
    stateMap.resize( Int(itr->attribute("count")) );
    itr->fetch(stateMap.size(), &stateMap[0]);
  }

  // sanity check
  for (uint i=0; i<stateMap.size(); ++i) {
    if (stateMap[i] == NotFound)
      continue;
    if (stateMap[i] >= cpCandFields.size()) {
      cpCandFields.clear();
      stateMap.clear();
      return;
    }
  }

  // TODO : generate error messages when settings do not match
  //        loaded aerodynamic mesh.

}

void TransientLoadDialog::changeEvent(QEvent *e)
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
