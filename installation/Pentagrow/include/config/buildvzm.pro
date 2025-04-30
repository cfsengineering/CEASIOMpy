
# qmake project file to compile everything 
# needed for vzm

TEMPLATE = subdirs
vzm.depends = boost genua surf predicates qcustomplot QGLViewer/QGLViewer

SUBDIRS = boost \
          genua \
          surf \
          predicates \
          qcustomplot \
          QGLViewer/QGLViewer \
          vzm

