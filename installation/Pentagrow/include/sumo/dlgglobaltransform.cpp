#include "dlgglobaltransform.h"
#include "ui_dlgglobaltransform.h"
#include <genua/svector.h>

DlgGlobalTransform::DlgGlobalTransform(QWidget *parent) :
  QDialog(parent), ui(new Ui::DlgGlobalTransform)
{
  ui->setupUi(this);
}

DlgGlobalTransform::~DlgGlobalTransform()
{
  delete ui;
}

Vct3 DlgGlobalTransform::translation() const
{
  Real x = ui->m_sbTranslateX->value();
  Real y = ui->m_sbTranslateY->value();
  Real z = ui->m_sbTranslateZ->value();
  return Vct3(x,y,z);
}

double DlgGlobalTransform::scale() const
{
  return ui->m_sbScale->value();
}
