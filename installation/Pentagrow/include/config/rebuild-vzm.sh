#! /bin/bash
#
# build scope and sumo including all dependencies;
# script deletes qmake cache files so that it can be
# called even after another spec was used to generate cache

devroot=$HOME/git
gcclist="boost nlopt predicates genua surf qglviewer/QGLViewer qcustomplot vzm"

mode="CONFIG+=release CONFIG-=debug CONFIG*=avx"
if (($# > 0)); then
    if [ "$1" = "debug" ]; then
        mode="CONFIG+=debug"
        echo "Deugging mode."
    elif [ "$1" = "profile" ]; then
        mode="CONFIG+=profile CONFIG-=debug CONFIG*=avx"
        echo "Profiling mode."
    elif [ "$1" = "lima" ]; then
    	mode="CONFIG+=release CONFIG-=debug CONFIG*=avx CONFIG+=vzm-lima"
      echo "LIMA mode."
    fi
fi

cfg="$mode CONFIG+=preset-vzm"

if [[ $(uname) == "Darwin" ]]; then
  echo "Mac OS X"
  SPEC="macx-clang"
  if [[ -d "$HOME/Qt/5.12.6" ]]; then
  	QTROOT=$HOME/Qt/5.12.6/clang_64
  elif [[ -d "$HOME/Qt/5.9.6" ]]; then
  	QTROOT=$HOME/Qt/5.9.6/clang_64
  elif [[ -d "$HOME/Qt/5.6.3" ]]; then
  	QTROOT=$HOME/Qt/5.6.3/clang_64
  elif [[ -d "$HOME/Qt/5.5" ]]; then
  	QTROOT=$HOME/Qt/5.5/clang_64
  elif [[ -d "$HOME/Qt/5.3" ]]; then
  	QTROOT=$HOME/Qt/5.3/clang_64
  else
    QTROOT=/Users/david/Qt/5.3/clang_64
  fi

  QMAKE=$QTROOT/bin/qmake
  sumotools=$HOME/bin/dwfsumo.app/Contents/Tools
  scopetools=$HOME/bin/dwfscope.app/Contents/Tools
  scopedocs=$HOME/bin/dwfscope.app/Contents/Documentation
  rm -rf $HOME/bin/dwfsumo.app
  rm -rf $HOME/bin/dwfscope.app

  echo "QMAKE = " $QMAKE 

  nproc=$(sysctl -n hw.ncpu)
else
  echo "Linux"
  SPEC=linux-g++-64
  if [[ -d "/opt/Qt-5.6" ]]; then
    QTROOT=/opt/Qt-5.6
    QMAKE=$QTROOT/bin/qmake
  elif [[ -d "/opt/Qt/5.5" ]]; then
    QTROOT=/opt/Qt/5.5
    QMAKE=$QTROOT/bin/qmake
  elif [[ -d "/opt/Qt/4.8" ]]; then
    QTROOT=/opt/Qt/4.8
    QMAKE=$QTROOT/bin/qmake
  elif [[ -x "/usr/bin/qmake-qt5" ]]; then
    QMAKE=qmake-qt5
  elif [[ -x "/usr/bin/qmake-qt4" ]]; then
    QMAKE=qmake-qt4
  else
    QMAKE=qmake
  fi

  nproc=$(grep -c ^processor /proc/cpuinfo)
fi
echo "Using $nproc make jobs"

#
# Build loop
#

for i in $gcclist; do
  cd $devroot/$i
  make distclean
  rm -rf .qmake.* build-*
  projectfile=$(basename $i)".pro"
  echo "QMAKE: " $QMAKE -spec $SPEC $cfg $projectfile 
  $QMAKE -spec $SPEC $cfg $projectfile
  make -j$nproc || exit 42
done

cd $devroot/../bin
bash ./rewireapp.sh vzm

mkdir -p vzm.app/Contents/userdoc
cp -R $devroot/vzm/userdoc/site/ vzm.app/Contents/userdoc  

