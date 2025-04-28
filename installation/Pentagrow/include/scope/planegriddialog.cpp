//
// project:      dwfs core
// file:
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
//

#include "planegriddialog.h"
#include "ui_planegriddialog.h"
#include "view.h"
#include "planegrid.h"

PlaneGridDialog::PlaneGridDialog(QWidget *parent, ViewManager *v) :
    QDialog(parent), view(v),
    ui(new Ui::PlaneGridDialog)
{
  ui->setupUi(this);

  connect(ui->cbPlaneX, SIGNAL(clicked(bool)),
          this, SLOT(toggleX(bool)));
  connect(ui->cbPlaneY, SIGNAL(clicked(bool)),
          this, SLOT(toggleY(bool)));
  connect(ui->cbPlaneZ, SIGNAL(clicked(bool)),
          this, SLOT(toggleZ(bool)));

  connect(ui->sbOffsetX, SIGNAL(editingFinished()),
          this, SLOT(toggleX()));
  connect(ui->sbOffsetY, SIGNAL(editingFinished()),
          this, SLOT(toggleY()));
  connect(ui->sbOffsetZ, SIGNAL(editingFinished()),
          this, SLOT(toggleZ()));
  adjustSize();

}

PlaneGridDialog::~PlaneGridDialog()
{
  delete ui;
}

void PlaneGridDialog::toggleX(bool flag)
{
  PlaneGrid & pg(view->planeGrid(0));
  pg.toggle(flag);
  if (flag) {
    Vct3f pn;
    pn[0] = 1.0f;
    pg.create(pn, ui->sbOffsetX->value(),
              view->lowCorner(), view->highCorner());
  }

   emit planesChanged();
}

void PlaneGridDialog::toggleY(bool flag)
{
  PlaneGrid & pg(view->planeGrid(1));
  pg.toggle(flag);
  if (flag) {
    Vct3f pn;
    pn[1] = 1.0f;
    pg.create(pn, ui->sbOffsetY->value(),
              view->lowCorner(), view->highCorner());
  }

   emit planesChanged();
}

void PlaneGridDialog::toggleZ(bool flag)
{
  PlaneGrid & pg(view->planeGrid(2));
  pg.toggle(flag);
  if (flag) {
    Vct3f pn;
    pn[2] = 1.0f;
    pg.create(pn, ui->sbOffsetZ->value(),
              view->lowCorner(), view->highCorner());
  }

  emit planesChanged();
}

void PlaneGridDialog::changeEvent(QEvent *e)
{
  QDialog::changeEvent(e);
  switch (e->type()) {
  case QEvent::LanguageChange:
    ui->retranslateUi(this);
    break;
  default:
    break;
  }
}
