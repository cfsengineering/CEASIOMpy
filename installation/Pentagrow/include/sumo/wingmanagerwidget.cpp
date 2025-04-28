
/* ------------------------------------------------------------------------
 * file:       wingmanagerwidget.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Manages user input for wing skeleton modification
 * ------------------------------------------------------------------------ */

#include <QListWidget>
#include <QCheckBox>
#include <QRadioButton>
#include <QLabel>
#include <QPushButton>
#include <QLineEdit>
#include <QColorDialog>

#include "ui_wingstat.h"
#include "sectioneditor.h"
#include "wingmanagerwidget.h"
#include "wingskeleton.h"

using namespace std;

// ------------------ WingStat ------------------------------

class WingStat : public QDialog, public Ui::WingStat
{
  public:
    
   WingStat(QWidget *parent, const WingSkeletonPtr & w) : 
      QDialog(parent), wsp(w)
   {
      setupUi(this);
      retranslateUi(this);
      
      // set text for statistics 
      lbArea->setText( QString::number(wsp->referenceArea(), 'g', 4) );
      lbChord->setText( QString::number(wsp->geoMeanChord(), 'g', 4) );
      lbSpan->setText( QString::number(wsp->referenceSpan(), 'g', 4) );
      lbMac->setText( QString::number(wsp->aeroMeanChord(), 'g', 4) );
      lbRmin->setText( QString::number(wsp->minRadius(), 'e', 4) );
    }
    
  private:
    
    WingSkeletonPtr wsp;
};

// ------------- WingManagerWidget ------------------------------------------------

WingManagerWidget::WingManagerWidget(QWidget *parent, WingSkeletonPtr sp)
  : QDialog(parent), wsp(sp)
{
  // initialize GUI 
  setupUi( this );
  retranslateUi( this );
  
  // fill in available data
  leName->setText(wsp->name().c_str());
  
  cbAutoSym->setChecked( wsp->autoSym() );
  cbDetectWinglet->setChecked( wsp->detectWinglet() );
  rbCubic->setChecked( wsp->cubicInterpolation() );
  cbVisible->setChecked( wsp->visible() );
  
  const Vct3 & org(wsp->origin());
  const Vct3 & rot(wsp->rotation());
  
//   QLocale lcd;
//   lePosX->setText(lcd.toString(org[0]));
//   lePosX->setValidator(new QDoubleValidator(-1e18, 1e18, 6, lePosX));
//   
//   lePosY->setText(lcd.toString(org[1]));
//   lePosY->setValidator(new QDoubleValidator(-1e18, 1e18, 6, lePosY));
//   
//   lePosZ->setText(lcd.toString(org[2]));
//   lePosZ->setValidator(new QDoubleValidator(-1e18, 1e18, 6, lePosZ));
//   
//   leRotX->setText(lcd.toString( deg(rot[0])) );
//   leRotX->setValidator(new QDoubleValidator(-1e18, 1e18, 6, leRotX));
//   
//   leRotY->setText(lcd.toString( deg(rot[1])) );
//   leRotY->setValidator(new QDoubleValidator(-1e18, 1e18, 6, leRotY));
  
  adapt(sbPosX, org[0]);
  adapt(sbPosY, org[1]);
  adapt(sbPosZ, org[2]);
  
  adapt(sbRotX, deg(rot[0]));
  adapt(sbRotY, deg(rot[1]));
  adapt(sbRotZ, deg(rot[2]));
  
  sbRightCap->setValue( wsp->southCapHeight() );
  sbLeftCap->setValue( wsp->northCapHeight() );
  
  updateList();

  // widget connections
  connect( listSection, SIGNAL(currentRowChanged(int)),
           this, SLOT(sectionSelectionChanged(int)) );

  connect( this, SIGNAL(geometryChanged()), SLOT(updateList()) );
  connect( cbAutoSym, SIGNAL(toggled(bool)), SLOT(buildFlagSwitched(bool)) );
  connect( cbDetectWinglet, SIGNAL(toggled(bool)), SLOT(buildFlagSwitched(bool)) );
  connect( rbLinear, SIGNAL(toggled(bool)), SLOT(buildFlagSwitched(bool)) );
  connect( rbCubic, SIGNAL(toggled(bool)), SLOT(buildFlagSwitched(bool)) );

  // buttons
  connect( pbNewSection, SIGNAL(clicked()), SLOT(newSection()) );
  connect( pbEditSection, SIGNAL(clicked()), SLOT(editSection()) );
  connect( pbRemoveSection, SIGNAL(clicked()), SLOT(removeSection()) );
  connect( pbMoveUp, SIGNAL(clicked()), this, SLOT(moveSectionUp()) );
  connect( pbMoveDown, SIGNAL(clicked()), this, SLOT(moveSectionDown()) );
  connect( pbSortSections, SIGNAL(clicked()), this, SLOT(sortSections()) );

  connect( pbTransform, SIGNAL(clicked()), SLOT(rebuildWing()) );
  connect( pbChangeColor, SIGNAL(clicked()), SLOT(changeColor()) );
  connect( pbClose, SIGNAL(clicked()), SLOT(saveAndClose()) );
  connect( pbStat, SIGNAL(clicked()), SLOT(showStats()) );

  // delete object on close()
  QDialog::setAttribute(Qt::WA_DeleteOnClose);
}

uint WingManagerWidget::selectedSection()
{
  return listSection->currentRow();
}

void WingManagerWidget::saveAndClose()
{
  rebuildWing();
  close();
}

void WingManagerWidget::updateList()
{
  listSection->clear();
  const uint ns(wsp->nsections());
  for (uint i=0; i<ns; ++i) {
    QString s( wsp->section(i)->name().c_str() );
    listSection->addItem( s );
  }
}

void WingManagerWidget::newSection()
{
  WingSectionPtr afp(new WingSection);
  afp->rename("Section"+str(wsp->nsections()+1));

  // section insertion location
  int isec = listSection->currentRow();

  // open section editing dialog and process
  bool ok;
  SectionEditor dlg(this, afp);
  if (dlg.exec() == QDialog::Accepted) {
    ok = dlg.process();
    if (ok) {
      if (uint(isec)+1 >= wsp->nsections())
        wsp->addSection(afp);
      else
        wsp->insertSection(isec+1, afp);
      rebuildWing();
    }
  } 
}

void WingManagerWidget::editSection()
{
  uint idx = selectedSection();
  if (idx == NotFound)
    return;

  bool ok;
  WingSectionPtr afp(wsp->section(idx));
  SectionEditor dlg(this, afp);
  if (dlg.exec() == QDialog::Accepted) {
    ok = dlg.process();
    if (ok) {
      rebuildWing();
    } 
  } 
}

void WingManagerWidget::removeSection()
{
  uint idx = selectedSection();
  if (idx == NotFound)
    return;
  else {
    wsp->removeSection(idx);
    rebuildWing();
  }

  int isel(-1);
  if (idx < wsp->nsections())
    isel = idx;
  else
    isel = idx-1;
  if (isel >= 0)
    listSection->setCurrentRow(isel, QItemSelectionModel::SelectCurrent);
}

void WingManagerWidget::sortSections()
{
  wsp->heuristicSort();
  updateList();
  rebuildWing();
}

void WingManagerWidget::moveSectionUp()
{
  int isec = listSection->currentRow();
  if (isec <= 0)
    return;

  wsp->swapSections(isec, isec-1);
  rebuildWing();
  updateList();

  listSection->setCurrentRow(isec-1, QItemSelectionModel::SelectCurrent);
  pbMoveUp->setEnabled(isec > 1);
}

void WingManagerWidget::moveSectionDown()
{
  int isec = listSection->currentRow();
  if (uint(isec) >= wsp->nsections())
    return;

  wsp->swapSections(isec, isec+1);
  rebuildWing();
  updateList();

  listSection->setCurrentRow(isec+1, QItemSelectionModel::SelectCurrent);
  pbMoveDown->setEnabled(isec+2 < (int) wsp->nsections());
}

void WingManagerWidget::sectionSelectionChanged(int isec)
{
  qDebug("Selected row: %d", isec);
  if (isec < 0)
    return;

  pbMoveUp->setEnabled(isec > 0);
  pbMoveDown->setEnabled(isec+1 < (int) wsp->nsections());
}

void WingManagerWidget::buildFlagSwitched(bool)
{
  rebuildWing();
}

void WingManagerWidget::rebuildWing()
{
  // update name
  wsp->rename( leName->text().toStdString() );
  
  // extract boolean settings
  wsp->autoSym( cbAutoSym->isChecked() );
  wsp->detectWinglet( cbDetectWinglet->isChecked() );
  wsp->cubicInterpolation( rbCubic->isChecked() );
  wsp->visible( cbVisible->isChecked() );
  
  Vct3 pos;
  pos[0] = sbPosX->value();
  pos[1] = sbPosY->value();
  pos[2] = sbPosZ->value();
  
  Vct3 rot;
  rot[0] = rad( sbRotX->value() );
  rot[1] = rad( sbRotY->value() );
  rot[2] = rad( sbRotZ->value() );
  
  wsp->southCapHeight( sbRightCap->value() );
  wsp->northCapHeight( sbLeftCap->value() );
  
  wsp->origin(pos);
  wsp->rotation(rot);
  wsp->interpolate();
  
  emit geometryChanged();
}

void WingManagerWidget::changeColor()
{
  Vct4 c( wsp->pgColor() );
  QColor cinit = QColor::fromRgbF(c[0], c[1], c[2]);
  QColor cnew = QColorDialog::getColor(cinit, this);
  cnew.getRgbF(&c[0], &c[1], &c[2]);
  wsp->pgColor(c);
}

void WingManagerWidget::showStats()
{
  WingStat wstat(this, wsp);
  wstat.exec();
}

void WingManagerWidget::adapt(QDoubleSpinBox *sb, double v) const
{
  // double lgv = ceil( -log10(v) );
  // sb->setDecimals( max(3, int(lgv+2)) );
  sb->setSingleStep( 0.2*v );
  sb->setValue(v);
}
