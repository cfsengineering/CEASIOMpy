
/* ------------------------------------------------------------------------
 * file:       assemblytree.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Left-pane tree widget in main window
 * ------------------------------------------------------------------------ */

#ifndef SUMO_ASSEMBLYTREE_H
#define SUMO_ASSEMBLYTREE_H

#include <QTreeWidget>

#ifndef Q_MOC_RUN
#include "assembly.h"
#include "shelltreeitems.h"
#endif

class QMouseEvent;

/**
*/
class AssemblyTree : public QTreeWidget
{
  Q_OBJECT
  
  public:
    
    /// construct tree attached to parent 
    AssemblyTree(QWidget *parent, const AssemblyPtr & a);
    
    /// change model to display 
    void changeAssembly(const AssemblyPtr & a);

  signals:
    
    /// announce selection change 
    void itemSelected(ShTreeItem *item);
    
    /// announce right mouse button click 
    void rmbClicked(ShTreeItem *item, const QPoint & p);
    
  public slots:
    
    /// create all items from assembly
    void build();
    
    /// update display tree 
    void update();
    
  private slots:
    
    /// emit selection changed signal 
    void signalSelectionChange(QTreeWidgetItem *cur, int col);
    
  protected:
    
    /// right click
    void mouseReleaseEvent(QMouseEvent *e);
    
    /// catch context menu request
    void contextMenuEvent(QContextMenuEvent *e);

  private:
    
    /// check if top-level item with label s is present 
    ShTreeItem *findSurfaceItem(const std::string & s) const;
    
    /// find frame item or return 0
    ShTreeItem *findFrameItem(const ShTreeItem *parent, 
                              const std::string & s) const;
    
    /// create/and or update item for body 
    void updateBodyItem(int idx);
    
    /// create/and or update item for wing
    void updateWingItem(int idx);
    
  private:
    
    /// assembly to display
    AssemblyPtr asy; 
};

#endif
