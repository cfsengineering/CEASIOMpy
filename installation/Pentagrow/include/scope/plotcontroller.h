
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
 
#ifndef SCOPE_PLOTCONTROLLER_H
#define SCOPE_PLOTCONTROLLER_H

#include "forward.h"
#include <QObject>
#include <QString>

/** Keeps track of plot state.
 *
 * PlotController provides a signals-and-slots interface for the UI elements
 * which control the display of a single MxMesh.
 *
 * \sa MeshPlotter, SectionPlotter, PathPlotter
 */
class PlotController : public QObject
{
  Q_OBJECT

public:

  /// flag indicating how an animation should be run
  enum AniMode { NoAnimation = 0,
                 LoopAnimation = 1,
                 RampedDeformation = 2,
                 TrajectoryDeformation = 4,
                 TrajectoryFlightPath = 8};

  /// empty controller
  PlotController() : m_vblue(0.0f), m_vred(0.0f), m_colorspread(0.5f),
    m_modescale(1.0), m_rbscale(1.0),
    m_ficontour(NotFound), m_fideform(NotFound), m_fineedles(NotFound),
    m_tianim(NotFound), m_condensation(0),
    m_changeFlags(NoChange), m_colorMode(PlainColors), m_autoUpdate(false) {}

  /// load from file
  MxMeshPtr load(const QString &fn);

  /// load data fields from multiple .bout files
  MxMeshPtr loadFields(const QStringList &fns);

  /// assign a different mesh to plotter
  void assign(MxMeshPtr pmx);

  /// initial state
  void init();

  /// access display manager
  MeshPlotterPtr plotter() const {return m_plotter;}

  /// access mesh to plot
  MxMeshPtr pmesh() const;

  /// query whether the current mesh has any elements
  bool hasElements() const;

  /// query whether mesh has any volume elements
  bool hasVolume() const;

  /// query whether the current mesh has any data fields
  bool hasFields() const;

  /// test whether vector fields are present
  bool hasVectorFields() const;

  /// query whether there are displacement fields
  bool hasDisplacements() const;

  /// query whether there are any modal time-trajectories
  bool hasTrajectories() const;

  /// index of currently contoured field
  uint contourField() const {return m_ficontour;}

  /// access maximum value of current contour field
  float maxFieldValue() const {return m_vmax;}

  /// access mean value of current contour field
  float meanFieldValue() const {return m_vmean;}

  /// access maximum value of current contour field
  float minFieldValue() const {return m_vmin;}

  /// issue OpenGL drawing commands
  void draw() const;

signals:

  /// issued when new draw operation required
  void needRedraw();

  /// issued when bounding box has changed
  void needBoxUpdate();

  /// indicates that mesh structure (e.g. number of sections) changed
  void structureChanged();

  /// emitted when section has been shown/hidden
  void sectionShown(int isec, bool flag);

  /// emitted when boco has been shown/hidden
  void bocoShown(int isec, bool flag);

  /// blue color limit changed
  void blueLimitChanged(double vblue);

  /// red color limit changed
  void redLimitChanged(double vred);

  /// indicates relative current progress of animation
  void animationAt(float rpos);

  /// signalled when a non-looping animation has finished
  void animationDone();

  /// post message
  void postStatusMessage(const QString &msg);

public slots:

  /// show streamline dialog
  void openStreamlineDialog();

  /// show hedgehog plot dialog
  void openHedgehogDialog();

  /// close all currently opened configuration dialogs
  void closeAllDialogs();

  /// reload mesh configuration (after section/field changes etc)
  void reload();

  /// if true, update display immediately for each change
  void autoUpdate(bool flag);

  /// show/hide an entire section
  void showSection(int isection, bool flag);

  /// toggle the visibility of a boco
  void showBoco(int iboco, bool flag);

  /// set all element colors from sections
  void colorBySection(bool flag=true);

  /// set all element colors from bocos
  void colorByBoco(bool flag=true);

  /// open color editor to change color for a single section
  void changeSectionColor(int isection);

  /// open color editor to change color for a single boco
  void changeBocoColor(int iboco);

  /// upload colors for one or all (default) sections
  void uploadSectionColor(int isection=-1);

  /// erase an entire section
  void eraseSection(int isec);

  /// add a boco which maps section isec
  uint addMappedBoco(int isec);

  /// erase an element group
  void eraseBoco(int iboco);

  /// determine contour color limits from spread factor
  void contourSpread(float colorSpread);

  /// change color limits explicitely
  void contourLimits(float blueValue, float redValue);

  /// change condensation mode for n-dimensional fields
  void condensation(int vfm);

  /// use field ifield to compute contour colors
  void contourField(int ifield, bool updateClrLimits = true);

  /// apply deformations from field ifield to mesh
  void deformField(int ifield);

  /// set index of trajectory to show/animate
  void trajectory(int itj);

  /// scaling factor for elastic deformations
  void deformScale(float s);

  /// scaling factor for rigid-body motion
  void rbScale(float s);

  /// set animation mode
  void animationMode(int mode) {m_animode = mode;}

  /// animate currently active mode
  void animate(float rpos);

  /// select a vector field for needle-type display
  void needleField(int ifield, int mode, float scale);

  /// update mesh display from current settings
  void updateDisplay();

private slots:

  /// update streamline settings
  void changeStreamlineDisplay(bool enabled);

  /// change streamline color
  void changeStreamlineColor();

private:

  /// test whether flag changed
  bool changed(int flag) const {
    return (m_changeFlags & flag);
  }

  /// update min/max values for contour plotting
  void updateBounds();

  /// update blue/red color limits
  void updateColorLimits();

  /// update geometry for animated deformation
  void animateDispField(float rpos);

  /// update geometry for trajectory animation
  void animateTrajectory(float rpos);

private:

  enum ChangeFlag { NoChange = 0, ContourIndex = 1, DeformIndex = 2,
                    ColorLimits = 4, SpreadFactor = 8, CondensationMode = 16,
                    ElasticScale = 32, PathScale = 64, NeedleIndex = 128,
                    TrajectoryIndex = 256};

  enum ColorMode { PlainColors, BySections, ByBocos, FieldContour };

  /// mesh display manager
  MeshPlotterPtr m_plotter;

  /// dialog for streamline configuration
  SurfaceStreamlineDialog *m_sldialog = nullptr;

  /// dialog for hedgehog plot configuration
  HedgehogDialog *m_hhdialog = nullptr;

  /// mininum and maximum values of current field
  float m_vmin, m_vmax, m_vmean;

  /// current color limits
  float m_vblue, m_vred;

  /// spread factor
  float m_colorspread;

  /// elastic deformation scaling factor
  float m_modescale;

  /// rigid-body motion deformation factor
  float m_rbscale;

  /// field used for color contouring
  uint m_ficontour;

  /// field used for deformation display
  uint m_fideform;

  /// field used for vector (needle) display
  uint m_fineedles;

  /// trajectory to display/animate
  uint m_tianim;

  /// scale factor for needle display
  float m_needleScale;

  /// mode to use for needle vector display
  int m_needleMode;

  /// condensation mode for n-dimensional fields
  int m_condensation;

  /// animation mode to use
  int m_animode;

  /// keep track of which settings changed
  int m_changeFlags;

  /// determines how displayed colors are determined
  int m_colorMode;

  /// true if OpenGL representation updated immediately upon change
  bool m_autoUpdate;
};

#endif // PLOTCONTROLLER_H
