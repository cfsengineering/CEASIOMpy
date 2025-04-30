
/* ------------------------------------------------------------------------
 * file:       shelltreeitems.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Items for the left-pane tree of the main window
 * ------------------------------------------------------------------------ */

#ifndef SUMO_SHELLTREEITEMS_H
#define SUMO_SHELLTREEITEMS_H

#include <QTreeWidgetItem>

#include "assembly.h"
#include "bodyskeleton.h"
#include "wingskeleton.h"
#include "bodyframe.h"
#include "wingsection.h"

typedef enum { ShBodyItemType = QTreeWidgetItem::UserType+1,
               ShWingItemType,
               ShBFrameItemType,
               ShWSectionItemType } ShellTreeItemType;

class ShTreeItem : public QTreeWidgetItem
{
public:

  /// construct with type tag
  ShTreeItem(ShellTreeItemType t, uint itIndex = NotFound,
             uint parIndex = NotFound)
    : QTreeWidgetItem(t), itemIndex(itIndex), parentIndex(parIndex) {}

  /// virtual destruction
  virtual ~ShTreeItem() {}

  /// check if item is well-defined
  virtual bool isValid() const {return (itemIndex != NotFound);}

  /// update text property
  virtual void updateText() = 0;

  /// access item name
  virtual const std::string & geoname() const = 0;

  /// access index of item itself
  uint index() const {return itemIndex;}

  /// access index of item itself
  void index(uint i) {itemIndex = i; followIndex();}

  /// access index of parent entity
  uint parent() const {return parentIndex;}

  /// check whether item is a top-level entity
  bool topLevel() const {return parentIndex == NotFound;}

protected:

  /// update the referenced object
  virtual void followIndex() {}

protected:

  /// index of the represented body/wing/section/frame
  uint itemIndex;

  /// index of the parent item (NotFound for assembly)
  uint parentIndex;
};

class ShBodyItem : public ShTreeItem
{
public:

  /// construct item from surface
  ShBodyItem(const AssemblyPtr & a, uint idx);

  /// check if item is still valid
  bool isValid() const;

  /// set proper text
  void updateText();

  /// retrieve body skeleton
  const BodySkeletonPtr & geometry() const {return bsp;}

  /// access geometry object name
  const std::string & geoname() const {
    assert(bsp);
    return bsp->name();
  }

protected:

  void followIndex() {
    if (asy and (itemIndex != NotFound) and (itemIndex < asy->nbodies()))
      bsp = asy->body(itemIndex);
    else
      bsp.reset();
  }

private:

  /// assembly
  AssemblyPtr asy;

  /// attached body skeleton
  BodySkeletonPtr bsp;
};

class ShWingItem : public ShTreeItem
{
public:

  /// construct item from surface
  ShWingItem(const AssemblyPtr & a, uint idx);

  /// check if item is still valid
  bool isValid() const;

  /// set proper text
  void updateText();

  /// retrieve body skeleton
  const WingSkeletonPtr & geometry() const {return wsp;}

  /// access geometry object name
  const std::string & geoname() const {
    assert(wsp);
    return wsp->name();
  }

protected:

  void followIndex() {
    if (asy and (itemIndex != NotFound) and (itemIndex < asy->nwings()))
      wsp = asy->wing(itemIndex);
    else
      wsp.reset();
  }

private:

  /// assembly
  AssemblyPtr asy;

  /// wing geometry
  WingSkeletonPtr wsp;
};

class ShBFrameItem : public ShTreeItem
{
public:

  /// construct item from surface
  ShBFrameItem(const AssemblyPtr & a, uint ibody, uint iframe);

  /// check if item is still valid
  bool isValid() const;

  /// set proper text
  void updateText();

  /// retrieve body skeleton
  const BodyFramePtr & geometry() const {return bfp;}

  /// access geometry object name
  const std::string & geoname() const {
    assert(bfp);
    return bfp->name();
  }

  /// access body
  const BodySkeletonPtr & body() const {return bsp;}

protected:

  void followIndex() {
    if (bsp and (itemIndex != NotFound) and (itemIndex < bsp->nframes()))
      bfp = bsp->frame(itemIndex);
    else
      bfp.reset();
  }

private:

  /// parent surface
  BodySkeletonPtr bsp;

  /// section
  BodyFramePtr bfp;
};

class ShWSectionItem : public ShTreeItem
{
public:

  /// construct item from surface
  ShWSectionItem(const AssemblyPtr & a, uint iwing, uint iframe);

  /// check if item is still valid
  bool isValid() const;

  /// set proper text
  void updateText();

  /// retrieve section object
  const WingSectionPtr & geometry() const {return afp;}

  /// access geometry object name
  const std::string & geoname() const {
    assert(afp);
    return afp->name();
  }

  /// access parent wing
  const WingSkeletonPtr & wing() const {return wsp;}

protected:

  void followIndex() {
    if (wsp and (itemIndex != NotFound) and (itemIndex < wsp->nsections()))
      afp = wsp->section(itemIndex);
    else
      afp.reset();
  }

private:

  /// parent surface
  WingSkeletonPtr wsp;

  /// section
  WingSectionPtr afp;
};

#endif
