
# qmake project file to compile everything 
# needed for sumo and scope

TEMPLATE = subdirs
CONFIG  += ordered

SUBDIRS = ../boost \
          ../genua \
          ../surf \
          ../QGLViewer/QGLViewer \
          ../scope \
          ../sumo

