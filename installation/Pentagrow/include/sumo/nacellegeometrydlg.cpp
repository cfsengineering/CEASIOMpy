
/* ------------------------------------------------------------------------
 * file:       nacellegeometrydlg.cpp
 * copyright:  (c) 2009 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Define engine nacelle geometry
 * ------------------------------------------------------------------------ */

#include "nacellegeometrydlg.h"
#include "ui_nacellegeometrydlg.h"
#include "bodyskeleton.h"

bool NacelleGeometryDlg::bShown = false;

NacelleGeometryDlg::NacelleGeometryDlg(QWidget *parent, BodySkeleton & b) :
    QDialog(parent), body(b),
    m_ui(new Ui::NacelleGeometryDlg)
{
  bShown = true;
  m_ui->setupUi(this);

  // use as non-modal widget
  QWidget::setAttribute(Qt::WA_DeleteOnClose, true);

  bool flag = body.inletLip();
  m_ui->cbGenerateLip->setChecked( flag );
  if (flag) {
    m_ui->sbAxialOffset->setValue(body.axialLipOffset());
    m_ui->sbRadialOffset->setValue(body.radialLipOffset());
    m_ui->sbShapeCoef->setValue(body.shapeCoefLip());
  }

  connect(m_ui->pbApply, SIGNAL(clicked()), this, SLOT(apply()));
}

NacelleGeometryDlg::~NacelleGeometryDlg()
{
  bShown = false;
  delete m_ui;
}

void NacelleGeometryDlg::apply()
{
  if ( m_ui->cbGenerateLip->isChecked() ) {
    body.inletLip(true);
    body.axialLipOffset( m_ui->sbAxialOffset->value() );
    body.radialLipOffset( m_ui->sbRadialOffset->value() );
    body.shapeCoefLip( m_ui->sbShapeCoef->value() );
  } else {
    body.inletLip(false);
  }

  body.interpolate();
  emit geometryChanged();
}

void NacelleGeometryDlg::changeEvent(QEvent *e)
{
    QDialog::changeEvent(e);
    switch (e->type()) {
    case QEvent::LanguageChange:
        m_ui->retranslateUi(this);
        break;
    default:
        break;
    }
}
