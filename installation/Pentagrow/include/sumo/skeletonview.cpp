
/* ------------------------------------------------------------------------
 * file:       skeletonview.cpp
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Used for body side- and top views
 * ------------------------------------------------------------------------ */

#include <iostream>
#include <QResizeEvent>
#include <QPainter>
#include <QMenu>
#include <QAction>
#include <QPixmap>
#include <QImageReader>
#include <QFileDialog>
#include <genua/defines.h>
#include "frameviewitem.h"
#include "skeletonview.h"

using namespace std;

SkeletonView::SkeletonView(QWidget *parent) :  
    QFrame(parent)
{
  QFrame::setFrameShape( QFrame::StyledPanel );
  QFrame::setFrameShadow( QFrame::Plain );
  QFrame::setLineWidth(4);
  
  ppm = 0;
  xdorg = 0;
  ydorg = 0;
  xmin = huge;
  xmax = -huge;
  ymin = huge;
  ymax = -huge;
  iselect = -1;
  nzoom = 0;
  symlock = false;
  
  origim = new QPixmap;
  trfim = new QPixmap;
  drawbgi = false;
  
  xname = " x";
  yname = " y";
  hname = " size";
  
  initActions();
}

void SkeletonView::initActions()
{
  ctmenu = new QMenu(this);
  actFlipLock = ctmenu->addAction( tr("&Symmetry lock"), this, 
                                   SLOT(flipSymLock()) );
  actFlipLock->setCheckable(true);
  actInsert = ctmenu->addAction( tr("&Insert frame here"), this,
                                 SLOT(insertFrame()) );
  actRemove = ctmenu->addAction(  tr("&Remove nearest frame"), this,
                                 SLOT(removeFrame()) );
  actLoadBgi = ctmenu->addAction( tr("&Load background image"), this,
                                 SLOT(loadBackgroundImage()) );
  
  // on construction, there is no background image, disabled
  actToggleBgi = ctmenu->addAction( tr("Toggle &background image"), this,
                                    SLOT(toggleBackgroundImage()) );
  actToggleBgi->setEnabled(false);
  actToggleBgi->setCheckable(true);
}

void SkeletonView::changeNames(const QString & x, const QString & y,
                               const QString & h)
{
  xname = x;
  yname = y;
  hname = h;
}
    
void SkeletonView::clear()
{
  fhdl.clear();
  otl.clear();
  
  iselect = -1;
  nzoom = 0;
  ppm = 0;
  xdorg = 0;
  ydorg = 0;
  xmin = huge;
  xmax = -huge;
  ymin = huge;
  ymax = -huge;
}

void SkeletonView::insertFrame()
{
  // convert mouse position to physical value
  double x = xdorg + mspress.x()/ppm;
  emit sigInsertFrame(x);
}

void SkeletonView::removeFrame()
{
  // convert mouse position to physical value
  double x = xdorg + mspress.x()/ppm;
  emit sigRemoveFrame(x);
}

void SkeletonView::fitView()
{
  // recompute boundaries
  xmin = huge;
  xmax = -huge;
  ymin = huge;
  ymax = -huge;
  
  const int nf(fhdl.size());
  for (int i=0; i<nf; ++i) {
    const QPointF & p(fhdl[i].position());
    qreal h = fhdl[i].height();
    xmin = min(xmin, p.x());
    xmax = max(xmax, p.x());
    ymin = min(ymin, p.y()-0.5*h);
    ymax = max(ymax, p.y()+0.5*h);
  }
  
  qreal xlen = xmax - xmin;
  qreal ylen = ymax - ymin;
  
  if (xlen > 0) {
    qreal w = width();
    qreal h = height();
    ppm = 0.9*min(w/xlen, h/ylen);
    xdorg = xmin - 0.05*xlen;
    ydorg = 0.5*(ymin + ymax);
    displace();
  }
  
  nzoom = 0;
}

void SkeletonView::displace()
{
  const int nf(fhdl.size());
  for (int i=0; i<nf; ++i) 
    fhdl[i].replace(QPointF(xdorg,ydorg), ppm);
  const int no(otl.size());
  for (int i=0; i<no; ++i)
    otl[i].replace(QPointF(xdorg,ydorg), ppm);
  repaint();
}

void SkeletonView::xMoveFrame(int i, double dx)
{
  fhdl[i].move(dx, 0.0);
  fhdl[i].replace(QPointF(xdorg,ydorg), ppm);
  repaint();
}

bool SkeletonView::selectFrame()
{
  QPointF pos(mspress.x(), -(mspress.y()-0.5*height()));
  const int nf(fhdl.size());
  for (int i=0; i<nf; ++i) {
    const FrameHandle & h(fhdl[i]);
    if (h.inCenterBox(pos)) {
      act = SkvMove;
      if (symlock)
        setCursor(Qt::SizeHorCursor);
      else
        setCursor(Qt::SizeAllCursor);
      iselect = i;
      return true;
    } else if (h.inTopBox(pos)) {
      act = SkvModTop;
      setCursor(Qt::SizeVerCursor);
      iselect = i;
      return true;
    } else if (h.inBotBox(pos)) {
      act = SkvModBot;
      setCursor(Qt::SizeVerCursor);
      iselect = i;
      return true;
    }
  }
  
  act = SkvNone;
  iselect = -1;
  return false;
}

bool SkeletonView::contextMenu()
{
  QPointF pos(mspress.x(), -(mspress.y()-0.5*height()));
  int fselect(-1);
  const int nf(fhdl.size());
  for (int i=0; i<nf; ++i) {
    const FrameHandle & h(fhdl[i]);
    if (h.inCenterBox(pos)) {
      fselect = i;
      break;
    } else if (h.inTopBox(pos)) {
      fselect = i;
      break;
    } else if (h.inBotBox(pos)) {
      fselect = i;
      break;
    }
  }
  
  if (fselect != -1) {
    actRemove->setEnabled(true);
    actRemove->setText( QString(tr("&Remove frame %1")).arg(fselect+1) );
    actInsert->setEnabled(false);
    actFlipLock->setChecked(symlock);
    ctmenu->exec( mapToGlobal(mspress) );
    return true;
  } else {
    actRemove->setText( QString(tr("&Remove nearest frame")) );
    actRemove->setEnabled(true);
    actInsert->setEnabled(true);
    actFlipLock->setChecked(symlock);
    ctmenu->exec( mapToGlobal(mspress) );
    return true;
  } 
  
  return false;
}

void SkeletonView::postFramePosition(int i, double t)
{
  assert(uint(i) < fhdl.size());
  const QPointF & p(fhdl[i].position());
  double h = fhdl[i].height();
  double y = p.y() + t*h;
  QString s(xname);
  s += ": " + QString::number(p.x(), 'f', 4);
  s += yname;
  s += ": " + QString::number(y, 'f', 4);
  s += hname;
  s += ": " + QString::number(h, 'f', 4);
  emit mptrPosition(s);
}

void SkeletonView::loadBackgroundImage()
{
  // offer only supported image formats for selection
  QList<QByteArray> imf = QImageReader::supportedImageFormats();
  QString filter = tr("Supported formats (");
  for (int i=0; i<imf.size(); ++i)
    filter += QString("*.%1 ").arg(imf[i].constData());
  filter += tr(");; All files(*.*)");
  
  QString caption = tr("Load background image");
  QString fn = QFileDialog::getOpenFileName(this, caption, QString(), filter);
  if (not fn.isEmpty()) {
    if (origim->load(fn)) {
      drawbgi = true;
      actToggleBgi->setEnabled(true);
      actToggleBgi->setChecked(drawbgi);
      fitBackgroundImage(width(), height());
    } else {
      drawbgi = false;
      actToggleBgi->setEnabled(false);
      actToggleBgi->setChecked(drawbgi);
    }
    repaint();
  }
}
    
void SkeletonView::toggleBackgroundImage()
{
  if (origim->width() > 0) {
    drawbgi = not drawbgi;
    actToggleBgi->setChecked(drawbgi);
    fitBackgroundImage(width(), height());
    repaint();
  } else {
    actToggleBgi->setEnabled(false);
    drawbgi = false;
  }
}

void SkeletonView::fitBackgroundImage(int w, int h)
{
  if ( (not drawbgi) or (origim->isNull()) )
    return;
  
  *trfim = origim->scaled(w, h, Qt::KeepAspectRatio, 
                                Qt::SmoothTransformation);
}
       
void SkeletonView::resizeEvent(QResizeEvent *e)
{
  // Resizing heuristic:
  // If the user has not used zoom/pan since last fitView(),
  // we simply keep the view to enclose the whole scene.
  // Otherwise, resizing will only move the drawing origin
  if (nzoom == 0) {
    fitView();
  } else {
    qreal w = e->size().width();
    qreal ow = e->oldSize().width();
    xdorg -= 0.5*(w - ow)/ppm;
    displace();
  }  
  
  // transform background image to fit the new widget size 
  fitBackgroundImage(e->size().width(), e->size().height());
}

void SkeletonView::paintEvent(QPaintEvent *e)
{
  QPainter pnt(this);
  pnt.setRenderHint(QPainter::Antialiasing);
  
  // fill background with white or background image  
  pnt.fillRect(QRectF(0,0,width(),height()), Qt::white);
  if (drawbgi and (not trfim->isNull()) ) {
    int imx = (width() - trfim->width()) / 2;
    int imy = (height() - trfim->height()) / 2;
    pnt.drawPixmap(QPoint(imx,imy), *trfim);
  }
      
  // move origin and make y point up
  pnt.translate(0.0, 0.5*height());
  pnt.scale(1.0, -1.0);
  
  // draw line at y == 0
  qreal yo = -ydorg*ppm;
  QPen p1(Qt::DashDotLine);
  p1.setColor(Qt::gray);
  pnt.setPen(p1);
  pnt.drawLine(QPointF(0,yo), QPointF(width(),yo));
  
  // draw outlines
  const int no(otl.size());
  for (int i=0; i<no; ++i) 
    otl[i].paint(&pnt);
  
  // draw frame handles 
  const int nf(fhdl.size());
  for (int i=0; i<nf; ++i) 
    fhdl[i].paint(&pnt);
  
  // draw frame numbers, but not upside down 
  QPointF tpos;
  pnt.scale(1.0, -1.0);
  qreal hds = FrameHandle::handleSize();
  for (int i=0; i<nf; ++i) {
    tpos = fhdl[i].textPos();
    tpos.ry() = -tpos.y() - (hds + 4);
    pnt.drawText(tpos, QString::number(i+1));
  }
  pnt.end();  

  QFrame::paintEvent(e);
}

void SkeletonView::mousePressEvent(QMouseEvent *e)
{  
  iselect = -1;
  switch (e->button()) {
    
    case Qt::LeftButton:
      mspress = e->pos();
      selectFrame();
      break;
    
    case Qt::MidButton:
      if (e->type() == QEvent::MouseButtonDblClick) {
        fitView();
      } else {
        act = SkvZoom;
        mspress = e->pos();
      }
      break;
      
    case Qt::RightButton:      
      mspress = e->pos();
      act = SkvPan;
      setCursor(Qt::ClosedHandCursor);
      span = 0.0;
      break;
      
    default:
      act = SkvNone;
  }
  
  // QWidget::mousePressEvent(e);
}

void SkeletonView::mouseMoveEvent(QMouseEvent *e)
{
  qreal dx, dy, zf, ippm(1./ppm);
  switch (act) {
    
    case SkvPan:
      dx = (e->pos().x() - mspress.x())*0.5*ippm;
      dy = (e->pos().y() - mspress.y())*0.5*ippm;
      mspress = e->pos();
      xdorg -= dx;
      ydorg += dy;
      span += sq(dx) + sq(dy);
      displace();
      break;
      
    case SkvZoom:
      dx = e->pos().x() - mspress.x();
      dy = e->pos().y() - mspress.y();
      mspress = e->pos();
      zf = 1.0 + dy/height();
      xdorg += 0.5*width()*ippm*(1.0 - 1.0/zf);
      ppm *= zf;
      displace();
      break;
      
    case SkvMove:
      dx = (e->pos().x() - mspress.x())*ippm;
      dy = symlock ? 0.0 : (e->pos().y() - mspress.y())*ippm;
      mspress = e->pos();
      fhdl[iselect].move(dx, -dy);
      fhdl[iselect].replace(QPointF(xdorg,ydorg), ppm);
      repaint();
      postFramePosition(iselect, 0.0);
      emit xFrameMoved(iselect, dx);      
      break;
      
    case SkvModTop:
      dy = (e->pos().y() - mspress.y())*ippm;
      mspress = e->pos();
      if (symlock) {
        fhdl[iselect].moveTop(-dy);
        fhdl[iselect].moveBot( dy);
      } else
        fhdl[iselect].moveTop(-dy);
      fhdl[iselect].replace(QPointF(xdorg,ydorg), ppm);
      repaint();
      postFramePosition(iselect, 0.5);
      break;
      
    case SkvModBot:
      dy = (e->pos().y() - mspress.y())*ippm;
      mspress = e->pos();
      if (symlock) {
        fhdl[iselect].moveTop( dy);
        fhdl[iselect].moveBot(-dy);
      } else
        fhdl[iselect].moveBot(-dy);
      fhdl[iselect].replace(QPointF(xdorg,ydorg), ppm);
      repaint();
      postFramePosition(iselect, -0.5);
      break;
      
    default:
      break;
  }
  
  // QWidget::mouseMoveEvent(e);
}

void SkeletonView::mouseReleaseEvent(QMouseEvent *)
{
  switch (act) {
  
    case SkvPan:
      if (span == 0) {
        contextMenu();
      } else {
        ++nzoom;
      }
      break;
      
    case SkvZoom:
      ++nzoom;
      break;
      
    case SkvMove:
    case SkvModTop:
    case SkvModBot:
      emit frameModified(iselect);
      break;
      
    default:
      break;
    
  }
  
  setCursor(Qt::ArrowCursor);
  act = SkvNone;
  iselect = -1;
  
  // QWidget::mouseReleaseEvent(e);
}

void SkeletonView::wheelEvent(QWheelEvent *e)
{
  double steps = e->delta() / 120.;
  double zf = 1.0 - 0.2*steps;
  xdorg += 0.5*width()*(1.0 - 1.0/zf)/ppm;
  ppm *= zf;
  displace();
}

