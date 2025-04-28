
/* ------------------------------------------------------------------------
 * file:       frameeditor.cpp
 * copyright:  (c) 2006 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Widget for interactive modification of interpolation frames
 * ------------------------------------------------------------------------ */

#include "editframeproperties.h"
#include "frameeditor.h"
#include "bodyskeleton.h"

#include <QPainter>
#include <QLineEdit>
#include <QPaintEvent>
#include <QResizeEvent>
#include <QMouseEvent>
#include <QWheelEvent>
#include <QDoubleValidator>
#include <QMenu>
#include <QAction>
#include <QPixmap>
#include <QImageReader>
#include <QFileDialog>
#include <QMessageBox>

using namespace std;

FrameEditor::FrameEditor(QWidget *parent) : QFrame(parent), efp(0)
{
  iEdit = iFront = iBack = iSelect = -1;
  nzoom = 0;
  act = FeNone;
  symlock = false;
  ctrlpts = false;

  // enable focus 
  QWidget::setFocusPolicy(Qt::StrongFocus);
  QFrame::setFrameStyle( QFrame::StyledPanel | QFrame::Plain );
  
  // construct pixmaps
  origim = new QPixmap;
  trfim = new QPixmap;
  drawbgi = false;
  
  // construct actions
  initActions();
}

void FrameEditor::initActions()
{
  ctmenu = new QMenu(this);
  
  actEditProp = ctmenu->addAction( tr("Edit frame properties"),
                                  this, SLOT(editProperties()) );
  actUnconstrain = ctmenu->addAction( tr("Release shape constraint"),
                                     this, SLOT(eraseConstraint()) );
  actNextFrame = ctmenu->addAction( tr("Go to next frame"),
                                   this, SLOT(nextFrame()) );
  actPrevFrame = ctmenu->addAction( tr("Go to previous frame"),
                                   this, SLOT(prevFrame()) );
  //   actCtrlPoints = ctmenu->addAction( tr("Show control points"),
  //                                       this, SLOT(toggleControlPoints()) );
  //   actCtrlPoints->setCheckable(true);
  actInsertPoint = ctmenu->addAction( tr("Insert point here"),
                                     this, SLOT(insertPoint()) );
  actRemovePoint = ctmenu->addAction( tr("Remove nearest point"),
                                     this, SLOT(removePoint()) );
  
  actLoadBgi = ctmenu->addAction( tr("&Load background image"), this,
                                 SLOT(loadBackgroundImage()) );
  
  // on construction, there is no background image, disabled
  actToggleBgi = ctmenu->addAction( tr("Toggle &background image"), this,
                                   SLOT(toggleBackgroundImage()) );
  actToggleBgi->setEnabled(false);
  actToggleBgi->setCheckable(true);

  // project a single point to overlay geometry
  actProjectPoint = ctmenu->addAction( tr("Project nearest point to overlay"),
                                      this, SLOT(projectPoint()) );

  // project interpolation points to overlay geometry
  actProjectAll = ctmenu->addAction( tr("Fit frame to overlay (F)"),
                                    this, SLOT(projectPoints()) );
}

void FrameEditor::setProjector(FrameProjectorPtr pp)
{
  pfpj = pp;
  bool havePj = (pfpj) and (not pfpj->empty());
  actProjectPoint->setEnabled( havePj );
  actProjectAll->setEnabled( havePj );
}

void FrameEditor::contextMenu()
{
  // TODO : Enable/disable menu entries based on position
  ctmenu->exec( mapToGlobal(mspress) );
}

void FrameEditor::setFrame(const BodySkeletonPtr & sp, int iframe)
{
  bsp = sp;
  iEdit = iframe;
  
  if (not bsp) {
    repaint();
    return;
  }
  
  assert(sp);
  assert(iframe >= 0);
  assert(uint(iframe) < sp->nframes());
  
  if (iframe > 0)
    iFront = iEdit-1;
  else
    iFront = -1;
  if (uint(iframe+1) < sp->nframes())
    iBack = iEdit+1;
  else
    iBack = -1;

  build();
}

void FrameEditor::fetch(uint ifr, QPolygonF & hdl, QPolygonF & cv) const
{
  if (not bsp)
    return;
  
  // compute position of interpolation points in 3D
  const BodyFrame & bf(*bsp->frame(ifr));
  if (ctrlpts) {
    
    const PointList<3> & cp( bf.curve()->controls() );
    const int ncp(cp.size()/2 + 1);
    hdl.resize(ncp);
    for (int i=0; i<ncp; ++i) {
      Real y = cp[i][1];
      Real z = cp[i][2];
      hdl[i] = QPointF(y,z);
    }  
    
  } else {
    
    const Vct3 & forg(bf.origin());
    Real w = bf.frameWidth();
    Real h = bf.frameHeight();
    const PointList<2> & rip(bf.riPoints());
    const int nh(rip.size());
    hdl.resize(nh);
    for (int i=0; i<nh; ++i) {
      Real y = forg[1] + 0.5*w*rip[i][0];
      Real z = forg[2] + 0.5*h*rip[i][1];
      hdl[i] = QPointF(y,z);
    }
  }
  
  // curve points
  PointList<3> cpt;
  bf.revaluate(cpt);
  const int nc(cpt.size());
  cv.resize(nc);
  for (int i=0; i<nc; ++i)
    cv[i] = QPointF(cpt[i][1], cpt[i][2]);
}

void FrameEditor::build()
{
  if (not bsp)
    return;
  
  if (pfpj != 0 and (not pfpj->empty()) and iEdit != -1) {
    Plane fplane = bsp->frame(iEdit)->framePlane();
    Vct3 po = fplane.vector() * fplane.offset() + bsp->origin();
    pfpj->intersect( Plane(fplane.vector(), dot(po, fplane.vector())),
                    segments );
    modelSpaceSegments();
  } else {
    segments.clear();
    opps.clear();
  }

  QPolygonF key, curve;
  if (iEdit != -1) {
    fetch(iEdit, key, curve);
    fpEdit.init(key, curve);
    if (not segments.empty())
      fpEdit.setOverlay(opps);
    fpEdit.editable( true );
    fpEdit.shapeConstrained( bsp->frame(iEdit)->shapeConstraint() != 0 );
    fpEdit.setCurveColor( Qt::darkBlue );
  }
  
  if (iFront != -1) {
    fetch(iFront, key, curve);
    fpFront.init(key, curve);
    fpFront.editable( false );
    fpFront.setCurveColor( Qt::darkGreen );
  }

  if (iBack != -1) {
    fetch(iBack, key, curve);
    fpBack.init(key, curve);
    fpBack.editable( false );
    fpBack.setCurveColor( Qt::darkRed );
  }
  
  // const BodyFrame & bf(*bsp->frame(iEdit));
  // iLastHandle = bf.riPoints().size() - 1;
  iLastHandle = fpEdit.nHandles() - 1;
  
  actUnconstrain->setEnabled( bsp->frame(iEdit)->shapeConstraint() != 0 );
  
  fitView();
}

void FrameEditor::modelSpaceSegments()
{
  opps.clear();
  if (pfpj == 0)
    return;

  PointList<3> sps;
  pfpj->modelSpaceSegments(segments, sps);

  const Vct3 & org( bsp->origin() );

  const int np = sps.size();
  opps.resize(np);
  for (int i=0; i<np; ++i)
    opps[i] = QPointF( sps[i][1]-org[1], sps[i][2]-org[2] );
}

void FrameEditor::fitView()
{
  if (not bsp)
    return;
  
  // size in physical coordinates 
  Vct2 yzmin, yzmax;
  yzmin = huge;
  yzmax = -huge;
  frameDimensions(iEdit, yzmin, yzmax);
  if (iFront > -1)
    frameDimensions(iFront, yzmin, yzmax);
  if (iBack > -1)
    frameDimensions(iBack, yzmin, yzmax);
  
  Real twidth = yzmax[0] - yzmin[0];
  Real theight = yzmax[1] - yzmin[1];
  Real yctr = 0.5*(yzmin[0] + yzmax[0]);
  Real zctr = 0.5*(yzmin[1] + yzmax[1]);
  
  qreal w = width();
  qreal h = height();
  ppm = 0.9*min(w/twidth, h/theight);
  dorg = QPointF(yctr, zctr);
  displace();
  
  nzoom = 0;
}

void FrameEditor::nextFrame()
{
  if (not bsp)
    return;
  
  int lastframe = bsp->nframes() - 1;
  if (iEdit < lastframe) {
    iEdit++;
    iFront++;
    if (iEdit < lastframe)
      iBack++;
    else
      iBack = -1;
    build();
  } 
  
  if (efp != 0)
    efp->setFrame(bsp->frame(iEdit));
}

void FrameEditor::prevFrame()
{
  if (not bsp)
    return;
  
  int lastframe = bsp->nframes() - 1;
  if (iEdit > 0) {
    iEdit--;
    if (iEdit == lastframe-1)
      iBack = lastframe;
    else
      iBack--;
    if (iEdit > 0)
      iFront--;
    else
      iFront = -1;
    build();
  }
  
  if (efp != 0)
    efp->setFrame(bsp->frame(iEdit));
}

void FrameEditor::frameDimensions(int i, Vct2 & yzmin, Vct2 & yzmax) const
{
  if (not bsp)
    return;
  
  const BodyFrame & bf( *bsp->frame(i) );
  const Vct3 & org( bf.origin() );
  Real w = bf.frameWidth();
  Real h = bf.frameHeight();
  yzmin[0] = min(yzmin[0], org[1]-0.5*w);
  yzmin[1] = min(yzmin[1], org[2]-0.5*h);
  yzmax[0] = max(yzmax[0], org[1]+0.5*w);
  yzmax[1] = max(yzmax[1], org[2]+0.5*h);
}

void FrameEditor::displace() 
{
  if (not bsp)
    return;
  
  if (iEdit > -1)
    fpEdit.replace(dorg, ppm);
  if (iFront > -1)
    fpFront.replace(dorg, ppm);
  if (iBack > -1)
    fpBack.replace(dorg, ppm);
  
  repaint();
}

int FrameEditor::selectHandle()
{
  if (not bsp)
    return -1;
  
  QPointF tpos( 0.5*width()-mspress.x(), 
               0.5*height()-mspress.y() );
  iSelect = fpEdit.onHandle(tpos);
  
  if (iSelect != -1) 
    act = FeMove;
  else
    act = FeNone;
  
  if (iSelect == 0 or iSelect == iLastHandle)
    symlock = true;
  else
    symlock = false;
  
  return iSelect; 
}

void FrameEditor::updateDrawing()
{
  if (not bsp)
    return;
  
  QPolygonF key, curve;
  if (iEdit != -1) {
    fetch(iEdit, key, curve);
    fpEdit.init(key, curve);
    if (not segments.empty())
      fpEdit.setOverlay(opps);
    fpEdit.replace(dorg, ppm);
    fpEdit.shapeConstrained( bsp->frame(iEdit)->shapeConstraint() != 0);
  }
  iLastHandle = fpEdit.nHandles() - 1;
  
  repaint();
}

void FrameEditor::interpolate()
{
  if (not bsp)
    return;
  
  if (iSelect > -1) {
    
    // replace modified point with screen point 
    BodyFrame & bf(*bsp->frame(iEdit));
    const QPointF & npos(fpEdit.position(iSelect));
    
    if (ctrlpts) {
      PointList<3> & cp( bf.curve()->controls() );
      cp[iSelect][1] = npos.x();
      cp[iSelect][2] = npos.y();
      
      // retain symmetry 
      const int ncp = cp.size();
      const int iop = ncp-1-iSelect;
      cp[iop][1] = -npos.x();
      cp[iop][2] =  npos.y();
      
      bf.evalIpp();
    } else {
      const Vct3 & org(bf.origin());
      Real w = bf.frameWidth();
      Real h = bf.frameHeight();
      
      PointList<2> & rip(bf.riPoints());
      rip[iSelect][0] = 2*(npos.x() - org[1]) / w;
      rip[iSelect][1] = 2*(npos.y() - org[2]) / h;
      
      bf.interpolate();
    }
    bsp->interpolate();
    
    updateDrawing();
    emit geometryChanged();
  }
}

void FrameEditor::postMousePos()
{
  double ippm = 1./ppm;
  double x = dorg.x() + (0.5*width() - mspress.x())*ippm;
  double y = dorg.y() + (0.5*height() - mspress.y())*ippm;
  QString s;
  s += " x: " + QString::number(x, 'f', 4);
  s += " z: " + QString::number(y, 'f', 4);
  emit postStatusMessage(s);
}

void FrameEditor::insertPoint()
{
  if (not bsp)
    return;
  
  Vct2 sp;
  sp[0] = dorg.x() + (0.5*width() - mspress.x())/ppm;
  sp[1] = dorg.y() + (0.5*height() - mspress.y())/ppm;
  
  BodyFrame & bf(*bsp->frame(iEdit));
  const Vct3 & org(bf.origin());
  sp[0] = 2*(sp[0] - org[1]) / bf.frameWidth();
  sp[1] = 2*(sp[1] - org[2]) / bf.frameHeight();
  bf.insertPoint(sp);
  bf.interpolate();
  bsp->interpolate();
  
  updateDrawing();
  emit geometryChanged();
}

void FrameEditor::removePoint()
{
  if (not bsp)
    return;
  
  Vct2 sp;
  sp[0] = dorg.x() + (0.5*width() - mspress.x())/ppm;
  sp[1] = dorg.y() + (0.5*height() - mspress.y())/ppm;
  
  BodyFrame & bf(*bsp->frame(iEdit));
  const Vct3 & org(bf.origin());
  sp[0] = 2*(sp[0] - org[1]) / bf.frameWidth();
  sp[1] = 2*(sp[1] - org[2]) / bf.frameHeight();
  bf.removePoint(sp);
  bf.interpolate();
  bsp->interpolate();
  
  updateDrawing();
  emit geometryChanged();
}

void FrameEditor::projectPoint()
{
  if (not bsp or iEdit < 0)
    return;
  if (pfpj == 0 or pfpj->empty())
    return;

  eraseConstraint();

  Vct2 sp;
  sp[0] = dorg.x() + (0.5*width() - mspress.x())/ppm;
  sp[1] = dorg.y() + (0.5*height() - mspress.y())/ppm;

  BodyFrame & bf(*bsp->frame(iEdit));
  const Vct3 & org(bf.origin());
  sp[0] = 2*(sp[0] - org[1]) / bf.frameWidth();
  sp[1] = 2*(sp[1] - org[2]) / bf.frameHeight();

  // keep a copy of the old point if something should go wrong
  PointList<2> & rpt(bf.riPoints());
  uint ipt = bf.nearestRPoint(sp);
  Vct2 ro = rpt[ipt];

  try {
    bsp->projectPoint(*pfpj, segments, iEdit, ipt);
    bf.interpolate();
    bsp->interpolate();
  } catch (Error & xcp) {
    rpt[ipt] = ro;
    bf.interpolate();
    bsp->interpolate();

    QMessageBox::information(this, tr("Point projection failed."),
                             tr("This particular point cannot be projected  "
                                "to the overlay geometry as it ends up in the "
                                "same projected position as another existing point. "
                                "Move point before projection. <br><br> "
                                "Error message: ")
                             + QString::fromStdString(xcp.what()));
  }

  updateDrawing();
  emit geometryChanged();
}

void FrameEditor::projectPoints()
{
  if (not bsp or iEdit < 0)
    return;
  if (pfpj == 0 or pfpj->empty())
    return;

  eraseConstraint();

  // distance tolerance for projection
  BodyFrame & bf( *bsp->frame(iEdit) );

  // safeguard: keep old points
  PointList<2> rpts = bf.riPoints();

  Real fh = bf.frameHeight();
  Real fw = bf.frameWidth();
  Real maxdst = 0.25*std::min(fh, fw);

  try {
    bsp->projectPoints(*pfpj, segments, iEdit, maxdst);
    bf.interpolate();
    bsp->interpolate();
  } catch (Error & xcp) {
    bf.riPoints() = rpts;
    bf.interpolate();
    bsp->interpolate();

    QMessageBox::information(this, tr("Frame fitting failed."),
                             tr("This frame cannot be adapted to match "
                                "overlay geometry entirely. Try to modify "
                                "its shape manually to better fit the overlay "
                                "or fit individual points.<br><br> "
                                "Error message: ")
                             + QString::fromStdString(xcp.what()));
  }

  updateDrawing();
  emit geometryChanged();
}

bool FrameEditor::editProperties()
{
  if (not bsp)
    return false;
  
  efp = new EditFrameProperties(this, bsp, bsp->frame(iEdit));
  connect(efp, SIGNAL(frameShapeChanged()), this, SIGNAL(geometryChanged()));
  connect(efp, SIGNAL(frameShapeChanged()), this, SLOT(updateDrawing()));
  connect(efp, SIGNAL(frameShapeChanged()), this, SLOT(fitView()));
  connect(efp, SIGNAL(previousFramePlease()), this, SLOT(prevFrame()) );
  connect(efp, SIGNAL(nextFramePlease()), this, SLOT(nextFrame()) );
  bool acc = (efp->exec() == QDialog::Accepted);
  
  delete efp;
  efp = 0;
  
  return acc;
}

void FrameEditor::toggleControlPoints()
{
  ctrlpts = !ctrlpts;
  actCtrlPoints->setChecked(ctrlpts);
  // actInsertPoint->setDisabled(ctrlpts);
  // actRemovePoint->setDisabled(ctrlpts);
  fpEdit.drawEdges(ctrlpts);
  updateDrawing();
}

void FrameEditor::eraseConstraint()
{
  if ((not bsp) or iEdit == -1)
    return;
  
  bsp->frame(iEdit)->eraseConstraint();
  fpEdit.shapeConstrained(false);
  actUnconstrain->setEnabled(false);
  repaint();
}

void FrameEditor::loadBackgroundImage()
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

void FrameEditor::toggleBackgroundImage()
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

void FrameEditor::fitBackgroundImage(int w, int h)
{
  if ((not drawbgi) or (origim->isNull()))
    return;
  
  *trfim = origim->scaled(w, h, Qt::KeepAspectRatio, 
                          Qt::SmoothTransformation);
}

void FrameEditor::mousePressEvent(QMouseEvent *e)
{
  switch (e->button()) {
  
  case Qt::LeftButton:
    mspress = e->pos();
    selectHandle();
    postMousePos();
    break;

  case Qt::MidButton:
    if (e->type() == QEvent::MouseButtonDblClick) {
      fitView();
    } else {
      act = FeZoom;
      mspress = e->pos();
    }
    break;

  case Qt::RightButton:
    mspress = e->pos();
    act = FePan;
    setCursor(Qt::ClosedHandCursor);
    span = 0;
    break;

  default:
    break;
  }
  
}

void FrameEditor::mouseMoveEvent(QMouseEvent *e)
{
  qreal dx, dy, zf, ippm(1./ppm);
  switch (act) {

  case FePan:
    dx = (e->pos().x() - mspress.x())*0.5*ippm;
    dy = (e->pos().y() - mspress.y())*0.5*ippm;
    mspress = e->pos();
    dorg.rx() += dx;
    dorg.ry() += dy;
    span += sq(dx) + sq(dy);
    displace();
    break;

  case FeZoom:
    dx = e->pos().x() - mspress.x();
    dy = e->pos().y() - mspress.y();
    mspress = e->pos();
    zf = 1.0 + dy/height();
    ppm *= zf;
    displace();
    break;

  case FeMove:
    dx = (e->pos().x() - mspress.x())*ippm;
    dy = (e->pos().y() - mspress.y())*ippm;
    dx = ( symlock ? 0.0 : dx );
    mspress = e->pos();
    fpEdit.move(iSelect, -dx, -dy);
    repaint();
    postMousePos();
    break;

  default:
    break;
  }
}

void FrameEditor::mouseReleaseEvent(QMouseEvent *e)
{
  switch (act) {

  case FePan:
    if (span == 0) {
      mspress = e->pos();
      contextMenu();
    } else {
      ++nzoom;
    }
    break;

  case FeZoom:
    ++nzoom;
    break;

  case FeMove:
    interpolate();
    break;

  case FeNone:
  default:
    break;
  }
  
  setCursor(Qt::ArrowCursor);
  act = FeNone;
  iSelect = -1;
}

void FrameEditor::wheelEvent(QWheelEvent *e)
{
  double steps = e->delta() / 120.;
  double zf = 1.0 - 0.2*steps;
  ppm *= zf;
  displace();
}

void FrameEditor::resizeEvent(QResizeEvent *e)
{
  fitView();

  // transform background image to fit the new widget size 
  fitBackgroundImage(e->size().width(), e->size().height());
}

void FrameEditor::keyPressEvent(QKeyEvent *e)
{
  if (not bsp)
    return;
  
  switch (e->key()) {
  
  case Qt::Key_Plus:
    nextFrame();
    e->accept();
    break;
    
  case Qt::Key_Minus:
    prevFrame();
    e->accept();
    break;

  case Qt::Key_F:
    projectPoints();
    e->accept();
    break;

  default:
    // cerr << "Keycode: " << e->key() << endl;
    break;
  }
}

void FrameEditor::paintEvent(QPaintEvent *e)
{
  QPainter painter(this);
  
  // use antialiasing for everything
  painter.setRenderHint(QPainter::Antialiasing);
  
  // fill background with white 
  QRect paintRect = QWidget::contentsRect();
  painter.fillRect(paintRect, palette().color(QPalette::Base));
  if (drawbgi and (not trfim->isNull())) {
    int imx = (width() - trfim->width()) / 2;
    int imy = (height() - trfim->height()) / 2;
    painter.drawPixmap(QPoint(imx,imy), *trfim);
  }

  // move origin and make y point upward
  painter.translate(0.5*width(), 0.5*height());
  painter.scale(-1.0, -1.0);

  // draw defined frames
  if (bsp) {
    if (iFront > -1)
      fpFront.paint( &painter );
    if (iBack > -1)
      fpBack.paint( &painter );
    if (iEdit > -1)
      fpEdit.paint( &painter );
  }

  painter.end();

  QFrame::paintEvent(e);
}




