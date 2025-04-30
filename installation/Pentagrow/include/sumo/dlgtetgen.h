
/* ------------------------------------------------------------------------
 * file:       dlgtetgen.h
 * copyright:  (c) 2008 by <david.eller@gmx.net>
 * ------------------------------------------------------------------------
 * Interface to tetgen volume mesh generator
 * ------------------------------------------------------------------------ */

#ifndef SUMO_DLGTETGEN_H
#define SUMO_DLGTETGEN_H

#include <QProcess>
#include <QTime>
#include "ui_dlgtetgen.h"
#ifndef Q_MOC_RUN
#include "assembly.h"
#include <genua/configparser.h>
#endif

/** Interface for volume mesh generation functions.
 *
 *  This dialog allows to set options to define a spherical farfield
 *  boundary, adjust settings to pass to tetgen, and various options
 *  for the prismatic mesh generator.
 *
 *
 */
class DlgTetgen : public QDialog, private Ui::DlgTetgen
{
  Q_OBJECT
  
public:

  /// initialize with assembly
  DlgTetgen(QWidget *parent);

  /// assign to assembly
  void assign(AssemblyPtr pasy);

signals:

  /// emit when a volume mesh has been created
  void volumeMeshAvailable(bool);

private slots:

  /// activated by 'run' button
  void startGeneration();

  /// finalize mesh generation process after external tool call completed
  void finishGeneration(int exitCode, QProcess::ExitStatus exitStatus);

  /// interrupt mesh generation process
  void abortGeneration();

  /// change number of farfield boundary triangles
  void updateFarTriCount(int nref);

  /// update display of mesh statistics
  void updateMeshStats();

  /// change maximum tet volume when farfield changed
  void updateTetVolume();

  /// update tetgen output window
  void updateTetgenOutput();

  /// try to find tetgen executable
  bool locateTetgen();

  /// write output to log window
  void printLog(const QString &s);

private:

  /// extract configuration from UI
  void fetchConfig();

  /// start child process
  void startTetGeneration();

  /// finish tetgen process normally
  void finishTetGeneration(int exitCode, QProcess::ExitStatus exitStatus);

  /// start envelope generation, pass envelope and farfield to tetgen
  void startHybridGeneration();

  /// re-read tet mesh, fill prismatic region
  void finishHybridGeneration(int exitCode, QProcess::ExitStatus exitStatus);

  /// generate temporary file name for tetgen call
  const QString & tempFileName();

  /// start tetgen process on previously stored smesh file
  void runFirstTetgenPass();

  /// run second tetgen pass to improve tet growth rate
  void runSecondTetgenPass();

  /// generate edge metric file for second tetgen pass
  void writeMetricFile();

private:

  /// flag indicating whether hybrid or tet mesh generation is running
  enum RunStat {Inactive, TetGen, Hybrid};

  /// reference to assembly
  AssemblyPtr m_asy;

  /// pentahedral mesh generator
  ReportingPentaGrowPtr m_pgrow;

  /// current mesh generator configuration
  ConfigParser m_cfg;

  /// path to tetgen and temp dir
  QString m_tetgenpath, m_tmpdirpath;

  /// base name of temporary files
  QString m_tmpfilebase;

  /// tetgen child process
  QProcess m_tgproc;

  /// keep track of mesh generation time
  QTime m_mgclk;

  /// indicates which process is active, if any
  RunStat m_rstat;

  /// tetgen pass indicator
  uint m_tetgenPass;
};

#endif
