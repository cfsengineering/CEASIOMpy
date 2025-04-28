
/* ------------------------------------------------------------------------
 * file:       sectioneditor.h
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog for wing section properties
 * ------------------------------------------------------------------------ */



// for error codes
#include <surf/naca6.h>

#include "util.h"
#include "dlgairfoil.h"
#include "sectioneditor.h"
#include "wingsection.h"
#include <genua/ioglue.h>

#include <QLineEdit>
#include <QPushButton>
#include <QLabel>
#include <QRadioButton>
#include <QFileDialog>
#include <QMessageBox>

using std::string;

QString SectionEditor::lastdir;

SectionEditor::SectionEditor(QWidget *parent, WingSectionPtr w) : 
  QDialog(parent), wsp(w)
{
  Ui::DlgEditSection::setupUi(this);
  Ui::DlgEditSection::retranslateUi(this);
  
  // create dialog and enter available data
  leName->setText(wsp->name().c_str());

  // set airfoil name
  lbCoordName->setText(wsp->airfoilName().c_str());
  
  const Vct3 & ctr(wsp->origin());
  sbPosX->setValue(ctr[0]);
  sbPosY->setValue(ctr[1]);
  sbPosZ->setValue(ctr[2]);
  sbChord->setValue(wsp->chordLength());
  sbTwist->setValue(deg(wsp->twistAngle()));
  sbDihedral->setValue(deg(wsp->dihedralAngle()));
  sbYaw->setValue(deg(wsp->yawAngle()));
  
  // interpolation/approximation
  int nap = wsp->nApprox();
  int nrp = wsp->riPoints().size();
  if (nap == -1) {
    rbInterpolate->setChecked(true);
    sbNApprox->setValue( std::max(20, std::min(60, nrp/2)) );
  } else {
    rbApproximate->setChecked(true);
    sbNApprox->setValue(nap);
  }
  
  // reverse parametrization
  cbReverseParam->setChecked( wsp->isReversed() );

  // break flag 
  cbMarkAsBreak->setChecked(wsp->isBreak());
  
  connect(pbChange, SIGNAL(clicked()), this, SLOT(genCoordinates()) );
  connect(pbLoadFile, SIGNAL(clicked()), this, SLOT(loadCoordinates()) );
  connect(pbSave, SIGNAL(clicked()), this, SLOT(saveCoordinates()) );
}

bool SectionEditor::process()
{
  // retrieve data from input fields
  string sname = leName->text().toStdString();
  Real chord = sbChord->value();
  Real twist = rad( sbTwist->value() );
  Real dihedral = rad( sbDihedral->value() );
  Real yaw = rad( sbYaw->value() );
  
  Vct3 ctr;
  ctr[0] = sbPosX->value();
  ctr[1] = sbPosY->value();
  ctr[2] = sbPosZ->value();

  // apply transformations
  wsp->rename(sname);
  wsp->origin(ctr);
  wsp->chordLength(chord);
  wsp->twistAngle(twist);
  wsp->dihedralAngle(dihedral);
  wsp->yawAngle(yaw);
  
  // appoximation/interpolation
  if (rbInterpolate->isChecked()) {
    wsp->setNApprox(-1);
  } else if (rbApproximate->isChecked()) {
    wsp->setNApprox(sbNApprox->value());
  }

  // reverse parametrization
  wsp->reverse( cbReverseParam->isChecked() );
  
  // break segments at this position 
  wsp->markAsBreak( cbMarkAsBreak->isChecked() );
  
  try {
    wsp->interpolate();
  } catch (Error & xcp) {
    string msg = xcp.what();
    QString title("Airfoil modification failure");
    QString text("<b> Geometry processing error </b> <hr>");
    text += "Interpolation/approximation of the current airfoil ";
    text += "failed with the following error:<br>";
    text += msg.c_str();
    text += " Reducing the number of approximation nodes may help.";
    QMessageBox::warning(this, title, text);
    return false;
  }
  
  return true;
}

bool SectionEditor::loadCoordinates()
{
  QString filter(tr("Coordinate files (*.txt *.dat);;All files (*.*)"));
  QString s = QFileDialog::getOpenFileName(this, tr("Open coordinate file"),
                                           lastdir, filter);
  if (!s.isNull()) {
    lastdir = QFileInfo(s).absolutePath();
    try {
      wsp->fromFile(str(s));
    } catch (Error & xcp) {
      QString msg;
      msg = tr("Failed to load airfoil coordinates from file");
      msg += "<b>" + s + "</b>.<br>";
      msg += "Error message: ";    
      msg += qstr(xcp.what());
      QMessageBox::information(this, tr("Error loading coordinates"), msg);
      return false;
    }
  } 
  
  return true;
}

bool SectionEditor::genCoordinates()
{
  DlgAirfoil dlg(this);
  dlg.setCurrentAirfoil( wsp );
  
  if (dlg.exec() == QDialog::Accepted) {
    
    try {
      
      dlg.setAirfoil( wsp );
      dlg.remember();
      
      QString afn = QString::fromStdString(wsp->airfoilName());
      lbCoordName->setText( afn );
      
    } catch (Error & xcp) {
      
      QString msg("Airfoil generation failed. Error message:\n");
      msg += QString::fromStdString(xcp.what());
      QMessageBox::warning(this, "Profile generation failure.", msg);
      
      return false;      
    }
  }
  return true;
}

void SectionEditor::saveCoordinates()
{
  QString filter(tr("Coordinate files (*.txt *.dat);;All files (*.*)"));
  QString fn = QFileDialog::getSaveFileName(this, tr("Select file to save"
                                                     " airfoil coordinates"),
                                            lastdir, filter);

  if (fn.isEmpty())
    return;

  ofstream os( asPath(fn).c_str() );
  const PointList<2> & crd( wsp->riPoints() );
  const int np = crd.size();
  for (int i=0; i<np; ++i)
    os << crd[i][0] << " " << crd[i][1] << std::endl;
}

void SectionEditor::naca6error(int code)
{
  QString msg(tr("Generation of NACA 6-series airfoil failed.\n"));
  switch (code) {
  case NACA6_INVALID_FAMILY:
    msg += tr("No such profile family.");
    break;
  case NACA6_INVALID_CAMBER:
    msg += tr("Invalid camber line.");
    break;
  case NACA6_INVALID_TOC:
    msg += tr("Invalid thickness ratio.");
    break;
  case NACA6_TOOMANYLINES:
    msg += tr("Too many mean lines.");
    break;
  case NACA6_ZERO_POINTER:
    msg += tr("Internal error: Zero pointer passed to naca6().");
    break;
  case NACA6_A_OUTOFRANGE:
    msg += tr("Loading factor 'a' out of range.");
    break;
  case NACA6_NOTCONVERGED:
    msg += tr("Iteration failed to converge.");
    msg += tr("Specified section may be too thin (<1%).");
    break;
  case NACA6_LIBFAILED:
    msg += tr("naca6() generated not enough points. ");
    msg += tr("Specified section may be too thin (<1%).");
    break;
  }
  QMessageBox::warning(this, "Profile generation failure.", msg);
}


