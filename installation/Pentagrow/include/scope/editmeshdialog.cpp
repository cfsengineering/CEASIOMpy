
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
 
#include "editmeshdialog.h"
#include "meshplotter.h"
#include <genua/mxmesh.h>

EditMeshDialog::EditMeshDialog(QWidget *parent) : QDialog(parent, Qt::Tool)
{
  setupUi(this);

#ifdef Q_OS_MACX
  gbStatistics->setFlat(true);
  gbPathBox->setFlat(true);
  gbNote->setFlat(true);
#endif

  connect(pbLoadPath, SIGNAL(clicked()), this, SIGNAL(loadTrajectory()));
  connect(pbErasePath, SIGNAL(clicked()), this, SLOT(erasePath()));
  connect(cbSelectPath, SIGNAL(currentIndexChanged(int)),
          this, SLOT(selectPath(int)));

  // make xml display model delete references to mesh annotation when
  // dialog closed
  connect(this, SIGNAL(finished(int)),
          xmlDisplay, SLOT(detach()));
}

void EditMeshDialog::assign(MeshPlotterPtr pm)
{
  plotter = pm;
  if (not plotter)
    return;
  pmsh = pm->pmesh();
  if (not pmsh)
    return;

  QLocale loc;
  lbNodeCount->setText( loc.toString( pmsh->nnodes() ) );
  lbElementCount->setText( loc.toString( pmsh->nelements() ) );
  lbSectionCount->setText( loc.toString( pmsh->nsections() ) );
  lbGroupCount->setText( loc.toString( pmsh->nbocos() ) );
  lbFieldCount->setText( loc.toString( pmsh->nfields() ) );
  countPrimitives();

  const int npath = pmsh->ndeform();
  cbSelectPath->clear();
  for (int i=0; i<npath; ++i)
    cbSelectPath->addItem( QString::fromStdString(pmsh->deform(i).name()) );

  if (npath == 0)
    gbPathBox->hide();
  else
    gbPathBox->show();


  // disabled, will crash when loading new mesh
  // gbNote->hide();

  note = pmsh->note();
  xmlDisplay->display( &note );
  const uint noteSize = std::distance(note.begin(), note.end());
  if (noteSize > 0) {
    gbNote->show();
  } else {
    gbNote->hide();
  }

  adjustSize();
}

void EditMeshDialog::countPrimitives()
{
  if (not plotter)
    return;

  qulonglong ntri(0), nedg(0), nvtx(0);
  qulonglong nsec = pmsh->nsections();
  for (size_t i=0; i<nsec; ++i) {
    const SectionPlotter & sp( plotter->section(i) );
    if (sp.visible()) {
      ntri += sp.nVisibleTriangles();
      nedg += sp.nVisibleEdges();
      nvtx += sp.vertices().size();
    }
  }

  QLocale loc;
  lbVisTriangleCount->setText( loc.toString(ntri) );
  lbVisEdgeCount->setText( loc.toString(nedg) );
  lbVisVertexCount->setText( loc.toString(nvtx) );
}

void EditMeshDialog::selectPath(int i)
{
  if ((not pmsh) or (uint(i) > pmsh->ndeform()))
    return;
  Real T = pmsh->deform(i).duration();
  lbPathDuration->setText( QString::number(T) + "s" );
}

void EditMeshDialog::erasePath()
{
  int i = cbSelectPath->currentIndex();
  if ((not pmsh) or (uint(i) > pmsh->ndeform()))
    return;

  pmsh->eraseDeform(i);
  cbSelectPath->removeItem(i);
}

void EditMeshDialog::changeEvent(QEvent *e)
{
  QDialog::changeEvent(e);
  switch (e->type()) {
  case QEvent::LanguageChange:
    retranslateUi(this);
    break;
  default:
    break;
  }
}
