//
// project:      scope
// file:         slicedlg.h
// copyright:    (c) 2010 by david.eller@gmx.net
// license:      see the file 'license.txt'
//
// UI for mesh slice generation

#ifndef SCOPE_SLICEDLG_H
#define SCOPE_SLICEDLG_H

#include <QDialog>
#include <QStringList>
#ifndef Q_MOC_RUN
#include <genua/mxmeshslice.h>
#endif

class SegmentPlot;
class QComboBox;

namespace Ui {
class SliceDlg;
}

/** Dialog for mesh data slices */
class SliceDlg : public QDialog
{
  Q_OBJECT
public:

  /// dialog w/o attached mesh
  SliceDlg(QWidget *parent = 0);

  /// destroy
  ~SliceDlg();

  /// attach mesh before calling slice()
  void attach(MxMeshPtr pm, const Vct3f &plo, const Vct3f &phi);

  /// set directory to start from
  void lastDirectory(const QString & s) {lastdir = s;}

public slots:

  /// assign field index for plot on left axis
  void assignLeftField(int ifield);

  /// assign field index for plot on left axis
  void assignRightField(int ifield);

  /// assign field index for axis which was changed last
  void assignCurrentField(int ifield);

private slots:

  /// perform slice operation
  void slice();

  /// save as matlab function
  void savePlot();

  /// set nx plane
  void planeNx();

  /// set ny plane
  void planeNy();

  /// set nz plane
  void planeNz();

  /// set nx plane
  void planeNx(double offs);

  /// set ny plane
  void planeNy(double offs);

  /// set nz plane
  void planeNz(double offs);

  /// change data column to use for bottom axis
  void bottomAxis(int col);

  /// change data column to use for left axis
  void leftAxis(int col);

  /// change data column to use for left axis
  void rightAxis(int col);

  /// show currently selected plot data
  void showPlot();

protected:

  /// set selection box from field names
  void fillComboBox(QComboBox *box) const;

  /// determine default data columns to plot
  void defaultColumns();

  /// set all geometric entry field to zero
  void allZero();

  /// lookup column from field name
  int columnIndex(int ifield) const;

  /// language change
  void changeEvent(QEvent *e);

private:

  /// slice object
  MxMeshSlice mslice;

  /// column names of current slice (if any)
  QStringList columnNames;

  /// used to determine whether y-axis should be inverted
  std::vector<bool> invertAxis;

  /// segmented plot for left (main) and right axis
  SegmentPlot *leftPlot, *rightPlot;

  /// columns which are currently plotted
  int botCol, leftCol, rightCol;

  /// UI management: keep track of which plot was modified last
  bool leftLastChanged;

  /// bounding box for default dimensions
  Vct3f lobox, hibox;

  /// whether to limit the slice to plane range
  bool bInPlane;

  /// last directory used
  QString lastdir;

  /// UI object
  Ui::SliceDlg *ui;
};

#endif // SLICEDLG_H
