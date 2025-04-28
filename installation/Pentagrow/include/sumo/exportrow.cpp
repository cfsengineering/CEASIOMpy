
/* ------------------------------------------------------------------------
 * file:       exportrow.cpp
 * copyright:  (c) 2007 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Configurable export interface for unigraphics
 * ------------------------------------------------------------------------ */
 
 
#include <QFile>
#include <QFileInfo>
#include <QFileDialog>
#include <genua/ioglue.h>
#include <genua/point.h>
#include "component.h"
#include "assembly.h"
#include "exportrow.h"
#include "util.h"

using std::string;
 
ExportRow::ExportRow(const Assembly & m, QWidget *parent) : 
    QDialog(parent), msf(m)
{
  setupUi(this);
  retranslateUi(this);
  
  // fill combo box 
  const uint nsf(msf.nbodies() + msf.nwings());
  assert(nsf > 1);
  for (uint i=0; i<nsf; ++i) {
    ComponentPtr cmp( msf.sumoComponent(i) );
    cbSurface->insertItem(i, QString::fromStdString(cmp->name()) );
  }
  
  // connect slot 
  connect( cbSurface, SIGNAL(currentIndexChanged(int)), 
           this, SLOT(changeSurface(int)) );
  setSelected(0);  
}

void ExportRow::setSelected(int index)
{
  cbSurface->setCurrentIndex(index);
  changeSurface(index);
}

void ExportRow::changeSurface(int index)
{
  const Component & m(*msf.sumoComponent(index));
  Real lmax = 0.125*m.refLength();
  sbLmax->setValue(lmax);
}

void ExportRow::store()
{
  int index = cbSurface->currentIndex();
  const Component & m(*msf.sumoComponent(index));
  bool iponly = cbIpOnly->isChecked();
  Real scl = sbScaling->value();
  if (scl == 0)
    scl = 1.0;
  
  string rsep;
  int rsi = cbSeparator->currentIndex();
  if (rsi == 0)
    rsep = "\nROW\n";
  else if (rsi == 1)
    rsep = "\n";
  else 
    rsep = "";
  
  int numax = sbNpps->text().toInt();
  int n2s = sbNbs->text().toInt();
  Real lmax = sbLmax->value();
  Real phimax = rad( sbPhimax->value() );
  
  QString caption = tr("Save point grid to file");
  QString filter = tr("Text files (*.txt *.dat);; All files (*)");
  QString fn = QFileDialog::getSaveFileName(this, caption, lastdir, filter);
  
  if ( !fn.isEmpty() ) {
    
    if (iponly) {
    
      PointListArray pts;
      m.ipolPoints( pts );
      const uint nc(pts.size());
      ofstream os( asPath(fn).c_str() );
      os.precision(15);
      os << std::scientific;
      for (uint j=0; j<nc; ++j) {
        os << rsep;
        const uint nr(pts[j].size());
        for (uint i=0; i<nr; ++i) {
          os << scl*pts[j][i] << endl;
        }
      }
      
    } else {
      
      // fetch points to write 
      PointGrid<3> pgrid;
      m.exportGrid(numax, n2s, lmax, phimax, pgrid);
      
      // write scaled grid to file 
      const uint nr(pgrid.nrows());
      const uint nc(pgrid.ncols());
      ofstream os( asPath(fn).c_str() );
      os.precision(15);
      os << std::scientific;
      for (uint j=0; j<nc; ++j) {
        os << rsep;
        for (uint i=0; i<nr; ++i) {
          os << scl*pgrid(i,j) << endl;
        }
      }
    }
    
    // store directory
    QFileInfo qfi(fn);
    lastdir = qfi.absolutePath();
  }
}

