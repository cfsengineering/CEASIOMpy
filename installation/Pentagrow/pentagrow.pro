# Standalone pentagrow project file

TEMPLATE = app
TARGET = pentagrow

# Impostazioni di build
CONFIG += console thread warn_on openmp release c++11
CONFIG -= qt app_bundle
QT -= core gui
#QMAKE_CXXFLAGS += -D_GLIBCXX_USE_CXX11_ABI=0

# Directory dove mettere l'eseguibile
DESTDIR = bin

# Percorsi degli header
INCLUDEPATH += $$PWD/include
INCLUDEPATH += $$PWD/include/eigen
INCLUDEPATH += $$PWD/include/boost
INCLUDEPATH += $$PWD/include/surf
INCLUDEPATH += $$PWD/include/genua

# Librerie da linkare
LIBS += -L$$PWD/lib64 -lsurf -lpredicates -lgenua -lboost_components -lz -lhdf5_hl -lhdf5 -llapack -lblas
LIBS += -fopenmp
# Fortran runtime (necessario per lapack/blas)
LIBS += `gfortran -m64 -print-file-name=libgfortran.a`

# Sorgenti e header
SOURCES += \
    test_pentagrow.cpp \
    frontend.cpp \
    include/genua/configparser.cpp \
    include/genua/logger.cpp \
    include/genua/mxmesh.cpp \
    include/genua/xmlelement.cpp \
    include/genua/cgnsfile.cpp

HEADERS += \
    frontend.h

