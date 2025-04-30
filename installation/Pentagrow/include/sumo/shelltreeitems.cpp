
/* ------------------------------------------------------------------------
 * file:       shelltreeitems.cpp
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Items for the left-pane tree of the main window
 * ------------------------------------------------------------------------ */

#include <QFont>
#include "shelltreeitems.h"

using namespace std;

static QString prefixed_name(const std::string & s, uint nf, uint idx)
{
  ++idx;
  
  QString pf;
  if ((nf < 10) or (nf < 100 and idx > 9) ) {
    pf = "";
  } else if (nf < 100 and idx < 10) {
    pf = "0";
  } else if (idx < 10) {
    pf = "00";
  } 
  pf += QString::number(idx) + " ";
  return pf + QString::fromStdString(s);
}

// ----------------------------------------------------------------------------

ShBodyItem::ShBodyItem(const AssemblyPtr & a, uint idx) :
    ShTreeItem( ShBodyItemType, idx ), asy(a)
{
  if (idx != NotFound)
    bsp = asy->body(idx);

  QFont ft;
  ft.setBold(true);
  setFont(0, ft);
  updateText();
}
    
bool ShBodyItem::isValid() const 
{
  if (bsp)
    return (asy->find( bsp->name() ) != NotFound);
  else
    return false;
}
    
void ShBodyItem::updateText()
{
  QString s;
  if (bsp)
    s = QString::fromStdString(bsp->name());
  else
    s = "(Unassociated ShBodyItem)";
  setText(0, s);
}
 
// ----------------------------------------------------------------------------

ShWingItem::ShWingItem(const AssemblyPtr & a, uint idx) :
    ShTreeItem( ShWingItemType, idx ), asy(a)
{
  if (idx != NotFound)
    wsp = asy->wing(idx);

  QFont ft;
  ft.setBold(true);
  setFont(0, ft);
  updateText();
}
    
bool ShWingItem::isValid() const 
{
  if (wsp)
    return (asy->find( wsp->name() ) != NotFound);
  else
    return false;
}
    
void ShWingItem::updateText()
{
  QString s;
  if (wsp)
    s = QString::fromStdString(wsp->name());
  else
    s = QString("(ShWingItem not associated.)");
  setText(0, s);
}

// ----------------------------------------------------------------------------

ShBFrameItem::ShBFrameItem(const AssemblyPtr &a, uint ibody, uint iframe) :
    ShTreeItem( ShBFrameItemType, iframe, ibody )
{
  if (ibody < a->nbodies()) {
    bsp = a->body(ibody);
    if (iframe < bsp->nframes())
      bfp = bsp->frame(iframe);
  }

  updateText();
}
    
bool ShBFrameItem::isValid() const 
{
  if (bsp and bfp)
    return (bsp->find( bfp ) != NotFound);
  else
    return false;
}
    
void ShBFrameItem::updateText()
{
  QString s;
  if (bfp)
    s = prefixed_name(bfp->name(), bsp->nframes(), index());
  else
    s = "(Unassociated ShFrameItem)";
  setText(0, s);
}

// ----------------------------------------------------------------------------

ShWSectionItem::ShWSectionItem(const AssemblyPtr &a, uint iwing, uint isection) :
    ShTreeItem( ShWSectionItemType, isection, iwing )
{
  if (iwing < a->nwings()) {
    wsp = a->wing(iwing);
    if (isection < wsp->nsections())
      afp = wsp->section(isection);
  }

  updateText();
}
    
bool ShWSectionItem::isValid() const 
{
  if (wsp and afp)
    return (wsp->findByName( afp->name() ) != NotFound);
  else
    return false;
}
    
void ShWSectionItem::updateText()
{
  QString s;
  if (afp)
    s = prefixed_name(afp->name(), wsp->nsections(), index());
  else
    s = "(Unassociated ShSectionItem)";
  setText(0, s);
}


