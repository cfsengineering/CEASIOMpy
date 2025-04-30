
# qmake project file for libgenua.a

TARGET = genua
TEMPLATE = lib

CONFIG -= qt
CONFIG += warn_on thread staticlib openmp

DEFINES += BOOST_THREAD_USE_LIB

# configure which third-party components are compiled in
CONFIG += zip cgns builtin_cgns builtin_rply builtin_yaml

win32-g++ {
  CONFIG *= openmp posix_threads
}

CONFIG(debug, debug|release):TARGET = $$join(TARGET,,,_debug)

macx-icc:CONFIG*=mklpardiso

include(../config/rootconfig.pri)

# compiled-in libjudy not yet adapted for 32bit
target-64bit {
  CONFIG += judy builtin_judy
} else {
  CONFIG -= judy
  CONFIG -= builtin_judy
}

# everything below can use definitions from rootconfig

DESTDIR = $$TARGET_LIB_DIR

# mac and linux ship with zlib and expat, use them.
#
# windows does not have a system zlib
win32 {
  CONFIG += builtin_zlib builtin_expat
} else {
  CONFIG -= builtin_zlib 
}

cgns {
  
   # DEFINES     += HAVE_CGNS
   INCLUDEPATH += ./cgns ./cgns/adf
  
    builtin_cgns {

      linux-g++ | linux-g++-64 | macx-g++ | macx-g++42 {
        QMAKE_CFLAGS -= --std-c99
        QMAKE_CFLAGS *= -fno-strict-aliasing
      }

      # libcgns version 2.53 -- note: 2.54 incompatible with VS2008
      HEADERS += cgns/cg_malloc.h \
            cgns/cgns_header.h \
            cgns/cgnsKeywords.h \
            cgns/cgnslib.h \
            cgns/cgnslib_f.h \
            cgns/cgnswin_f.h \
            cgns/fortran_macros.h \
            cgns/adf/ADF.h \
            cgns/adf/ADF_fbind.h \
            cgns/adf/ADF_internals.h
    
      SOURCES += cgns/adf_cond.c \
            cgns/cg_malloc.c \
            cgns/cgns_error.c \
            cgns/cgns_internals.c \
            cgns/cgnslib.c \
            cgns/adf/ADF_interface.c \
            cgns/adf/ADF_internals.c \
            cgns/adf/ADF_fortran_2_c.c \
            cgns/adf_ftoc.c \
            cgns/cg_ftoc.c \
    }
  
    # C++ interface
  
    HEADERS += cgnsboco.h \
        cgnsdescriptor.h \
        cgnsfile.h \
        cgnssection.h \
        cgnssol.h \
        cgnszone.h \
        cgnsfwd.h
    SOURCES += cgnsboco.cpp \
        cgnsdescriptor.cpp \
        cgnsfile.cpp \
        cgnssection.cpp \
        cgnssol.cpp \
        cgnszone.cpp
}

builtin_expat {
  
  DEFINES += _REENTRANT XML_STATIC XML_BUILDING_EXPAT
  INCLUDEPATH += ./expat
  
  HEADERS += expat/ascii.h \
           expat/asciitab.h \
           expat/expat.h \
           expat/expat_config.h \
           expat/expat_external.h \
           expat/iasciitab.h \
           expat/internal.h \
           expat/latin1tab.h \
           expat/macconfig.h \
           expat/nametab.h \
           expat/utf8tab.h \
           expat/winconfig.h \
           expat/xmlrole.h \
           expat/xmltok.h \
           expat/xmltok_impl.h \
           expat/xmltok_impl.c \
           expat/xmltok_ns.c     
  SOURCES += expat/xmlparse.c \
           expat/xmlrole.c \
           expat/xmltok.c \
           expat/xmltok_impl.c \
           expat/xmltok_ns.c
} else {  
  DEFINES += _REENTRANT XML_STATIC
}

zip {

      linux-g++ | linux-g++-64 | macx-g++ | macx-g++42 {
        QMAKE_CFLAGS -= --std-c99
        QMAKE_CFLAGS *= -fno-strict-aliasing
      }

   # C++ interface for zip.c/unzip.c
   HEADERS += zlib/zip.h \
              zlib/unzip.h \
              zlib/ioapi.h \
              zipfile.h
   SOURCES += zlib/zip.c \
              zlib/unzip.c \
              zlib/ioapi.c \
              zipfile.cpp
  
   # builtin zlib, can be replaced by 
   # system zlib on Linux/Mac
  
   builtin_zlib {
      INCLUDEPATH += ./zlib
      DEFINES     += NOCRYPT _REENTRANT
      HEADERS += zlib/crc32.h \
                zlib/deflate.h \
                zlib/inffast.h \
                zlib/inffixed.h \
                zlib/inflate.h \
                zlib/inftrees.h \
                zlib/trees.h \
                zlib/zconf.h \
                zlib/zlib.h \
                zlib/zutil.h
      SOURCES += zlib/adler32.c \
                zlib/compress.c \
                zlib/crc32.c \
                zlib/deflate.c \
                zlib/infback.c \
                zlib/inffast.c \
                zlib/inflate.c \
                zlib/inftrees.c \
                zlib/trees.c \
                zlib/uncompr.c \
                zlib/zutil.c
    }

    ippz {
      INCLUDEPATH += ../ippz/src
    }
}

builtin_judy {

    # Judy is much less useful on 32bit, at least for mesh generation,
    # so, to start with, just use it on 64bit systems
    DEFINES += HAVE_JUDY
    target-64bit {
      DEFINES += JU_64BIT
    }

    win32 {
      DEFINES += JU_WIN
    }

    linux-icc | macx-icc | win32-icc {
        QMAKE_CFLAGS *= -diag-disable 188,810
    }

    INCLUDEPATH += judy/src judy/src/JudyCommon judy/src/Judy1 judy/src/JudyL
    HEADERS += judymap.h

    SOURCES +=  judy/src/JudyCommon/JudyMalloc.c \
                judy/src/Judy1/Judy1ByCount.c \
                judy/src/Judy1/Judy1Cascade.c \
                judy/src/Judy1/Judy1Count.c \
                judy/src/Judy1/Judy1CreateBranch.c \
                judy/src/Judy1/Judy1Decascade.c \
                judy/src/Judy1/Judy1First.c \
                judy/src/Judy1/Judy1FreeArray.c \
                judy/src/Judy1/Judy1InsertBranch.c \
                judy/src/Judy1/Judy1MallocIF.c \
                judy/src/Judy1/Judy1MemActive.c \
                judy/src/Judy1/Judy1MemUsed.c \
                judy/src/Judy1/Judy1Next.c \
                judy/src/Judy1/Judy1NextEmpty.c \
                judy/src/Judy1/Judy1Prev.c \
                judy/src/Judy1/Judy1PrevEmpty.c \
                judy/src/Judy1/Judy1Set.c \
                judy/src/Judy1/Judy1SetArray.c \
                judy/src/Judy1/Judy1Test.c \
                judy/src/Judy1/Judy1Unset.c \
                judy/src/Judy1/j__udy1Test.c \
                judy/src/JudyL/JudyLByCount.c \
                judy/src/JudyL/JudyLCascade.c \
                judy/src/JudyL/JudyLCount.c \
                judy/src/JudyL/JudyLCreateBranch.c \
                judy/src/JudyL/JudyLDecascade.c \
                judy/src/JudyL/JudyLFirst.c \
                judy/src/JudyL/JudyLFreeArray.c \
                judy/src/JudyL/JudyLInsertBranch.c \
                judy/src/JudyL/JudyLMallocIF.c \
                judy/src/JudyL/JudyLMemActive.c \
                judy/src/JudyL/JudyLMemUsed.c \
                judy/src/JudyL/JudyLNext.c \
                judy/src/JudyL/JudyLNextEmpty.c \
                judy/src/JudyL/JudyLPrev.c \
                judy/src/JudyL/JudyLPrevEmpty.c \
                judy/src/JudyL/JudyLSet.c \
                judy/src/JudyL/JudyLSetArray.c \
                judy/src/JudyL/JudyLTest.c \
                judy/src/JudyL/JudyLUnset.c \
                judy/src/JudyL/j__udyLTest.c \
                judy/src/JudySL/JudySL.c \
                judy/src/JudyHS/JudyHS.c

    unix {
        SOURCES += judy/src/Judy1/Judy1TablesGcc64.c \
                   judy/src/JudyL/JudyLTablesGcc64.c
    }
}

system_judy {
    HEADERS += judymap.h
}

netcdf {
    SOURCES += mxmesh-netcdf.cpp
}

spqr {
    HEADERS += sparseqr.h \
               cholmodsolver.h \
               umfpacksolver.h
    SOURCES += sparseqr.cpp \
               cholmodsolver.cpp \
               umfpacksolver.cpp
}

mklpardiso {
    HEADERS += pardisosolver.h \
               dftitransform.h \
               trnlsp.h
    SOURCES += pardisosolver.cpp \
               dftitransform.cpp \
               trnlsp.cpp
}

# SPOOLES doesn't work currently
#
#spooles {
#    HEADERS += spoolessolver.h
#    SOURCES += spoolessolver.cpp
#}

posix_threads { 
    DEFINES += USE_PTHREADS
    HEADERS += synchron_posix.h
    SOURCES += synchron_posix.cpp \
        threadpool_posix.cpp
}
else { 
    DEFINES -= USE_PTHREADS
    HEADERS += synchron_boost.h
    SOURCES += threadpool_boost.cpp
}

mesquite {
    HEADERS += mxmsqadapter.h
    SOURCES += mxmsqadapter.cpp
}

fftw3 {
    HEADERS *= fftw3interface.h
    SOURCES *= fftw3interface.cpp
}

arpack {
  HEADERS *= arpack.h
  SOURCES *= arpack.cpp
}

builtin_rply {
  DEFINES += HAVE_RPLY
  HEADERS += rply/rply.h rply/rplyfile.h
  SOURCES += rply/rply.c
}

hdf5 {
  HEADERS += hdf5file.h
  SOURCES += hdf5file.cpp \
             mxmesh-hdf5.cpp \
             xmlelement-hdf5.cpp
}

builtin_yaml {
 HEADERS += yaml.h \
    yaml-cpp/anchor.h \
    yaml-cpp/binary.h \
    yaml-cpp/collectionstack.h \
    yaml-cpp/contrib/anchordict.h \
    yaml-cpp/contrib/graphbuilder.h \
    yaml-cpp/contrib/graphbuilderadapter.h \
    yaml-cpp/directives.h \
    yaml-cpp/dll.h \
    yaml-cpp/emitfromevents.h \
    yaml-cpp/emitter.h \
    yaml-cpp/emitterdef.h \
    yaml-cpp/emittermanip.h \
    yaml-cpp/emitterstate.h \
    yaml-cpp/emitterstyle.h \
    yaml-cpp/emitterutils.h \
    yaml-cpp/eventhandler.h \
    yaml-cpp/exceptions.h \
    yaml-cpp/exp.h \
    yaml-cpp/indentation.h \
    yaml-cpp/mark.h \
    yaml-cpp/node/convert.h \
    yaml-cpp/node/detail/bool_type.h \
    yaml-cpp/node/detail/impl.h \
    yaml-cpp/node/detail/iterator_fwd.h \
    yaml-cpp/node/detail/iterator.h \
    yaml-cpp/node/detail/memory.h \
    yaml-cpp/node/detail/node_data.h \
    yaml-cpp/node/detail/node_iterator.h \
    yaml-cpp/node/detail/node_ref.h \
    yaml-cpp/node/detail/node.h \
    yaml-cpp/node/emit.h \
    yaml-cpp/node/impl.h \
    yaml-cpp/node/iterator.h \
    yaml-cpp/node/node.h \
    yaml-cpp/node/parse.h \
    yaml-cpp/node/ptr.h \
    yaml-cpp/node/type.h \
    yaml-cpp/nodebuilder.h \
    yaml-cpp/nodeevents.h \
    yaml-cpp/null.h \
    yaml-cpp/parser.h \
    yaml-cpp/ptr_stack.h \
    yaml-cpp/ptr_vector.h \
    yaml-cpp/regex_yaml.h \
    yaml-cpp/regeximpl.h \
    yaml-cpp/scanner.h \
    yaml-cpp/scanscalar.h \
    yaml-cpp/scantag.h \
    yaml-cpp/setting.h \
    yaml-cpp/singledocparser.h \
    yaml-cpp/stlemitter.h \
    yaml-cpp/stream.h \
    yaml-cpp/stringsource.h \
    yaml-cpp/tag.h \
    yaml-cpp/token.h \
    yaml-cpp/traits.h \
    yaml-cpp/yaml.h

  SOURCES += yaml-cpp/binary.cpp \
    yaml-cpp/convert.cpp \
    yaml-cpp/directives.cpp \
    yaml-cpp/emit.cpp \
    yaml-cpp/emitfromevents.cpp \
    yaml-cpp/emitter.cpp \
    yaml-cpp/emitterstate.cpp \
    yaml-cpp/emitterutils.cpp \
    yaml-cpp/exp.cpp \
    yaml-cpp/memory.cpp \
    yaml-cpp/node_data.cpp \
    yaml-cpp/node.cpp \
    yaml-cpp/nodebuilder.cpp \
    yaml-cpp/nodeevents.cpp \
    yaml-cpp/null.cpp \
    yaml-cpp/ostream_wrapper.cpp \
    yaml-cpp/parse.cpp \
    yaml-cpp/parser.cpp \
    yaml-cpp/regex_yaml.cpp \
    yaml-cpp/scanner.cpp \
    yaml-cpp/scanscalar.cpp \
    yaml-cpp/scantag.cpp \
    yaml-cpp/scantoken.cpp \
    yaml-cpp/simplekey.cpp \
    yaml-cpp/singledocparser.cpp \
    yaml-cpp/stream.cpp \
    yaml-cpp/tag.cpp
}

HEADERS += algo.h \
    atomicop.h \
    binfilenode.h \
    bitfiddle.h \
    bounds.h \
    boxsearchtree.h \
    cgmesh.h \
    configparser.h \
    connectmap.h \
    csrmatrix.h \
    defines.h \
    dimsearchtree.h \
    dmatrix.h \
    dmatrix_ops.h \
    dvector.h \
    dvector_ops.h \
    edgecurve.h \
    edgeface.h \
    eig.h \
    element.h \
    facebubble.h \
    ffanode.h \
    float4.h \
    gaussline.h \
    gausstriag.h \
    hammertriag.h \
    hybridmesh.h \
    lapack.h \
    lapack_interface.h \
    lapack_overload.h \
    legendre.h \
    line.h \
    lls.h \
    looptask.h \
    lu.h \
    memberfun.h \
    meshfields.h \
    meshslice.h \
    mvop.h \
    mxmesh.h \
    mxmeshboco.h \
    mxmeshdeform.h \
    mxmeshfield.h \
    mxmeshsection.h \
    mxmeshtypes.h \
    pattern.h \
    piegl.h \
    plane.h \
    point.h \
    rsearchtree.h \
    scalarspline.h \
    sharedvector.h \
    smatrix.h \
    smatrix_ops.h \
    sparse.h \
    splinebasis.h \
    spvector.h \
    ssetrigo.h \
    strconv.h \
    strutils.h \
    svd.h \
    svector.h \
    svector_ops.h \
    synchron.h \
    sysinfo.h \
    threadpool.h \
    threadtask.h \
    timing.h \
    trafo.h \
    triangulation.h \
    triedge.h \
    triface.h \
    trigo.h \
    trimesh.h \
    xcept.h \
    xmlelement.h \
    dbprint.h \
    smallqr.h \
    mxmeshslice.h \
    kdop.h \
    b64arrayops.h \
    sparsitycounter.h \
    sse.h \
    avxemu.h \
    transformation.h \
    basicedge.h \
    basictriangle.h \
    enumobject.h \
    color.h \
    double4.h \
    cgstrip.h \
    atmosphere.h \
    fftbase.h \
    ndarrayview.h \
    ndarraybase.h \
    implicittree.h \
    mxelementtree.h \
    ndpointtree.h \
    ndarray.h \
    allocator.h \
    ssemalloc.h \
    float8.h \
    morton.h \
    ptinpoly.h \
    dyntritree.h \
    triset.h \
    volwavedrag.h \
    forward.h \
    typecode.h \
    theodorsen.h \
    blob.h \
    primitives.h \
    simdtype.h \
    double2.h \
    simdsupport.h \
    murmur.h \
    rbrotation.h \
    mxannotated.h \
    programversion.h \
    mxsolutiontree.h \
    quantbuffer.h \
    parallel_algo.h \
    parallel_loop.h \
    taskgroup.h \
    mxfieldbuffer.h \
    lz4/xxhash.h \
    lz4/lz4hc.h \
    lz4/lz4.h \
    lz4stream.h \
    preshinghashtable.h \
    abstractlinearsolver.h \
    mxstreamer.h \
    mxelementfunction.h \
    flagset.h \
    radialsort.h \
    logger.h \
    ioglue.h \
    iobuffer.h \
    eigensparsesolver.h \
    sparsebuilder.h \
    steptransform.h \
    avxtrigo_inc.h \
    avxtrigo.h \
    sparseblockmatrix.h \
    sparseblock.h \
    benzispai.h \
    splinefitter.h \
    packetstream.h \
    rcindexmap.h \
    omp_forward.h \
    benzitbb.h \
    convertingsolver.h \
    propmacro.h \
    rng.h \
    nzhashtable.h \
    ifmkl.h \
    viewptr.h \
    tasksystem.h \
    semaphore.h \
    lse.h \
    matrixview.h \
    floatcompressor.h \
    schur.h \
    simdbase.h \
    simdqr.h \
    craig.h \
    lsmr.h \
    stanfordsolver.h \
    lsqr.h \
    parbilu.h \
    cbvops.h \
    surfacestreamlines.h \
    syncedstream.h \
    scopedsetting.h \
    unroll.h \
    parallelfilter.h \
    parallelzipfilter.h \
    ioutil.h \
    tlscontainer.h \
    lockedqueue.h \
    forkjoingroup.h \
    pstl.h \
    spinbarrier.h \
    pointblock.h \
    sdirk.h \
    grulayer.h \
    linearlayer.h \
    unv58dataset.h \
    qvm.h \
    span.h \
    havelherout.h

SOURCES += trimesh.cpp \
    mxmesh-formats.cpp \
    triangulation.cpp \
    cgmesh.cpp \
    xmlelement.cpp \
    mxmesh.cpp \
    mxmeshsection.cpp \
    mxmeshslice.cpp \
    mxmeshboco.cpp \
    mxmeshdeform.cpp \
    mxmeshfield.cpp \
    meshslice.cpp \
    volwavedrag.cpp \
    meshfields.cpp \
    binfilenode.cpp \
    bounds.cpp \
    boxsearchtree.cpp \
    configparser.cpp \
    connectmap.cpp \
    edgecurve.cpp \
    edgeface.cpp \
    eig.cpp \
    dimsearchtree.cpp \
    element.cpp \
    facebubble.cpp \
    ffanode.cpp \
    hybridmesh.cpp \
    pattern.cpp \
    piegl.cpp \
    plane.cpp \
    point.cpp \
    rsearchtree.cpp \
    splinebasis.cpp \
    strutils.cpp \
    strtod.c \
    sysinfo.cpp \
    trafo.cpp \
    triedge.cpp \
    triface.cpp \
    xcept.cpp \
    cgstrip.cpp \
    atmosphere.cpp \
    planefit.cpp \ 
    mxelementtree.cpp \
    dyntritree.cpp \
    triset.cpp \
    implicittree.cpp \
    typecode.cpp \
    mxmesh-cgns.cpp \
    mxmeshdeform-lapack.cpp \
    sparsitycounter.cpp \
    mxannotated.cpp \
    mxsolutiontree.cpp \
    quantbuffer.cpp \
    mxfieldbuffer.cpp \
    blob.cpp \
    lz4/xxhash.c \
    lz4/lz4hc.c \
    lz4/lz4.c \
    lz4stream.cpp \
    preshinghashtable.cpp \
    abstractlinearsolver.cpp \
    mxstreamer.cpp \
    mxelementfunction.cpp \
    logger.cpp \
    iobuffer.cpp \
    steptransform.cpp \
    sparseblockmatrix.cpp \
    splinefitter.cpp \
    rcindexmap.cpp \
    fftbase.cpp \
    tasksystem.cpp \
    lse.cpp \
    color.cpp \
    dbprint.cpp \
    stanfordsolver.cpp \
    parbilu.cpp \
    surfacestreamlines.cpp \
    rng.cpp \
    syncedstream.cpp \
    rply/trimesh-rply.cpp \
    parallelfilter.cpp \
    parallelzipfilter.cpp \
    ioutil.cpp \
    sdirk.cpp \
    grulayer.cpp \
    linearlayer.cpp \
    unv58dataset.cpp


    



