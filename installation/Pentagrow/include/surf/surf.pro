#
# qmake project file for libsurf.a
#
TEMPLATE = lib
TARGET = surf

CONFIG += warn_on thread staticlib openmp
CONFIG -= qt
CONFIG(debug, debug|release):TARGET = $$join(TARGET,,,_debug)

DEFINES += BOOST_THREAD_USE_LIB

# DEFINES += HAVE_TETGEN
include(../config/rootconfig.pri)

target-64bit { 
  CONFIG *= judy 
} else {
  CONFIG -= judy
}

DESTDIR = $$TARGET_LIB_DIR
INCLUDEPATH += ..

macx-icc | linux-icc {
  QMAKE_CXXFLAGS *= -wd654
}

win32-icc {
  QMAKE_CXXFLAGS *= -Qwd654
}

nlopt {
  SOURCES += pentagrow-nlopt.cpp
}

!no-jrstriangle {
  DEFINES += HAVE_JRSTRIANGLE
  DEFINES += ANSI_DECLARATORS
  HEADERS += jrstriangle/triangle.h \
             jrstriangle/jrstrianglewrapper.h \
             jrstriangle/jrsmeshgenerator.h
  SOURCES += jrstriangle/triangle.c \
             jrstriangle/jrstrianglewrapper.cpp \
             jrstriangle/jrsmeshgenerator.cpp
}

HEADERS += airfoil.h \
    airfoilcollection.h \
    airfoillibrary.h \
    assembly.h \
    asycomponent.h \
    cascademesh.h \
    curve.h \
    cylinder.h \
    dnboxadaptor.h \
    dnedge.h \
    dnmesh.h \
    dnrefine.h \
    dnrfregion.h \
    dntriangle.h \
    dnvertex.h \
    dnwingcriterion.h \
    edgefaceisec.h \
    efimprove.h \
    eggframe.h \
    ellipframe.h \
    facetree.h \
    guige.h \
    igesdirentry.h \
    igesentity.h \
    igesfile.h \
    igesline.h \
    igessection.h \
    initgrid.h \
    intersect.h \
    linearsurf.h \
    longcapsurf.h \
    meshcomponent.h \
    meshgenerator.h \
    meshpatch.h \
    meshsections.h \
    naca6.h \
    naca6generator.h \
    nstcoordsys.h \
    nstelements.h \
    nstmesh.h \
    nstreader.h \
    nstrecord.h \
    openframe.h \
    patchmerger.h \
    planarmesh.h \
    planesurface.h \
    polysplinesurf.h \
    rotsurf.h \
    roundcapsurf.h \
    sides.h \
    skinsurf.h \
    splinecapsurf.h \
    spotrefine.h \
    stitchedsurf.h \
    subsurface.h \
    surface.h \
    symframe.h \
    symsurf.h \
    tetboundarygroup.h \
    tetmesh.h \
    transurf.h \
    tritetwriter.h \
    ttinode.h \
    ttintersection.h \
    ttintersector.h \
    ttitopology.h \
    wingletblend.h \
    wingtiparc.h \
    wingtipcap.h \
    iges308.h \
    iges408.h \
    ringcapsurf.h \
    paver.h \
    endcap.h \
    srfprojector.h \
    step.h \
    stepentitycreator.h \
    steplistrep.h \
    step_ap203.h \
    stepfile.h \
    stepentity.h \
    stepline.h \
    tticonnection.h \
    iges116.h \
    iges126.h \
    iges128.h \
    iges118.h \
    iges124.h \
    iges110.h \
    iges406.h \
    instance.h \
    producttree.h \
    fsimesh.h \
    fsielement.h \
    iges142.h \
    iges144.h \
    loadipol.h \
    wakesurf.h \
    pentagrow.h \
    iges120.h \
    revosurf.h \
    wakecomponent.h \
    capcomponent.h \
    iges314.h \
    polysplinecurve.h \
    multisurfprojector.h \
    abstractcurve.h \
    iges102.h \
    compositecurve.h \
    trimmedsurf.h \
    delaunaycore.h \
    dcface.h \
    dcedge.h \
    dcgeometry.h \
    dcplanegeometry.h \
    dcspatialgeometry.h \
    uvmapping.h \
    uvmapdelaunay.h \
    dcmeshcrit.h \
    product.h \
    linecurve.h \
    rationalsplinecurve.h \
    flapspec.h \
    rationalsplinesurface.h \
    iges108.h \
    forward.h \
    airfoilfitter.h \
    rbfinterpolator.h \
    dcfaceset.h \
    topoedge.h \
    topoface.h \
    topology.h \
    topovertex.h \
    abstractuvcurve.h \
    uvpolyline.h \
    uvsplinecurve.h \
    uvcubiccurve.h \
    lazyisectree.h \
    topoisecsegment.h \
    toposegmchain.h \
    surfinterpolator.h \
    dispinterpolator.h \
    iges100.h \
    circulararc.h \
    wingpart.h \
    slavedwake.h \
    tgrefiner.h \
    dcedgetable.h \
    hexboxpart.h \
    nstelementstress.h \
    nststressfield.h \
    topopart.h \
    basicpart.h \
    materialproperty.h \
    elementproperty.h \
    smbodymesh.h \
    smribmesh.h \
    smwingmesh.h \
    instancesurf.h \
    beziersegment.h \
    dcmeshgenerator.h \
    patchmeshgenerator.h \
    iges.h \
    mappedcurve.h \
    iges402.h

SOURCES += guige.c \
    facetree.cpp \
    moeller.cpp \
    moellerf.cpp \
    naca6.c \
    airfoil.cpp \
    airfoilcollection.cpp \
    airfoillibrary.cpp \
    assembly.cpp \
    asycomponent.cpp \
    cascademesh.cpp \
    curve.cpp \
    cylinder.cpp \
    dnboxadaptor.cpp \
    dnmesh.cpp \
    dnrefine.cpp \
    dnrfregion.cpp \
    dnwingcriterion.cpp \
    edgefaceisec.cpp \
    efimprove.cpp \
    eggframe.cpp \
    ellipframe.cpp \
    igesentity.cpp \
    igesfile.cpp \
    igessection.cpp \
    initgrid.cpp \
    intersect.cpp \
    linearsurf.cpp \
    longcapsurf.cpp \
    meshcomponent.cpp \
    meshgenerator.cpp \
    meshpatch.cpp \
    meshsections.cpp \
    naca6generator.cpp \
    nstcoordsys.cpp \
    nstelements.cpp \
    nstmesh.cpp \
    nstreader.cpp \
    nstrecord.cpp \
    openframe.cpp \
    patchmerger.cpp \
    planarmesh.cpp \
    planesurface.cpp \
    polysplinesurf.cpp \
    rotsurf.cpp \
    roundcapsurf.cpp \
    skinsurf.cpp \
    splinecapsurf.cpp \
    spotrefine.cpp \
    stitchedsurf.cpp \
    subsurface.cpp \
    surface.cpp \
    symframe.cpp \
    symsurf.cpp \
    tetboundarygroup.cpp \
    tetmesh.cpp \
    transurf.cpp \
    tritetwriter.cpp \
    ttinode.cpp \
    ttintersection.cpp \
    ttintersector.cpp \
    ttitopology.cpp \
    wingletblend.cpp \
    wingtiparc.cpp \
    wingtipcap.cpp \
    iges308.cpp \
    iges408.cpp \
    ringcapsurf.cpp \
    paver.cpp \
    endcap.cpp \
    srfprojector.cpp \
    step.cpp \
    stepentitycreator.cpp \
    steplistrep.cpp \
    step_ap203.cpp \
    stepfile.cpp \
    stepentity.cpp \
    stepline.cpp \
    tticonnection.cpp \
    iges116.cpp \
    iges126.cpp \
    iges128.cpp \
    iges118.cpp \
    iges124.cpp \
    iges110.cpp \
    iges406.cpp \
    instance.cpp \
    producttree.cpp \
    fsimesh.cpp \
    fsielement.cpp \
    iges142.cpp \
    iges144.cpp \
    loadipol.cpp \
    wakesurf.cpp \
    pentagrow.cpp \
    iges120.cpp \
    revosurf.cpp \
    wakecomponent.cpp \
    capcomponent.cpp \
    iges314.cpp \
    polysplinecurve.cpp \
    multisurfprojector.cpp \
    abstractcurve.cpp \
    iges102.cpp \
    compositecurve.cpp \
    trimmedsurf.cpp \
    delaunaycore.cpp \
    dcgeometry.cpp \
    dcspatialgeometry.cpp \
    uvmapping.cpp \
    uvmapdelaunay.cpp \
    dcmeshcrit.cpp \
    product.cpp \
    linecurve.cpp \
    rationalsplinecurve.cpp \
    flapspec.cpp \
    rationalsplinesurface.cpp \
    iges108.cpp \
    airfoilfitter.cpp \
    rbfinterpolator.cpp \
    dcplanegeometry.cpp \
    topoedge.cpp \
    topoface.cpp \
    topology.cpp \
    abstractuvcurve.cpp \
    uvpolyline.cpp \
    uvcubiccurve.cpp \
    topovertex.cpp \
    lazyisectree.cpp \
    topoisecsegment.cpp \
    toposegmchain.cpp \
    surfinterpolator.cpp \
    dispinterpolator.cpp \
    iges100.cpp \
    circulararc.cpp \
    wingpart.cpp \
    slavedwake.cpp \
    tgrefiner.cpp \
    hexboxpart.cpp \
    nstelementstress.cpp \
    nststressfield.cpp \
    topopart.cpp \
    basicpart.cpp \
    materialproperty.cpp \
    elementproperty.cpp \
    smbodymesh.cpp \
    smribmesh.cpp \
    smwingmesh.cpp \
    instancesurf.cpp \
    beziersegment.cpp \
    dcmeshgenerator.cpp \
    patchmeshgenerator.cpp \
    mappedcurve.cpp \
    iges402.cpp


















