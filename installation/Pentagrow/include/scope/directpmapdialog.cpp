
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
 
#include "directpmapdialog.h"
#include "ploaddialog.h"
#include <genua/atmosphere.h>

using namespace std;

DirectPMapDialog::DirectPMapDialog(QWidget *parent) :
  QDialog(parent, Qt::Tool), cplDlg(0)
{
  setupUi(this);

  cplDlg = new PLoadDialog(this);
  connect(cplDlg, SIGNAL(displayMesh(MxMeshPtr)),
          this, SIGNAL(displayMesh(MxMeshPtr)));

  // buttons
  connect(pbNext, SIGNAL(clicked()), this, SLOT(nextStep()));

  // spin boxes
  connect(sbAltitude, SIGNAL(editingFinished()),
          this, SLOT(altChanged()));
  connect(sbAirspeed, SIGNAL(editingFinished()),
          this, SLOT(airspeedChanged()));
  connect(cbSpeedUnit, SIGNAL(currentIndexChanged(int)),
          this, SLOT(unitChanged()));
  connect(rbSpecQ, SIGNAL(clicked()),
          this, SLOT(showDynamicPressure()));

  sispeed = sbAirspeed->value() * siSpeedConversion();
  showDynamicPressure();
}

bool DirectPMapDialog::assign(MxMeshPtr amesh)
{
  amp = amesh;
  if (not amp)
    return false;

  // add scalar data field to the combo box
  cbSelectField->clear();
  ifield.clear();
  uint idx = NotFound;
  for (uint i=0; i<amesh->nfields(); ++i) {
    const MxMeshField & mf( amesh->field(i) );
    if (not mf.nodal())
      continue;
    if (mf.ndimension() != 1)
      continue;
    if (not mf.realField())
      continue;
    cbSelectField->addItem( QString::fromStdString(mf.name()) );
    ifield.push_back(i);
    if (mf.name() == "CoefPressure" or mf.name() == "pressure_coeff")
      idx = i;
  }

  if (ifield.empty())
    return false;

  if (idx != NotFound)
    cbSelectField->setCurrentIndex(idx);

  return true;
}

void DirectPMapDialog::changeSelectedField(int idx)
{
  size_t ipos = std::distance(ifield.begin(),
                              std::find(ifield.begin(), ifield.end(), idx));
  if (ipos < ifield.size())
    cbSelectField->setCurrentIndex(ipos);
}

void DirectPMapDialog::altChanged()
{
  double altkm = sbAltitude->value();
  Atmosphere atm(1000 * altkm);

  // if speed is defined by Mach, adjust
  if (cbSpeedUnit->currentIndex() == 0) {
    sispeed = sbAirspeed->value() * atm.Aoo;
  }

  double q = 0.5*atm.Rho * sq(sispeed);
  sbDynamicPressure->setValue(q);  
}

void DirectPMapDialog::airspeedChanged()
{
  double sispeed = sbAirspeed->value() * siSpeedConversion();
  Atmosphere atm(1000 * sbAltitude->value());
  double q = 0.5 * atm.Rho * sq(sispeed);
  sbDynamicPressure->setValue(q);
}

void DirectPMapDialog::unitChanged()
{
  // set according to current unit
  sbAirspeed->setValue( sispeed / siSpeedConversion() );
}

void DirectPMapDialog::nextStep()
{
  Real q = sbDynamicPressure->value();
  const uint kfield = ifield[ cbSelectField->currentIndex() ];

  // debug
  qDebug("Passing q = %f Pa", q);

  Vector qcoef;
  Indices cpFields;
  bool staticMultiCase = cbMultiCase->isChecked();
  if (staticMultiCase) {

    const string & fieldname = amp->field(kfield).name();
    for (size_t i=0; i<amp->nfields(); ++i) {
      const MxMeshField &f( amp->field(i) );
      if (not f.nodal())
        continue;
      if (f.ndimension() != 1)
        continue;
      if (f.name() == fieldname) {
        cpFields.push_back(i);
        qcoef.push_back(q);
      }
    }

    if (qcoef.size() < 2)
      staticMultiCase = false;
    qDebug("Setting up for %zu load cases.", qcoef.size());

  } else {

    // single load case
    qcoef.resize(1);
    cpFields.resize(1);
    qcoef[0] = q;
    cpFields[0] = kfield;
  }

  cplDlg->assign(amp, cpFields, qcoef, staticMultiCase);
  cplDlg->show();
}

double DirectPMapDialog::siSpeedConversion() const
{
  // order :
  // 0 : Mach
  // 1 : kts
  // 2 : km/h
  // 3 : m/s
  // 4 : mph

  Atmosphere atm( 1000 * sbAltitude->value() );

  int iunit = cbSpeedUnit->currentIndex();
  switch (iunit) {
  case 0:
    return atm.Aoo;  // Mach
  case 1:
    return 1.852 / 3.6; // knots
  case 2:
    return 1.0 / 3.6;  // km/h
  case 3:
    return 1.0; // m/s
  case 4:
    return 1.6093472 / 3.6; // mph
  default:
    return 1.0;
  }
}

void DirectPMapDialog::showDynamicPressure()
{
  if (rbSpecQ->isChecked())
    return;
  Atmosphere atm( 1000*sbAltitude->value() );
  double q = 0.5 * atm.Rho * sq(sispeed);
  sbDynamicPressure->setValue(q);
}

void DirectPMapDialog::changeEvent(QEvent *e)
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
