
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
 
#include "componentdialog.h"
#include "plotcontroller.h"
#include "meshplotter.h"
#include "sectionplotter.h"
#include <genua/mxmesh.h>
#include <QInputDialog>

ComponentDialog::ComponentDialog(QWidget *parent)
  : QDialog(parent, Qt::Tool), m_plc(0)
{
  setupUi(this);

#ifdef Q_OS_MAC
  gbSections->setFlat(true);
  gbBocos->setFlat(true);
#endif

  // map element types to names
  m_et2s[Mx::Undefined] = tr("Undefined element");
  m_et2s[Mx::Point] = tr("Point element");
  m_et2s[Mx::Line2] = tr("2-node line element");
  m_et2s[Mx::Line3] = tr("3-node line element");
  m_et2s[Mx::Tri3] = tr("3-node triangle");
  m_et2s[Mx::Tri6] = tr("6-node triangle");
  m_et2s[Mx::Quad4] = tr("4-node quadrilateral");
  m_et2s[Mx::Quad8] = tr("8-node quadrilateral");
  m_et2s[Mx::Quad9] = tr("9-node quadrilateral");
  m_et2s[Mx::Tet4] = tr("4-node tetrahedron");
  m_et2s[Mx::Tet10] = tr("10-node tetrahedron");
  m_et2s[Mx::Pyra5] = tr("5-node pyramid");
  m_et2s[Mx::Pyra14] = tr("14-node pyramid");
  m_et2s[Mx::Hex8] = tr("8-node hexahedron");
  m_et2s[Mx::Hex20] = tr("20-node hexahedron");
  m_et2s[Mx::Hex27] = tr("27-node hexahedron");
  m_et2s[Mx::Penta6] = tr("6-node pentahedron");
  m_et2s[Mx::Penta15] = tr("15-node pentahedron");
  m_et2s[Mx::Penta18] = tr("18-node pentahedron");

  // map bocos to names
  std::map<Mx::BocoType, QString> bc2s;
  {
    const int n = (int) Mx::BcNTypes;
    for (int i=0; i<n; ++i) {
      Mx::BocoType m = (Mx::BocoType) i;
      bc2s[m] = QString::fromStdString( Mx::str(m) );
    }
  }

  // set text for available boco types in combo box
  const int nbt = (int) Mx::BcNTypes;
  for (int i=0; i<nbt; ++i) {
    std::map<Mx::BocoType, QString>::const_iterator itm;
    itm = bc2s.find( (Mx::BocoType) i );
    if (itm != bc2s.end())
      cbBocoType->addItem(itm->second);
    else
      cbBocoType->addItem(tr("Unknown BC"));
  }

  // update UI on user selection
  connect( cbSelectSection, SIGNAL(currentIndexChanged(int)),
           this, SLOT(sectionSelected(int)) );
  connect( cbSelectBoco, SIGNAL(currentIndexChanged(int)),
           this, SLOT(bocoSelected(int)) );

  // change boundary condition type
  connect( cbBocoType, SIGNAL(currentIndexChanged(int)),
           this, SLOT(changeBocoType(int)) );

  // apply changes to visibility masks
  connect( cbShowEdges, SIGNAL(clicked()),
           this, SLOT(apply()) );
  connect( cbShowElements, SIGNAL(clicked()),
           this, SLOT(apply()) );
  connect( cbShowNormals, SIGNAL(clicked()),
           this, SLOT(apply()) );
  connect( cbShowBoco, SIGNAL(clicked()),
           this, SLOT(apply()) );

  // erase entire section or boco
  connect( pbEraseSection, SIGNAL(clicked()),
           this, SLOT(eraseSection()) );
  connect( pbEraseBoco, SIGNAL(clicked()),
           this, SLOT(eraseBoco()) );
  connect( pbNewBoco, SIGNAL(clicked()),
           this, SLOT(newBoco()) );

  // change color of section or boco
  connect( pbSectionColor, SIGNAL(clicked()),
           this, SLOT(changeSectionColor()) );
  connect( pbBocoColor, SIGNAL(clicked()),
           this, SLOT(changeBocoColor()) );

  // global changes
  connect( pbToggleEdges, SIGNAL(clicked()),
           this, SLOT(toggleAllEdges()) );
}

void ComponentDialog::assign(PlotController *plc)
{
  if (m_plc != 0)
    this->disconnect(m_plc);

  m_plc = plc;
  if (m_plc == 0)
    return;

  // setup UI contents on mesh changes
  connect( m_plc, SIGNAL(structureChanged()),
           this, SLOT(updateStructure()) );

  updateStructure();
}

void ComponentDialog::updateStructure()
{
  int presection = cbSelectSection->currentIndex();
  int preboco = cbSelectBoco->currentIndex();
  cbSelectSection->clear();
  cbSelectBoco->clear();

  MxMeshPtr pmx = m_plc->pmesh();
  if (not pmx)
    return;
  for (uint i=0; i<pmx->nsections(); ++i) {
    const std::string & s( pmx->section(i).name() );
    cbSelectSection->addItem( QString::fromStdString(s) );
  }
  for (uint i=0; i<pmx->nbocos(); ++i) {
    const std::string & s( pmx->boco(i).name() );
    cbSelectBoco->addItem( QString::fromStdString(s) );
  }

  if (presection >= 0 and presection < cbSelectSection->count())
    selectSection(presection);
  else
    selectSection(0);

  if (preboco >= 0 and preboco < cbSelectBoco->count())
    selectBoco(preboco);
  else
    selectBoco(0);
}

void ComponentDialog::selectSection(int isection)
{
  if (isection < 0)
    return;
  else if (isection != cbSelectSection->currentIndex())
    cbSelectSection->setCurrentIndex(isection);
}

void ComponentDialog::selectBoco(int iboco)
{
  if (iboco < 0)
    return;
  else if (iboco != cbSelectBoco->currentIndex())
    cbSelectBoco->setCurrentIndex(iboco);
}

void ComponentDialog::sectionSelected(int isection)
{
  if (isection < 0 or m_plc == 0)
    return;

  MxMeshPtr pmx = m_plc->pmesh();
  if ((not pmx) or (uint(isection) >= pmx->nsections()))
    return;

  MeshPlotterPtr plotter = m_plc->plotter();
  if (not plotter)
    return;

  const SectionPlotter & sp( plotter->section(isection) );
  cbShowElements->setChecked( sp.showElements() );
  cbShowEdges->setChecked( sp.showEdges() );
  cbShowNormals->setChecked( sp.showNormals() );

  QLocale loc;
  const MxMeshSection & sec( pmx->section(isection) );
  int etype = sec.elementType();
  lbElementType->setText( m_et2s[etype] );
  QString info = tr("%1 elements").arg(loc.toString(sec.nelements()));
  lbElementCount->setText( info );
  cbShowNormals->setEnabled( sec.surfaceElements() );

  bool edgeOption = sec.volumeElements() or sec.surfaceElements();
  cbShowEdges->setEnabled(edgeOption);
}

void ComponentDialog::bocoSelected(int iboco)
{
  if (iboco < 0 or m_plc == 0)
    return;

  MxMeshPtr pmx = m_plc->pmesh();
  if ((not pmx) or (uint(iboco) >= pmx->nbocos()))
    return;

  MeshPlotterPtr plotter = m_plc->plotter();
  if (not plotter)
    return;

  const MxMeshBoco & bc( pmx->boco(iboco) );
  QLocale loc;
  QString infoText;
  if (bc.isRange())
    infoText =  tr("%1 elements: %2:%3").arg( loc.toString(bc.nelements()) )
                .arg( loc.toString(bc.rangeBegin()) )
                .arg( loc.toString(bc.rangeEnd()) );
  else
    infoText =  tr("%1 elements").arg(loc.toString(bc.nelements()));
  lbBocoCount->setText( infoText );
  cbShowBoco->setChecked( plotter->bocoVisible(iboco) );
  int btype = bc.bocoType();
  assert(btype < cbBocoType->count());
  cbBocoType->setCurrentIndex(btype);
}

void ComponentDialog::apply()
{
  if (m_plc == 0)
    return;

  uint isection = cbSelectSection->currentIndex();
  uint iboco = cbSelectBoco->currentIndex();

  MxMeshPtr pmx = m_plc->pmesh();
  if (not pmx)
    return;

  MeshPlotterPtr plotter = m_plc->plotter();
  if (not plotter)
    return;

  // changes to currently selected section
  if (isection < pmx->nsections()) {
    SectionPlotter & sp(plotter->section(isection));
    bool visBefore = sp.visible();
    bool sedges = cbShowEdges->isChecked();
    bool selems = cbShowElements->isChecked();
    bool snorm = cbShowNormals->isChecked();
    bool visAfter = sedges or selems;
    bool reDraw = false;
    if (sp.showEdges() != sedges) {
      sp.showEdges(sedges);
      reDraw = true;
    }
    if (sp.showElements() != selems) {
      sp.showElements(selems);
      reDraw = true;
    }
    if (sp.showNormals() != snorm) {
      sp.showNormals(snorm);
      reDraw = true;
    }
    if (visBefore != visAfter)
      emit sectionVisibilityChanged(isection, visAfter);
    if (reDraw)
      emit needRedraw();
  }

  // changes to currently selected boco
  if (iboco < pmx->nbocos()) {
    bool visBefore = plotter->bocoVisible(iboco);
    bool visAfter = cbShowBoco->isChecked();
    if (visBefore != visAfter) {
      m_plc->showBoco(iboco, visAfter);
      emit bocoVisibilityChanged(iboco, visAfter);
    }
  }
}

void ComponentDialog::toggleAllEdges()
{
  MxMeshPtr pmx = m_plc->pmesh();
  if (not pmx)
    return;

  MeshPlotterPtr plotter = m_plc->plotter();
  if (not plotter)
    return;

  const size_t nsec = pmx->nsections();
  for (size_t i=0; i<nsec; ++i) {
    SectionPlotter & sp(plotter->section(i));
    if (sp.visible())
      sp.showEdges( not sp.showEdges() );
  }
  emit needRedraw();
}

void ComponentDialog::changeBocoType(int bocoType)
{
  if (bocoType < 0 or m_plc == 0)
    return;

  MxMeshPtr pmx = m_plc->pmesh();
  if (not pmx)
    return;

  int iboco = cbSelectBoco->currentIndex();
  if (uint(iboco) > pmx->nbocos())
    return;

  MxMeshBoco & bc( pmx->boco(iboco) );
  bc.bocoType( (Mx::BocoType) bocoType );
}

void ComponentDialog::eraseSection()
{
  int isection = cbSelectSection->currentIndex();
  if (isection < 0 or m_plc == 0)
    return;

  m_plc->eraseSection(isection);
}

void ComponentDialog::eraseBoco()
{
  int isection = cbSelectBoco->currentIndex();
  if (isection < 0 or m_plc == 0)
    return;

  m_plc->eraseBoco(isection);
}

void ComponentDialog::newBoco()
{
  if (not m_plc)
    return;
  MxMeshPtr pmx = m_plc->pmesh();

  // fairly limited right now - can only create a boco which maps
  // a section exactly
  bool ok(false);
  QStringList secNames;
  for (size_t i=0; i<pmx->nsections(); ++i) {
    secNames << QString("[%1] - ").arg(i+1) +
                QString::fromStdString(pmx->section(i).name());
  }
  QString selected = QInputDialog::getItem(this, tr("Create new element group"),
                                   tr("Select mapped section"), secNames,
                                   0, false, &ok);
  if (not ok)
    return;

  int isec = secNames.indexOf(selected);
  if (size_t(isec) > pmx->nsections())
    return;

  // will emit structureChanged() which causes update of UI
  m_plc->addMappedBoco(isec);
}

void ComponentDialog::changeSectionColor()
{
  int isec = cbSelectSection->currentIndex();
  if (m_plc == 0 or isec < 0)
    return;
  m_plc->changeSectionColor(isec);
}

void ComponentDialog::changeBocoColor()
{
  int isec = cbSelectBoco->currentIndex();
  if (m_plc == 0 or isec < 0)
    return;
  m_plc->changeBocoColor(isec);
}

