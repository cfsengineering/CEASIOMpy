
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
 
#ifndef SCOPE_FORWARD_H
#define SCOPE_FORWARD_H

#ifndef Q_MOC_RUN
#include <surf/forward.h>
#include <genua/forward.h>
#endif

// models, OpenGL display handling

struct PlotTriangle;
typedef std::vector<PlotTriangle> PlotTriangleArray;

struct PlotEdge;
typedef std::vector<PlotEdge> PlotEdgeArray;

class SectionPlotter;
class PathPlotter;
class HedgehogPlotter;
class MeshPlotter;
typedef boost::shared_ptr<MeshPlotter> MeshPlotterPtr;
typedef std::vector<MeshPlotterPtr> MeshPlotterArray;

class TreeItem;
typedef boost::shared_ptr<TreeItem> TreeItemPtr;

class SidebarTreeItem;
typedef boost::shared_ptr<SidebarTreeItem> SidebarTreeItemPtr;

class XmlTreeItem;
typedef boost::shared_ptr<XmlTreeItem> XmlTreeItemPtr;

// Qt dependent View/Controller

class PlotController;
class SpaceMouseMotionData;
class SpaceMouseInterface;
class SpaceMouseMotionEvent;
class SpaceMouseButtonEvent;

// dialogs

class SectionCopyDialog;
class ComponentDialog;
class ContourDialog;
class DisplacementDialog;
class MeshCutDialog;
class TransformationDialog;
class DisplaceMeshSettings;
class PlaneGridDialog;
class SliceDlg;
class ElementInfoBox;
class NodeInfoBox;
class AddModeshapeDialog;
class HedgehogDialog;
class EditMeshDialog;
class LongManeuvDialog;
class DirectPMapDialog;
class InrelLoadDialog;
class DeformationMapDlg;
class MeshQualityDialog;
class SidebarTree;
class SidebarTreeModel;
class SidebarTreeItem;
class SurfaceStreamlineDialog;
class ForceDisplayDialog;
class BuildFlutterModeDialog;

#endif // FORWARD_H
