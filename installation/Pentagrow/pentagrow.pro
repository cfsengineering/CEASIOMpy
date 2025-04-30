# Standalone pentagrow project file

TEMPLATE = app
TARGET = pentagrow

# Impostazioni di build
CONFIG += console thread warn_on openmp release
CONFIG -= qt app_bundle
QT -= core gui

# Directory dove mettere l'eseguibile
DESTDIR = bin

# Percorsi degli header
INCLUDEPATH += $$PWD/include
INCLUDEPATH += $$PWD/include/eigen
INCLUDEPATH += $$PWD/include/boost
INCLUDEPATH += $$PWD/include/surf

# Librerie da linkare
LIBS += -L$$PWD/lib64 -lsurf -lpredicates -lgenua -lboost_components -lz -lhdf5_hl -lhdf5 -llapack -lblas
LIBS += -fopenmp
# Fortran runtime (necessario per lapack/blas)
LIBS += `gfortran -m64 -print-file-name=libgfortran.a`

# Sorgenti e header
SOURCES += \
    test_pentagrow.cpp \
    frontend.cpp

HEADERS += \
    frontend.h
