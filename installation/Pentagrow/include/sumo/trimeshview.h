
/* ------------------------------------------------------------------------
 * project:    ftkview
 * file:       trimeshview.h
 * begin:      Dec 2008
 * copyright:  (c) 2008 by <dlr@kth.se>
 * ------------------------------------------------------------------------
 * OpenGL viewer for steady 3D plots and animations
 * ------------------------------------------------------------------------
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * ------------------------------------------------------------------------ */

#ifndef SUMO_TRIMESHVIEW_H
#define SUMO_TRIMESHVIEW_H

#include <vector>
#include <QMouseEvent>
#include <QGLViewer/qglviewer.h>

#ifndef Q_MOC_RUN
#include <genua/plane.h>
#include <genua/trimesh.h>
#include <genua/boxsearchtree.h>
#endif

class TetMesh;
class SpaceMouseMotionData;

class TriangleGroup
{
  public:

    /// initialize triangle group
    TriangleGroup() : msh(0), tag(-1) {
      rgba[0] = 0.6; rgba[1] = 0.6; rgba[2] = 0.6; rgba[3] = 1.0;
    }

    /// draw the complete mesh
    uint assign(const TriMesh *m);
    
    /// extract triangles with tag t
    uint extract(const TriMesh *m, int t);

    /// draw these triangles
    void glDraw() const;
    
    /// compute the next color
    void nextColor(double col[]) const;
    
  private:

    /// parent mesh
    const TriMesh *msh;

    /// triangles in this group
    Indices idx;

    /// color to use for drawing
    double rgba[4];
    
    /// tag of this group
    int tag;

    /// used for color generation
    static int hue;
};

/** Display widget.

  This is a specialized QGLViewer which draws a triangle mesh only, and does 
  so much more efficiently than the more flexible widget used in scope. 
  
 */
class TriMeshView : public QGLViewer
{
  Q_OBJECT
  
  public:

    enum MvCamDirection {MvPosX, MvNegX, MvPosY, MvNegY,
                         MvPosZ, MvNegZ, MvTopLeftFwd};

    /// empty initialization
    TriMeshView(QGLContext *ctx, QWidget *parent);

    /// clear OpenGL state
    virtual ~TriMeshView();

    /// access settings
    bool drawEdgeFlag() const {return bDrawEdges;}
    
    /// access settings
    bool drawPolygonFlag() const {return bDrawPolygons;}
    
    /// access settings
    bool drawNormalFlag() const {return bDrawNormals;}
    
    /// access settings
    bool drawCutFlag() const {return bDrawCut;}
    
    /// cutting plane normal
    const Vct3 & cutPlaneNormal() const {return pcut.vector();}
    
    /// distance of cutting plane from origin
    Real cutPlaneDistance() const {return pcut.offset();}
    
    /// orthographic view?
    bool orthoCamera() const;
    
    /// load mesh object
    void display(const TriMesh *pm);
    
    /// set volume mesh cut to display
    void displayCut(const TetMesh *tvm);
    
    /// clear view 
    void clear();
    
  public slots:
    
    /// draw element edges?
    void toggleDrawEdges(bool flag) {bDrawEdges = flag;}

    /// draw elements?
    void toggleDrawPolygons(bool flag) {bDrawPolygons = flag;}

    /// draw surface normals?
    void toggleDrawNormals(bool flag) {bDrawNormals = flag;}
    
    /// draw volume mesh cut
    void toggleDrawCut(bool flag) {bDrawCut = flag;}
    
    /// toggle orthographic camera mode
    void toggleOrthoCamera(bool flag);
    
    /// set plane for calculation of volume mesh cut
    void cuttingPlane(const Plane & p) {pcut = p;}
    
    /// dialog for surface feature plotting
    void dlgDrawOptions();
    
    /// save pixmap snapshot of current view
    void saveSnapshot(); 
    
    /// change view direction 
    void changeCamDirection(MvCamDirection cd);
    
    /// change mesh cut 
    void updateMeshCut();
    
    /// build display lists
    void buildDisplayList();

    /// compute scene properties
    void updateSceneDimensions();
    
    /// fit display to scene
    void fitScreen();

    /// interface for motion controller
    void multiAxisControl(const SpaceMouseMotionData &mdata);

    /// handle space mouse buttons
    void multiAxisButtonPressed(uint buttons);

  signals:

    /// emitted for new status bar message
    void postStatusMessage(const QString & s);

  private:

    /// initialize display
    void init();
    
    /// plot the current scene
    void draw();

    /// overload left click to display point position and value
    void mouseReleaseEvent(QMouseEvent* e);
    
    /// catch keys x,y,z to change view direction
    void keyPressEvent(QKeyEvent *e);

    /// draw triangles
    void drawElements();

    /// draw tets cut by plane
    void drawTets();
    
    /// draw edges
    void drawEdges();

    /// draw normal vectors
    void drawNormals();
    
    /// identify index of node under screen pixel
    uint nodeUnderPixel(const QPoint & spt, bool & found) const;
    
  private:

    /// surface mesh to draw
    const TriMesh *msh;

    /// cut through volume mesh may be drawn
    TriMesh mcut; 
    
    /// volume mesh associated with this cut
    const TetMesh *pvm;
    
    /// vertex search tree
    BSearchTree btree;

    /// components to draw
    std::vector<TriangleGroup> tgroup;
    
    /// plane to use for volume mesh cut
    Plane pcut;
    
    /// one single OpenGL display list used (for now)
    uint iDisplayList;

    /// settings for surface drawing
    bool bDrawEdges, bDrawPolygons, bDrawNormals, bDrawCut;

    /// whether OpenGL context has been initialized
    bool bGlInitialized;

    /// length of normals to draw
    Real lnrm;
    
    /// scene bounding box
    qglviewer::Vec vLo, vHi;

    /// colors for polygons (if not contoured), edges and normals
    QColor cPolygons, cEdges, cNormals, cTets;

    /// type of projection used
    qglviewer::Camera::Type projection;
};

#endif

