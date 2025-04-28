
/* ------------------------------------------------------------------------
 * file:       cseditorwidget.cpp
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Modeless control surface editor
 * ------------------------------------------------------------------------ */
 
#include <QPushButton>
#include <QComboBox>
#include <QSpinBox>
#include <QTableWidget>
#include <QMessageBox>

#include "util.h"
#include "assembly.h"
#include "ctsystem.h"
#include "cseditorwidget.h"

using namespace std;

CsEditorWidget::CsEditorWidget(QWidget *parent, Assembly & a) : 
    QDialog(parent), asy(a), showing(false)
{
  setupUi(this);
  retranslateUi(this);
  QDialog::setModal(false);
  QDialog::setAttribute(Qt::WA_DeleteOnClose);
  
  // fill components 
  init();
  
  // make name column in pattern table read-only
  // tablePattern->setColumnReadOnly(0, true);
  
  connect( pbNewFlap, SIGNAL(released()), this, SLOT(newFlap()) );
  connect( pbMirrorCopy, SIGNAL(released()), this, SLOT(mirrorFlap()) );
  connect( pbDeleteFlap, SIGNAL(released()), this, SLOT(deleteFlap()) );
  connect( pbNewHinge, SIGNAL(released()), this, SLOT(addHingepoint()) );
  
  connect( rbTrailingEdge, SIGNAL(released()), this, SLOT(changeFlapType()) );
  connect( rbLeadingEdge, SIGNAL(released()), this, SLOT(changeFlapType()) );
  
  connect( cbFlapName, SIGNAL(activated(int)), 
           this, SLOT(showFlap(int)) );
  connect( cbFlapName, SIGNAL(editTextChanged(const QString&)),
           this, SLOT(renameFlap(const QString&)) );
  connect( cbSelectWing, SIGNAL(activated(int)), 
           this, SLOT(changeWing(int)) );
  connect( sbEditHinge, SIGNAL(valueChanged(int)), 
           this, SLOT(showHingepoint(int)) );
  connect( sbSpanwisePos, SIGNAL(editingFinished()), 
           this, SLOT(changeHingepoint()) );
  connect( sbChordwisePos, SIGNAL(editingFinished()), 
           this, SLOT(changeHingepoint()) );
  
  connect( pbNewPattern, SIGNAL(released()), this, SLOT(newPattern()) );
  connect( pbDeletePattern, SIGNAL(released()), this, SLOT(deletePattern()) );
  
  connect( pbClose, SIGNAL(released()), this, SLOT(close()) );
  
  connect( cbPattern, SIGNAL(activated(int)), 
           this, SLOT(showPattern(int)) );
  connect( cbPattern, SIGNAL(editTextChanged(const QString&)),
           this, SLOT(renamePattern(const QString&)) );
  connect( tablePattern, SIGNAL(cellChanged(int, int)), 
           this, SLOT(changePattern(int, int)) );
  
  // update patterns when switching views 
  connect( tabContainer, SIGNAL(currentChanged(int)), 
           this, SLOT(tabChanged(int)) );
  
  // make control system visible 
  asy.ctsystem().updateGeometry();
  asy.ctsystem().toggleVisible(true);

  if (asy.ctsystem().nsurf() > 0)
    showFlap(0);
  if (asy.ctsystem().npattern() > 0)
    showPattern(0);
}

CsEditorWidget::~CsEditorWidget()
{
  asy.ctsystem().toggleVisible(false);
  emit geometryChanged();
}

void CsEditorWidget::init()
{
  // fill wing surface list 
  const int nw(asy.nwings());
  
  for (int i=0; i<nw; ++i) 
    cbSelectWing->addItem( QString::fromStdString(asy.wing(i)->name()) );
  
  // fill control surface names 
  CtSystem & csys(asy.ctsystem());
  const int nsf(csys.nsurf());
  for (int i=0; i<nsf; ++i)
    cbFlapName->addItem( QString::fromStdString(csys.surface(i).name()) );
   
  // enter pattern names 
  const int np(csys.npattern());
  for (int i=0; i<np; ++i)
    cbPattern->addItem( QString::fromStdString(csys.pattern(i).name()) );
}

bool CsEditorWidget::close()
{
  CtSystem & csys(asy.ctsystem());
  csys.toggleVisible(false);
  emit geometryChanged();
  return QDialog::close();
}

void CsEditorWidget::showHingepoint(int i)
{
  CtSystem & csys(asy.ctsystem());
  if (csys.nsurf() == 0 or i <= 0)
    return;
  
  --i;
  int isf = cbFlapName->currentIndex();
  const CtSurface & cs(csys.surface(isf));
  
  sbSpanwisePos->setValue( cs.spanwisePosition(i) );
  sbChordwisePos->setValue( cs.chordwisePosition(i) );
  sbEditHinge->setValue(i+1);
}

void CsEditorWidget::addHingepoint()
{
  CtSystem & csys(asy.ctsystem());
  if (csys.nsurf() == 0)
    return;
  
  int ipos, isf = cbFlapName->currentIndex();
  CtSurface & cs(csys.surface(isf));
  
  // remove surface from patterns
  const int np = csys.npattern();
  for (int i=0; i<np; ++i)
    csys.pattern(i).remove( cs.name() ); 
  
  Real yp(0.0), xp(0.75);
  if (rbLeadingEdge->isChecked())
    xp = 0.25;
  
  // try to guess a value for yp 
  yp = 0.5*(cs.spanwisePosition(0) + cs.spanwisePosition(1));
  
  ipos = cs.addHingepoint(yp, xp);
  sbEditHinge->setMaximum(cs.nhinges());
  showHingepoint( ipos+1 );
  emit geometryChanged();
}

void CsEditorWidget::changeHingepoint()
{
  CtSystem & csys(asy.ctsystem());
  if (csys.nsurf() == 0)
    return;
  
  int isf = cbFlapName->currentIndex();
  CtSurface & cs(csys.surface(isf));
  int ihp = sbEditHinge->value() - 1;
  Real spos = sbSpanwisePos->value();
  Real cpos = sbChordwisePos->value();
  ihp = cs.changeHingepoint(ihp, spos, cpos) + 1;
  showHingepoint(ihp); 
  emit geometryChanged();
}

void CsEditorWidget::showFlap(int i)
{
  CtSystem & csys(asy.ctsystem());
  if (csys.nsurf() == 0 or i < 0)
    return;
  
  showing = true;
  const CtSurface & cs(csys.surface(i));
  int iw = cbSelectWing->findText( QString::fromStdString(cs.wing()) );
  assert(iw >= 0);
  cbFlapName->setCurrentIndex(i);
  cbFlapName->setItemText(i, QString::fromStdString(cs.name()) );
  cbSelectWing->setCurrentIndex(iw);
  
  switch (cs.type()) {
    case CtSurface::CsTef:
      rbTrailingEdge->setChecked(true);
      rbLeadingEdge->setChecked(false);
      break;
    case CtSurface::CsLef:
      rbTrailingEdge->setChecked(false);
      rbLeadingEdge->setChecked(true);
      break;
  }
    
  sbEditHinge->setMaximum(cs.nhinges());
  showHingepoint(1);
  showing = false;
}

void CsEditorWidget::newFlap()
{
  CtSystem & csys(asy.ctsystem());
  uint idx = csys.nsurf();
  string name = "UndefinedFlap" + str(idx+1);
  
  int iw = cbSelectWing->currentIndex();
  CtSurface s(asy.wing(iw));
  s.rename(name);
  idx = csys.append(s);
  cbFlapName->insertItem( idx, QString::fromStdString(name) );
  cbFlapName->setCurrentIndex( idx );
  showFlap( idx );
  emit geometryChanged();
}
    
void CsEditorWidget::mirrorFlap()
{  
  CtSystem & csys(asy.ctsystem());
  if (csys.nsurf() == 0)
    return;
  
  uint idx = cbFlapName->currentIndex();
  CtSurface mc = csys.surface(idx).mirrorCopy();
  uint imc = csys.append(mc);
  cbFlapName->insertItem(imc, QString::fromStdString(mc.name()));
  cbFlapName->setCurrentIndex( imc );
  showFlap( imc );  
  emit geometryChanged();
}
    
void CsEditorWidget::renameFlap(const QString &s)
{
  CtSystem & csys(asy.ctsystem());
  if (showing or csys.nsurf() == 0)
    return;
  
  int isf = cbFlapName->currentIndex();
  CtSurface & cs(csys.surface(isf));
  cs.rename(str(s));
  cbFlapName->setItemText(isf, s);
}
    
void CsEditorWidget::changeFlapType()
{
  CtSystem & csys(asy.ctsystem());
  if (csys.nsurf() == 0)
    return;
  
  int isf = cbFlapName->currentIndex();
  CtSurface & cs(csys.surface(isf));
  if (rbLeadingEdge->isChecked())
    cs.type( CtSurface::CsLef );
  else 
    cs.type( CtSurface::CsTef );
  cs.updateGeometry();
  emit geometryChanged();
}
    
void CsEditorWidget::deleteFlap()
{
  CtSystem & csys(asy.ctsystem());
  if (csys.nsurf() == 0)
    return;
  
  int idx = cbFlapName->currentIndex();
  csys.removeSurface(idx);
  cbFlapName->removeItem(idx);
  if (csys.nsurf() > 0) {
    if (idx > 0) {
      cbFlapName->setCurrentIndex(idx-1);
      showFlap(idx-1);
    } else {
      cbFlapName->setCurrentIndex(0);
      showFlap(0);  
    }
  } 
  
  // redraw 
  emit geometryChanged();
  
  // need to update pattern table, too!
  if (csys.npattern() > 0) 
    showPattern(cbPattern->currentIndex());
}

void CsEditorWidget::changeWing(int iw)
{
  CtSystem & csys(asy.ctsystem());
  if (csys.nsurf() == 0)
    return;
  
  uint isf = cbFlapName->currentIndex();
  csys.surface(isf).attachTo(asy.wing(iw));
  emit geometryChanged();
}

void CsEditorWidget::showPattern(int ipat)
{
  const CtSystem & csys(asy.ctsystem());
  if (csys.npattern() == 0 or ipat < 0)
    return; 

  showing = true;
  
  // activate entry in combo box 
  cbPattern->setCurrentIndex(ipat);
  
  // collect segment names 
  StringArray segments;
  StringArray::iterator pos;
  csys.segments(segments);
  
  // table flag settings
  QTableWidgetItem *item;
  Qt::ItemFlags nflags, fflags;
  nflags  = Qt::ItemIsEnabled;
  fflags  = Qt::ItemIsSelectable;
  fflags |= Qt::ItemIsEditable;
  fflags |= Qt::ItemIsEnabled;
  
  // fill columns 
  const CtPattern & cp(csys.pattern(ipat));
  const int nseg(segments.size());
  tablePattern->setRowCount(nseg);
  for (int i=0; i<nseg; ++i) {
    item = new QTableWidgetItem(QString::fromStdString(segments[i]));
    item->setFlags(nflags);
    tablePattern->setItem(i, 0, item);
    item = new QTableWidgetItem("0.000");
    item->setFlags(fflags);
    item->setTextAlignment(Qt::AlignRight);
    tablePattern->setItem(i, 1, item);
  }
  
  // set nonzero columns 
  Real f;
  string s;
  const int nnz(cp.npart());
  for (int i=0; i<nnz; ++i) {
    cp.get(i, s, f);
    pos = std::find(segments.begin(), segments.end(), s);
    if (pos == segments.end())
      continue;
    int irow = std::distance(segments.begin(), pos);
    tablePattern->item(irow, 1)->setText(QString::number(f, 'f', 3));
  }
  showing = false;
}

void CsEditorWidget::newPattern()
{
  CtSystem & csys(asy.ctsystem());
  if (csys.nsurf() == 0)
    return;
  
  const int np(csys.npattern());
  
  string pname = "Pattern" + str(np+1);
  CtPattern cp;
  cp.rename(pname);
  int idx = csys.append(cp);  
  cbPattern->insertItem(idx, QString::fromStdString(pname));
  showPattern( idx );
}
       
void CsEditorWidget::changePattern(int row, int col)
{
  CtSystem & csys(asy.ctsystem());
  if (showing or col == 0 or csys.npattern() == 0)
    return;
  
  bool ok(true);
  Real f = tablePattern->item(row, 1)->text().toDouble(&ok);
  if (not ok)
    return;
  
  StringArray segments;
  csys.segments( segments );
  
  int ipat = cbPattern->currentIndex();
  CtPattern & cp(csys.pattern(ipat));
  uint ics = cp.find(segments[row]);
  if (ics == NotFound)
    cp.append(segments[row], f);
  else 
    cp.set(ics, segments[row], f);
    
  showPattern(ipat);
}
       
void CsEditorWidget::deletePattern()
{
  CtSystem & csys(asy.ctsystem());
  if (csys.npattern() == 0)
    return;  
  
  int ipat = cbPattern->currentIndex();
  csys.removePattern( ipat );
  cbPattern->removeItem(ipat);
  if (csys.npattern() > 0) {
    if (ipat > 0) {
      showPattern(ipat-1);
    } else {
      showPattern(0);  
    }
  } else {
    tablePattern->setRowCount(0);
  }
}

void CsEditorWidget::renamePattern(const QString &s)
{
  CtSystem & csys(asy.ctsystem());
  if (showing or csys.npattern() == 0)
    return;
  
  int ipat = cbPattern->currentIndex();
  CtPattern & cp(csys.pattern(ipat));
  cp.rename(str(s));
  cbPattern->setItemText(ipat, s);
}

void CsEditorWidget::tabChanged(int itab)
{
  CtSystem & csys(asy.ctsystem());
  if (itab == 1) {
    if (csys.nsurf() == 0) {
      cbPattern->clear();
      tablePattern->setRowCount(0);
    }
  }
}
