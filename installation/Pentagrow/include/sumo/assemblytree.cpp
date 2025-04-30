
/* ------------------------------------------------------------------------
 * file:       assemblytree.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Left-pane tree widget in main window
 * ------------------------------------------------------------------------ */

#include "assemblytree.h"
#include <genua/sysinfo.h>
#include <QMouseEvent>
#include <QHeaderView>

using namespace std;

AssemblyTree::AssemblyTree(QWidget *parent, const AssemblyPtr & a) :
  QTreeWidget(parent), asy(a)
{
  setColumnCount(1);
  header()->hide();
  // setHeaderLabel(tr("Entity"));
  setSelectionMode(QAbstractItemView::SingleSelection);
  setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
  setTextElideMode(Qt::ElideMiddle);

#ifdef Q_OS_MAC
  setFrameStyle(QFrame::NoFrame);
  setAttribute(Qt::WA_MacShowFocusRect, false);
  setAutoFillBackground(true);

  QPalette color_palette = this->palette();
  QColor macSidebarColor(231, 237, 246);
  if (SysInfo::osversion() > SysInfo::OSX_1060)
    macSidebarColor = QColor(220, 226, 232);
  QColor macSidebarHighlightColor(168, 183, 205);
  color_palette.setColor(QPalette::Base, macSidebarColor);
  color_palette.setColor(QPalette::Highlight, macSidebarHighlightColor);
  setPalette(color_palette);
#endif

  build();
  
  connect(this, SIGNAL(itemClicked(QTreeWidgetItem*, int)),
          this, SLOT(signalSelectionChange(QTreeWidgetItem*, int)));
}

void AssemblyTree::changeAssembly(const AssemblyPtr & a)
{
  asy = a;
  build();
}

void AssemblyTree::build()
{
  cout << "AssemblyTree::build()" << endl;
  QTreeWidget::clear();
  
  const uint nb(asy->nbodies());
  for (uint i=0; i<nb; ++i) 
    updateBodyItem(i);
    
  const uint nw(asy->nwings());
  for (uint i=0; i<nw; ++i) 
    updateWingItem(i);
  
  sortItems(0, Qt::AscendingOrder);
  repaint();
}

void AssemblyTree::update()
{
  build();

//  // remove dead surface and section items
//  for (int i=0; i<topLevelItemCount(); ++i) {
//    ShTreeItem *item = dynamic_cast<ShTreeItem*>( topLevelItem(i) );
//    if (item == 0)
//      continue;
//    if (item->isValid()) {
//      item->index(i);
//      item->updateText();
//      for (int j=0; j<item->childCount(); ++j) {
//        ShTreeItem *sitem = dynamic_cast<ShTreeItem*>( item->child(j) );
//        if (sitem == 0)
//          continue;
//        if (sitem->isValid()) {
//          sitem->index(j);
//          sitem->updateText();
//        } else {
//          item->takeChild(j);
//          --j;
//        }
//      }
//    } else {
//      takeTopLevelItem(i);
//      --i;
//    }
//  }
  
//  // add any new surfaces
//  const uint nb(asy->nbodies());
//  for (uint i=0; i<nb; ++i)
//    updateBodyItem(i);
    
//  const uint nw(asy->nwings());
//  for (uint i=0; i<nw; ++i)
//    updateWingItem(i);
  
//  sortItems(0, Qt::AscendingOrder);
//  repaint();
}

ShTreeItem *AssemblyTree::findSurfaceItem(const std::string & s) const
{
  const int nti( topLevelItemCount() );
  for (int i=0; i<nti; ++i) {
    ShTreeItem *item = dynamic_cast<ShTreeItem*>( topLevelItem(i) );
    if (item != 0 and item->isValid() and item->geoname() == s)
      return item;
  }
  
  return 0;
}
    
ShTreeItem *AssemblyTree::findFrameItem(const ShTreeItem *parent, 
                                        const std::string & s) const
{
  if (parent == 0)
    return 0;
  
  const int n( parent->childCount() );
  for (int i=0; i<n; ++i) {
    ShTreeItem *item = dynamic_cast<ShTreeItem*>( parent->child(i) );
    if (item != 0 and item->geoname() == s)
      return item;
  }
  
  return 0;
}
    
void AssemblyTree::updateBodyItem(int idx)
{
  const BodySkeletonPtr & bsp(asy->body(idx));
  ShBodyItem *bi = dynamic_cast<ShBodyItem*>( findSurfaceItem(bsp->name()) );
  
  if (bi == 0) {
    
    // create body item if not already present 
    bi = new ShBodyItem(asy, idx);
    const uint nf(bsp->nframes());
    for (uint j=0; j<nf; ++j)
      bi->addChild( new ShBFrameItem(asy, idx, j) );
    QTreeWidget::addTopLevelItem(bi);
    
  } else {
    
    // update frame items if surface item present 
    const uint nf(bsp->nframes());
    for (uint j=0; j<nf; ++j) {
      const BodyFramePtr & bfp(bsp->frame(j));
      if (findFrameItem(bi, bfp->name()) == 0)
        bi->addChild( new ShBFrameItem(asy, idx, j) );
    }
  }
}

void AssemblyTree::updateWingItem(int idx)
{
  const WingSkeletonPtr & wsp(asy->wing(idx));
  ShWingItem *bi = dynamic_cast<ShWingItem*>( findSurfaceItem(wsp->name()) );
  
  if (bi == 0) {
    // create wing item if not already present 
    bi = new ShWingItem(asy, idx);
    const uint nf(wsp->nsections());
    for (uint j=0; j<nf; ++j)
      bi->addChild( new ShWSectionItem(asy, idx, j) );
    QTreeWidget::addTopLevelItem(bi);
    
  } else {
    // update frame items if surface item present 
    const uint nf(wsp->nsections());
    for (uint j=0; j<nf; ++j) {
      const WingSectionPtr & afp(wsp->section(j));
      if (findFrameItem(bi, afp->name()) == 0)
        bi->addChild( new ShWSectionItem(asy, idx, j) );
    }
  }
}

void AssemblyTree::mouseReleaseEvent(QMouseEvent *e)
{
  if (e->button() == Qt::RightButton) {
    QTreeWidgetItem *item = currentItem();
    ShTreeItem *sitem = dynamic_cast<ShTreeItem*>(item);
    if (sitem != 0)
      emit rmbClicked(sitem, e->globalPos());
  }
  QTreeWidget::mouseReleaseEvent(e);
}

void AssemblyTree::contextMenuEvent(QContextMenuEvent *e)
{
  QTreeWidgetItem *item = currentItem();
  ShTreeItem *sitem = dynamic_cast<ShTreeItem*>(item);
  if (sitem != 0)
    emit rmbClicked(sitem, e->globalPos());
}

void AssemblyTree::signalSelectionChange(QTreeWidgetItem *cur, int)
{
  if (cur == 0)
    return;
  
  ShTreeItem *sitem = dynamic_cast<ShTreeItem*>(cur);
  if (sitem != 0) 
    emit itemSelected(sitem);
}
