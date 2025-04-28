#include "buildfluttermodedialog.h"
#include "ui_buildfluttermodedialog.h"
#include "util.h"
#include <genua/dvector.h>
#include <genua/mxmesh.h>
#include <iostream>

using namespace std;

BuildFlutterModeDialog::BuildFlutterModeDialog(QWidget *parent) :
  QDialog(parent),
  m_ui(new Ui::BuildFlutterModeDialog)
{
  m_ui->setupUi(this);
  m_ui->m_leShapeName->setText("Flutter Mode");

  connect(m_ui->m_pbApply, SIGNAL(clicked()), this, SLOT(buildMode()));
}

BuildFlutterModeDialog::~BuildFlutterModeDialog()
{
  delete m_ui;
}

void BuildFlutterModeDialog::assign(MxMeshPtr pmx)
{
  m_pmx = pmx;
  if (m_pmx == nullptr)
    return;

  m_dsp.clear();
  const int nf = m_pmx->nfields();
  for (int i=0; i<nf; ++i) {
    MxMeshField::ValueClass vcl = pmx->field(i).valueClass();
    if (vcl == MxMeshField::ValueClass::Displacement or
        vcl == MxMeshField::ValueClass::Eigenmode)
      m_dsp.push_back(i);
  }

  m_ui->m_tablebMpf->clear();
  m_ui->m_tablebMpf->setRowCount(m_dsp.size());
  m_ui->m_tablebMpf->setColumnCount(2);

  QStringList colHeaders, rowHeaders;
  colHeaders << tr("Real") << tr("Imaginary");
  m_ui->m_tablebMpf->setHorizontalHeaderLabels(colHeaders);

  for (uint idx : m_dsp)
    rowHeaders << QString::number(idx+1);
  m_ui->m_tablebMpf->setVerticalHeaderLabels(rowHeaders);

  m_ui->m_leShapeName->setText( tr("Flutter Mode %1").arg(m_pmx->ndeform()+1) );

  tabulaRasa();
}

void BuildFlutterModeDialog::buildMode()
{
  Complex p( m_ui->m_sbRealPart->value(), m_ui->m_sbImagPart->value() );
  MxMeshDeform def(m_pmx.get());
  def.rename(str(m_ui->m_leShapeName->text()));

  if ( m_ui->m_tabWidget->currentWidget() == m_ui->m_tabText ) {

    std::string txt = str(m_ui->m_textMpf->toPlainText());
    CpxVector mpf;
    Real rep(0.0), imp(0.0);
    char *tail(0);
    const char *pos = txt.c_str();
    while ( *pos != '\0' ) {

      while (isspace(*pos))
        ++pos;
      if (*pos == '\0')
        break;

      rep = genua_strtod(pos, &tail);
      if (tail == pos)
        break;
      pos = tail;
      imp = genua_strtod(pos, &tail);
      if (tail == pos)
        break;
      pos = tail;
      mpf.push_back( Complex(rep, imp) );
    }

    Indices subDsp;
    CpxVector subMpf;
    if (mpf.size() != m_dsp.size()) {
      const int n = std::min(mpf.size(), m_dsp.size());
      subDsp.assign( m_dsp.begin(), m_dsp.begin()+n );
      subMpf.insert(subMpf.end(), mpf.begin(), mpf.begin()+n);
    } else {
      subDsp = m_dsp;
      subMpf = mpf;
    }

    // fill table from extracted values
    tabulaRasa();
    size_t nval = subMpf.size();
    assert(subMpf.size() == subDsp.size());
    for (size_t i=0; i<nval; ++i) {
      int row = std::distance(m_dsp.begin(),
                              std::lower_bound(m_dsp.begin(), m_dsp.end(),
                                               subDsp[i]));
      m_ui->m_tablebMpf->item(row,0)->setText(QString::number(subMpf[i].real()));
      m_ui->m_tablebMpf->item(row,1)->setText(QString::number(subMpf[i].imag()));
    }

    def.fromFlutterMode(subDsp, p, subMpf);
    m_pmx->appendDeform(def);

    emit flutterModeCreated();

  } else {

    const int nrow = m_ui->m_tablebMpf->rowCount();
    CpxVector mpf(nrow);
    for (int i=0; i<nrow; ++i) {
      QTableWidgetItem *realItem = m_ui->m_tablebMpf->item(i, 0);
      QTableWidgetItem *imagItem = m_ui->m_tablebMpf->item(i, 1);
      mpf[i] = Complex( realItem->text().toDouble(),
                        imagItem->text().toDouble() );
    }

    clog << "Modal participation factors: " << mpf << endl;

    def.fromFlutterMode(m_dsp, p, mpf);
    m_pmx->appendDeform(def);

    emit flutterModeCreated();
  }
}

void BuildFlutterModeDialog::tabulaRasa()
{
  const int nrow = m_ui->m_tablebMpf->rowCount();
  const int ncol = m_ui->m_tablebMpf->columnCount();
  for (int i=0; i<nrow; ++i) {
    for (int j=0; j<ncol; ++j) {
      m_ui->m_tablebMpf->setItem(i, j, new QTableWidgetItem("0.0"));
    }
  }
}
