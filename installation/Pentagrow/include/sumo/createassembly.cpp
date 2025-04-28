
/* ------------------------------------------------------------------------
 * file:       createassembly.cpp
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Dialog to select template or load from file
 * ------------------------------------------------------------------------ */

#include <sstream>
#include <QFileDialog>
#include <QPushButton>
#include <QRadioButton>
#include <QComboBox>
#include <QLineEdit>
#include <QMessageBox>
#include "componentlibrary.h"
#include "createassembly.h"
#include "util.h"

using namespace std;

CreateAssembly::CreateAssembly(QWidget *parent) : QDialog(parent)
{
  setupUi(this);
  retranslateUi(this);
  
  // fill data 
  const int nt = SumoComponentLib.nassembly();
  for (int i=0; i<nt; ++i) {
    cbSelectTemplate->addItem( SumoComponentLib.assemblyName(i) );
  }
  cbSelectTemplate->setCurrentIndex(0);
  
  connect( pbBrowse, SIGNAL(clicked()), this, SLOT(browse()) );
}

bool CreateAssembly::useTemplate() const 
{
  return rbUseTemplate->isChecked() or filename.isEmpty();
}

AssemblyPtr CreateAssembly::create()
{
  AssemblyPtr ptr;
  int idx = cbSelectTemplate->currentIndex();
  try {
    ptr = SumoComponentLib.assembly( idx );
  } catch (Error & xcp) {
    QString msg;
    msg  = tr("<b>Problem creating library assembly.</b>\n");
    msg += tr("Error message: ")+qstr(xcp.what());
    QMessageBox::information( this, "sumo", msg);
    return AssemblyPtr();
  }
  return ptr;
}

void CreateAssembly::browse()
{
  QString caption = tr("Load assembly from file");
  QString filter = tr("Sumo models (*.smx);; All files (*)");
  filename = QFileDialog::getOpenFileName(this, caption, lastdir, filter);
  if (filename.isEmpty())
    rbUseTemplate->setChecked(true);
  else
    leFilename->setText(filename);
}






