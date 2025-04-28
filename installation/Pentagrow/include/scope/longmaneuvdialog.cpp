
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
 
#include "longmaneuvdialog.h"
#include "ploaddialog.h"
#include <genua/atmosphere.h>
#include <genua/smallqr.h>
#include <QDebug>
#include <QMessageBox>

using namespace std;

LongManeuvDialog::LongManeuvDialog(QWidget *parent) :
  QDialog(parent)
{
  cplDlg = 0;
  setupUi(this);

  // cosmetic changes
  sbWingLoading->setSuffix( QString(" kg/sqm") );

  // default values used when actual parameters are not present
  refAlpha = 0;
  refChord = 1.0;
  Czo = 0.5;
  Cza = 4.5;
  Czq = 2.0;
  CzDe = 0.0;
  Cmo = 0.0;
  Cma = -0.1;
  Cmq = -5.0;
  CmDe = 0.0;

  // update derived properties
  connect( sbLoadFactor, SIGNAL(editingFinished()), this, SLOT(derive()));
  connect( sbMachNumber, SIGNAL(editingFinished()), this, SLOT(derive()));
  connect( sbAltitude, SIGNAL(editingFinished()), this, SLOT(derive()));
  connect( sbWingLoading, SIGNAL(editingFinished()), this, SLOT(derive()));
  connect( sbCgOffset, SIGNAL(editingFinished()), this, SLOT(derive()));

  // proceed to next stage
  connect( pbNext, SIGNAL(clicked()), this, SLOT(nextStep()) );
}

bool LongManeuvDialog::assign(const MxMeshPtr &amsh)
{
  amp = amsh;
  if (not amp)
    return false;

  try {

    // extract reference values and force coefficients
    Vct6 cf;
    XmlElement::const_iterator itn, nlast = amp->noteEnd();
    for (itn = amp->noteBegin(); itn != nlast; ++itn) {
      if (itn->name() == "Reference") {
        refAlpha = itn->attr2float("alpha", 0.0);
        refChord = itn->attr2float("chord", 1.0);
        fromString( itn->attribute("point"), refPoint );
      } else if (itn->name() == "ForceCoefficients") {
        const string & id = itn->attribute("id");
        itn->fetch(6, cf.pointer());
        if (id == "Reference") {
          Czo = cf[2];
          Cmo = cf[4];
        } else if (id == "Alpha") {
          Cza = cf[2];
          Cma = cf[4];
        } else if (id == "PitchRate") {
          Czq = cf[2];
          Cmq = cf[4];
        } else if (id == "Elevator") {
          CzDe = cf[2];
          CmDe = cf[4];
        }
      }
    }

    const int nfield = 3;
    ifield.resize(nfield);
    const char* fieldNames[] = {"CoefPressure", "DeltaCp: Alpha",
                                "DeltaCp: PitchRate"};
    for (int i=0; i<nfield; ++i) {
      ifield[i] = amp->findField(fieldNames[i]);
      if (ifield[i] == NotFound)
        throw Error( string("Data field not found in mesh: ") + fieldNames[i] );
    }

  } catch (Error & xcp) {
    QString title = tr("Incompatible mesh.");
    QString xmsg = QString::fromStdString(xcp.what());
    QString text = tr("Cannot use current aerodynamic mesh for load "
                      "interpolation. Error: %1").arg(xmsg);
    QMessageBox::information( this, title, text );
    return false;
  }

  return true;
}

void LongManeuvDialog::derive()
{
  double nz = sbLoadFactor->value();
  double mach = sbMachNumber->value();
  double altm = 1000 * sbAltitude->value();
  double ws = 9.81 * sbWingLoading->value();
  double dx = sbCgOffset->value();

  const double g = 9.81;
  Atmosphere isa(altm, 0.0);
  double uoo = mach * isa.Aoo;
  qoo = 0.5*sq(uoo) * isa.Rho;

  // non-dimensional pitch rate from kinematics
  qhat = 0.5*refChord*g*(nz - 1.0) / sq(uoo);
  double qdim = qhat * 2*uoo/refChord;
  Cz = nz * ws / qoo;

  bool useElevator = false;

  if (CmDe == 0) {

    // angle of attack from force balance
    alpha = refAlpha + ( Cz - Czo - Czq*qhat ) / Cza;
    deltaElevator = 0.0;

  } else {

    // solve for alpha and delta using normal force and pitch moment balance
    SMatrix<2,2> A;
    A(0,0) = Cza;
    A(0,1) = CzDe;
    A(1,0) = Cma;
    A(1,1) = CmDe;

    SVector<2> b;
    b[0] = Cz - Czo - Czq*qhat;
    b[1] = - Cz*dx - Cmo - Cmq*qhat;

    bool qrok = qrlls<2,2>(A.pointer(), b.pointer());
    if (qrok) {
      alpha = refAlpha + b[0];
      deltaElevator = b[1];
      useElevator = true;
    } else {
      alpha = rad(100.);
      deltaElevator = rad(100.);
    }
  }

  // update UI
  double qdeg = qdim * 180/M_PI;
  double adeg = alpha * 180/M_PI;
  double dedeg = deltaElevator * 180/M_PI;
  double ktas = uoo *3.6/1.852;
  lbTAS->setText(QString("%1 kts").arg(ktas, 0, 'g', 3) );
  lbPitchRate->setText( QString("%1 deg/s").arg(qdeg, 0, 'g', 3) );
  lbAlpha->setText( QString("%1 deg").arg(adeg, 0, 'g', 3) );
  lbCz->setText( QString("%1").arg(Cz, 0, 'g', 3) );
  if (useElevator)
    lbDeltaElevator->setText( QString("%1 deg").arg(dedeg, 0, 'g', 3) );
  else
    lbDeltaElevator->setText( tr("(n/a)") );
}

void LongManeuvDialog::nextStep()
{
  // in order to avoid passing one more argument, the dynamic pressure
  // is multiplied into the coefficients for the Cp fields
  Vector coef(3);
  coef[0] = 1.0 * qoo;
  coef[1] = (alpha - refAlpha) * qoo;
  coef[2] = qhat * qoo;

  if (cplDlg == 0) {
    cplDlg = new PLoadDialog(this);
    connect(cplDlg, SIGNAL(displayMesh(MxMeshPtr)),
            this, SIGNAL(displayMesh(MxMeshPtr)));
  }

  cplDlg->assign(amp, ifield, coef);
  cplDlg->show();
}

void LongManeuvDialog::changeEvent(QEvent *e)
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
