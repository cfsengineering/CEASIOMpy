
/* ------------------------------------------------------------------------
 * file:       skeletonwidget.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Contains top- and side view 
 * ------------------------------------------------------------------------ */

#ifndef SUMO_SKELETONWIDGET_H
#define SUMO_SKELETONWIDGET_H

#include <QWidget>
#ifndef Q_MOC_RUN
#include "bodyskeleton.h"
#endif

class QSplitter;
class QBoxLayout;
class SkeletonView;

class SkeletonWidget : public QWidget 
{
  Q_OBJECT
  
  public:
    
    /// initialize side- and top views
    SkeletonWidget(QWidget *parent);
    
    /// access currently shown body 
    const BodySkeletonPtr & currentBody() const {return mbsp;}
    
    /// change body to process
    void setBody(const BodySkeletonPtr & bsp);
    
  public slots:
    
    /// fit both views
    void fitView();
    
    /// called when frame i was modified 
    void frameModified(int i);
    
    /// called to insert new frame at x
    void insertFrame(double x);
    
    /// called to remove frame near x
    void removeFrame(double x);
    
    /// reconstruct complete geometry
    void reconstruct();
    
    /// update geometry only (not topology)
    void update();
    
    /// show dialog to change body properties 
    void editProperties();
    
  signals:
    
    /// geometry modification performed 
    void geometryChanged();
    
    /// frame topology modified
    void topologyChanged();
    
    /// post mouse pointer position message 
    void mptrPosition(const QString & s);
    
  private:
    
    /// fill initial data 
    void build();
    
    /// interpolate surface, update outlines
    void rebuild();
    
    /// generate QPolygon from 3D coordinates 
    void convert(int idrop, const Vct3 & org, const PointList<3> & pts, 
                 QPolygonF & ply) const;
    
  private:
    
    /// surface to manipulate 
    BodySkeletonPtr mbsp;
    
    /// space layout 
    QBoxLayout *layout;
    
    /// split views
    QSplitter *splitter;
     
    /// views
    SkeletonView *topview, *sideview;
};

#endif

