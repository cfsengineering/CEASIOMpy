
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
 
#ifndef CPLOADDIALOG_H
#define CPLOADDIALOG_H

#include "ui_ploaddialog.h"
#ifndef Q_MOC_RUN
#include "frfspec.h"
#include "tdlspec.h"
#include <genua/mxmesh.h>
#include <genua/transformation.h>
#include <surf/fsimesh.h>
#endif

/** Configure interpolation of pressures to nodal forces.

  This dialog is used to obtain the settings needed to interpolate a
  surface pressure field to a shell finite element model.

  */
class PLoadDialog : public QDialog, private Ui::CpLoadDialog
{
  Q_OBJECT

public:

  /// construct dialog
  explicit PLoadDialog(QWidget *parent = 0);

  /// assign aerodynamic mesh for steady case
  void assign(MxMeshPtr & am, const Indices & fields,
              const Vector & coef, bool multiCase=false);

  /// assign aerodynamic mesh for transient case
  void assign(MxMeshPtr &am, const Indices &fields,
              const Vector &t, const VectorArray &xt);

  /// assign aerodynamic mesh for single-input harmonic forcing
  void harmonic(MxMeshPtr & am, const Indices & fields, const Vector & freq);

  /// assign mode acceleration problem spec
  void assign(const FRFSpec & s);

  /// assign mode acceleration problem spec
  void assign(const TdlSpec & s);

  /// access current structural mesh (maybe null)
  const MxMeshPtr & structuralMesh() const {return smesh;}

  /// access current aerodynamic mesh (maybe null)
  const MxMeshPtr & fluidMesh() const {return amesh;}

  /// change default directory
  void defaultDirectory(const QString & d) {lastdir = d;}

  /// set nastran mesh file name, do nothing else
  void meshFileName(const QString & s);

  /// configure mapping settings from XML file
  void configure(const XmlElement &xe);

  /// configure mapping settings from plain text file (legacy)
  void configure(const ConfigParser &cfg);

  /// extract current settings
  ConfigParser currentSettings() const;

signals:

  /// request that top-level view object switches mesh display
  void displayMesh(MxMeshPtr pmx);

  /// indicates stages of long-running processes
  void statusMessage(const QString & msg);

public slots:

  /// invalidate load mapping object
  void flagDirty();

private slots:

  /// ask for nastran mesh file
  void browseNastranMesh();

  /// ask for output file
  void browseOutputFile();

  /// load mapping settings from text file
  void loadSettings();

  /// store mapping settings to text file
  void storeSettings();

  /// dispatch to suitable mapping routine
  void mapLoads();

  /// switch mesh display
  void displayStructure(bool flag);

  /// switch to agglomeration mode
  void toggleAgglomeration(bool flag);

  /// open (modal) rotation dialog
  void rotationDialog();

protected:

  /// load NASTRAN mesh from file, using filename to determine format
  bool loadNastran();

  /// initialize structural mesh
  void initStructure();

  /// whether a static or transient case is desired
  bool isTransient() const {return (not timeSteps.empty());}

  /// whether a frequency-domain case is analysed
  bool isHarmonic() const {return (not freqList.empty());}

  /// rebuild load mapping object
  void buildInterpolator();

  /// write a TABLE1D card to transient load definition file
  void writeTable(int tid, int jcol, std::ostream &os) const;

  /// write a TABLE1D card for hat function with 1.0 at frequency jcol
  void writeHatFunction(int tid, int jcol, std::ostream &os) const;

  /// perform static load mapping according to settings
  void mapStaticLoads();

  /// generate a series of loads
  void mapMultiStaticLoads();

  /// map time-dependent loads for direct transient analysis
  void mapTransientLoads();

  /// map frequency-domain pressure coefficients
  void mapHarmonicLoads();

  /// generate subcase loads for mode acceleration FRF
  void mapFRFLoads();

  /// create structural loads for time-domain inertial relief analysis
  void mapTdlLoads();

  /// runtime UI changes
  void changeEvent(QEvent *e);

private:

  /// aerodynamic and structural mesh
  MxMeshPtr amesh, smesh;

  /// load mapping
  FsiMeshPtr pfsi;

  /// PIDs to include and exclude from mapping; pressure field indices
  Indices inclPID, exclPID, cpFields;

  /// specification for mode acceleration FRFs
  FRFSpec fspec;

  /// specification for time-domain inertial relief analysis
  TdlSpec tspec;

  /// pressure field coefficients
  Vector pfCoef;

  /// time values for transient loading
  Vector timeSteps;

  /// frequency values for harmonic loading
  Vector freqList;

  /// pressure field coefficients, transient case
  VectorArray coefHist;

  /// transformation to apply to forces and moments
  Trafo3d fmTrafo;

  /// last directory visited
  QString lastdir;

  /// whether cp fields represent multiple load cases
  bool staticMultiCase;
};

#endif // CPLOADDIALOG_H
