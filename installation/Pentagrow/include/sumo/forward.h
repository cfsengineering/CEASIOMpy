
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
 
#ifndef SUMO_FORWARD_H
#define SUMO_FORWARD_H

#ifndef Q_MOC_RUN
#include <surf/forward.h>
#include <genua/forward.h>
#endif

class WingSection;
typedef boost::shared_ptr<WingSection> WingSectionPtr;
typedef std::vector<WingSectionPtr> WingSectionArray;

class WingSkeleton;
typedef boost::shared_ptr<WingSkeleton> WingSkeletonPtr;
typedef std::vector<WingSkeletonPtr> WingSkeletonArray;

class BodyFrame;
typedef boost::shared_ptr<BodyFrame> BodyFramePtr;
typedef std::vector<BodyFramePtr> BodyFrameArray;

class BodySkeleton;
typedef boost::shared_ptr<BodySkeleton> BodySkeletonPtr;
typedef std::vector<BodySkeletonPtr> BodySkeletonArray;

class Assembly;
typedef boost::shared_ptr<Assembly> AssemblyPtr;
typedef std::vector<AssemblyPtr> AssemblyArray;

class FrameProjector;
typedef boost::shared_ptr<FrameProjector> FrameProjectorPtr;

class FitIndicator;
typedef boost::shared_ptr<FitIndicator> FitIndicatorPtr;

class CgPainter;
typedef boost::shared_ptr<CgPainter> CgPainterPtr;

class CgInstancePainter;
typedef boost::shared_ptr<CgInstancePainter> CgInstancePainterPtr;
typedef std::vector<CgInstancePainterPtr> CgInstancePainterArray;

class ReportingPentaGrow;
typedef boost::shared_ptr<ReportingPentaGrow> ReportingPentaGrowPtr;

class MGenProgressCtrl;
typedef boost::shared_ptr<MGenProgressCtrl> MGenProgressPtr;

// GUI components

class SkeletonEditor;
class FrameEditor;
class SumoShell;
class RenderView;
class TriMeshView;
class SkeletonWidget;
class AssemblyTree;
class ShTreeItem;
class DlgTetgen;
class WaveDragDlg;
class WingSectionFitDlg;
class DlgGlobalTransform;

#endif // FORWARD_H
