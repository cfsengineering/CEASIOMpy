wget --recursive --no-parent https://svn.larosterna.com/oss/thirdparty/tetgen/
cp -r svn.larosterna.com/oss/thirdparty/tetgen/ ../
wget --recursive --no-parent https://svn.larosterna.com/oss/thirdparty/QGLViewer/
cp -r svn.larosterna.com/oss/thirdparty/QGLViewer/ ../
echo "Download necessary packages"
ls -l ../QGLViewer
ls -l ../tetgen
echo "Update sumo source code"
mv ../scope/userdoc/scope-userdoc/rmgoogleref.py ../scope/userdoc/scope-userdoc/rmgoogleref.py.orig
cp rmgoogleref.py ../scope/userdoc/scope-userdoc/rmgoogleref.py
mv ../genua/transformation.h ../genua/transformation.h.orig
cp transformation.h ../genua/transformation.h
mv ../scope/deformationmapdlg.cpp ../scope/deformationmapdlg.cpp.orig
cp deformationmapdlg.cpp ../scope/deformationmapdlg.cpp
mv ../config/rebuild-sumo.sh  ../config/rebuild-sumo.sh.orig
cp rebuild-sumo.sh ../config/rebuild-sumo.sh
echo "Following files have been updated"
ls -l ../scope/userdoc/scope-userdoc/rmgoogleref.py*
ls -l ../config/rebuild-sumo.sh*
ls -l ../genua/transformation.h*
ls -l ../scope/deformationmapdlg.cpp*

