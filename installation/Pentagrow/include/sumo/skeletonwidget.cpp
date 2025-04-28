
/* ------------------------------------------------------------------------
 * file:       skeletonwidget.cpp
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Contains top- and side view 
 * ------------------------------------------------------------------------ */

#include <QSplitter>
#include <QBoxLayout>

#include "bodyskeleton.h"
#include "frameviewitem.h"
#include "skeletonview.h"
#include "editbody.h"
#include "skeletonwidget.h"

using namespace std;

SkeletonWidget::SkeletonWidget(QWidget *parent) : QWidget(parent)
{
  topview = new SkeletonView(this);
  sideview = new SkeletonView(this);
  
  topview->changeNames(" x", " y", " width");
  sideview->changeNames(" x", " z", " height");  
  
  // assume xz-symmetry  
  topview->symLock( true );
  
  // fill the entire space with splitter 
  splitter = new QSplitter(Qt::Vertical, this);
  layout = new QBoxLayout(QBoxLayout::TopToBottom, this);

  layout->setMargin(3);
  layout->addWidget(splitter);
  splitter->addWidget(sideview);
  splitter->addWidget(topview);
  
  // couple movement in x-direction 
  connect( topview, SIGNAL(xFrameMoved(int, double)),
           sideview, SLOT(xMoveFrame(int, double)) );
  connect( sideview, SIGNAL(xFrameMoved(int, double)),
           topview, SLOT(xMoveFrame(int, double)) );

  // update surface when sections modified
  connect( topview, SIGNAL(frameModified(int)),
           this, SLOT(frameModified(int)) );
  connect( sideview, SIGNAL(frameModified(int)),
           this, SLOT(frameModified(int)) );
  
  // accept request to remove or insert frames 
  connect( topview, SIGNAL(sigInsertFrame(double)),
           this, SLOT(insertFrame(double)) );
  connect( sideview, SIGNAL(sigInsertFrame(double)),
           this, SLOT(insertFrame(double)) );
  connect( topview, SIGNAL(sigRemoveFrame(double)),
           this, SLOT(removeFrame(double)) );
  connect( sideview, SIGNAL(sigRemoveFrame(double)),
           this, SLOT(removeFrame(double)) );
  
  // pass position message on 
  connect( topview, SIGNAL(mptrPosition(const QString&)),
           this, SIGNAL(mptrPosition(const QString&)) );
  connect( sideview, SIGNAL(mptrPosition(const QString&)),
           this, SIGNAL(mptrPosition(const QString&)) );
  
  // topology change is always a geometry change as well
  connect(this, SIGNAL(topologyChanged()), 
          this, SIGNAL(geometryChanged()) );
}

void SkeletonWidget::fitView()
{
  if (not mbsp)
    return;
  
  topview->fitView();
  sideview->fitView();
}

void SkeletonWidget::setBody(const BodySkeletonPtr & bsp)
{
  mbsp = bsp;
    
  topview->clear();
  sideview->clear();
  
  // don not continue unless surface is defined
  if (not mbsp) {
    repaint();
    return;
  }
  
  build();
  
  // whenever a new body is set, we need to recompute
  // the viewport boundaries
  fitView();
}

void SkeletonWidget::convert( int idrop, const Vct3 & org, 
                              const PointList<3> & pts, 
                              QPolygonF & ply) const
{
  const int np(pts.size());
  assert(np%2 == 0);
  const int n(np/2);
  ply.resize(np);
  
  Vct3 p;
  switch (idrop) {
    
    case 0:
      for (int i=0; i<n; ++i) {
        p = pts[2*i] - org;
        const Vct3 & t( pts[2*i+1] );
        ply[2*i + 0] = QPointF(p[1], p[2]);
        ply[2*i + 1] = QPointF(t[1], t[2]);
      }
      break;
      
    case 1:
      for (int i=0; i<n; ++i) {
        p = pts[2*i] - org;
        const Vct3 & t( pts[2*i+1] );
        ply[2*i + 0] = QPointF(p[0], p[2]);
        ply[2*i + 1] = QPointF(t[0], t[2]);
      }
      break;
      
    case 2:
      for (int i=0; i<n; ++i) {
        p = pts[2*i] - org;
        const Vct3 & t( pts[2*i+1] );
        ply[2*i + 0] = QPointF(p[0], p[1]);
        ply[2*i + 1] = QPointF(t[0], t[1]);
      }
      break;
  }
}

void SkeletonWidget::build()
{
  if (not mbsp)
    return;
  
  // add frames
  const Vct3 & org(mbsp->origin());
  const int nf(mbsp->nframes());
  for (int i=0; i<nf; ++i) {
    const BodyFrame & fr(*mbsp->frame(i));
    Vct3 pos = fr.origin();
    double h = fr.frameHeight();
    double w = fr.frameWidth();
    sideview->addFrame(pos[0], pos[2], h);
    topview->addFrame(pos[0], pos[1], w);
  }
  
  // add outlines
  PointList<3> pbot, ptop, pleft, pright;
  mbsp->evaluate(pbot, ptop, pleft, pright);

  QPolygonF ply;
  convert(1, org, ptop, ply);
  sideview->addOutline(ply);
  
  convert(1, org, pbot, ply);
  sideview->addOutline(ply);
  
  convert(2, org, pleft, ply);
  topview->addOutline(ply);
  
  convert(1, org, pleft, ply);
  sideview->addOutline(ply, Qt::gray);
  
  convert(2, org, pright, ply);
  topview->addOutline(ply);
}

void SkeletonWidget::frameModified(int i)
{
  if (not mbsp)
    return;
  
  // retrieve position and dimensions 
  QPointF tpos, spos;
  Real h = sideview->fdim(i, spos);
  Real w = topview->fdim(i, tpos);
  
  Vct3 pos;
  pos[0] = spos.x();
  pos[1] = tpos.y();
  pos[2] = spos.y();
  
  BodyFrame & f(*mbsp->frame(i));
  f.origin(pos);
  f.setFrameHeight(h);
  f.setFrameWidth(w);
  f.interpolate();
  rebuild();
  emit geometryChanged();
}

void SkeletonWidget::rebuild()
{
  if (not mbsp)
    return;
  
  mbsp->interpolate();
  update();
}

void SkeletonWidget::insertFrame(double x)
{
  if (not mbsp)
    return;

  BodyFramePtr bp = mbsp->insertFrame(x);
  setBody(mbsp);
  emit topologyChanged();
}

void SkeletonWidget::removeFrame(double x)
{
  if (not mbsp)
    return;
  
  mbsp->removeFrame(x);
  setBody(mbsp);
  emit topologyChanged();
}

void SkeletonWidget::reconstruct()
{
  topview->clear();
  sideview->clear();
  
  // don not continue unless surface is defined
  if (not mbsp)
    return;
  
  build();
  
  // whenever a new body is set, we need to recompute
  // the viewport boundaries
  fitView();
}

void SkeletonWidget::update()
{
  if (not mbsp) {
    topview->clear();
    sideview->clear();
    return;
  }
  
  // change frame dimensions 
  const int nf(mbsp->nframes());
  for (int i=0; i<nf; ++i) {
    const BodyFrame & fr(*mbsp->frame(i));
    Vct3 pos = fr.origin();
    double h = fr.frameHeight();
    double w = fr.frameWidth();
    sideview->changeFrame(i, pos[0], pos[2], h);
    topview->changeFrame(i, pos[0], pos[1], w);
  }
  
  // generate outlines 
  const Vct3 & org(mbsp->origin());
  PointList<3> pbot, ptop, pleft, pright;
  mbsp->evaluate(pbot, ptop, pleft, pright);
  
  QPolygonF ply;
  convert(1, org, ptop, ply);
  sideview->changeOutline(0, ply);
  
  convert(1, org, pbot, ply);
  sideview->changeOutline(1, ply);
  
  convert(2, org, pleft, ply);
  topview->changeOutline(0, ply);
  
  convert(1, org, pleft, ply);
  sideview->changeOutline(2, ply);
  sideview->repaint();
  
  convert(2, org, pright, ply);
  topview->changeOutline(1, ply);
  topview->repaint();
}

void SkeletonWidget::editProperties()
{
  if (not mbsp)
    return;
  
  DlgEditBody *dlg = new DlgEditBody(this, mbsp);
  connect(dlg, SIGNAL(geometryChanged()), this, SLOT(update()));
  dlg->show();
}
