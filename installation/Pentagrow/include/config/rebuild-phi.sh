#! /bin/bash
#
# rebuild everything needed for phi using icpc

devroot=$HOME/Develop
gcclist="boost predicates genua surf lsfem ludwig phi"

mode="CONFIG+=release CONFIG-=debug CONFIG*=hostopt"
if (($# > 0)); then
    if [ "$1" = "debug" ]; then
        mode="CONFIG+=debug"
    elif [ "$1" = "profile" ]; then
        mode="CONFIG+=profile CONFIG-=debug CONFIG*=hostopt"
    fi
fi

cfg="$mode CONFIG+=no-spqr CONFIG+=no-metis CONFIG+=no-spooles CONFIG*=mklpardiso CONFIG*=openmp CONFIG*=tbb"

if [[ $(uname) == "Darwin" ]]; then
  echo "Mac OS X"
  SPEC="macx-icc"
  cfg="$cfg CONFIG*=builtin_expat"
  if [[ -d "$HOME/Qt/5.7" ]]; then
  	QTROOT=$HOME/Qt/5.7/clang_64
  elif [[ -d "$HOME/Qt/5.6" ]]; then
  	QTROOT=$HOME/Qt/5.6/clang_64
  elif [[ -d "$HOME/Qt/5.5" ]]; then
  	QTROOT=$HOME/Qt/5.5/clang_64
  elif [[ -d "$HOME/Qt/5.3" ]]; then
  	QTROOT=$HOME/Qt/5.3/clang_64
  elif [[ -d "$HOME/Qt/5.2.1/5.2.1/clang_64" ]]; then
	QTROOT=$HOME/Qt/5.2.1/5.2.1/clang_64/
  else
    QTROOT=/Users/david/Qt/5.3/clang_64
  fi
  QMAKE=$QTROOT/bin/qmake
  nproc=$(sysctl -n hw.ncpu)
else
  echo "Linux"
  if [[ $(which icpc) ]]; then
    SPEC=linux-icc-64
    echo "Configuring for Intel C++ compiler"
  else
    SPEC=linux-g++-64
  fi
  if [[ -d "/opt/Qt/5.5" ]]; then
    QTROOT=/opt/Qt/5.5
    QMAKE=$QTROOT/bin/qmake
  elif [[ -d "/opt/Qt/4.8" ]]; then
    QTROOT=/opt/Qt/4.8
    QMAKE=$QTROOT/bin/qmake
  elif [[ -x "/usr/bin/qmake-qt5" ]]; then
    QMAKE=qmake-qt5
  else
    QMAKE=qmake
  fi

  nproc=$(grep -c ^processor /proc/cpuinfo)
  sumotools=$HOME/bin
  scopetools=$HOME/bin
  scopedocs=$HOME/userdoc/dwfscope
fi
echo "Using $nproc make jobs"

source /opt/intel/bin/compilervars.sh intel64

echo $QMAKE $cfg

for i in $gcclist; do
  cd $devroot/$i
  make clean
  rm -rf .qmake.*
  find . -name "Makefile" | xargs rm -f
  projectfile=$(basename $i)".pro"
  $QMAKE -spec $SPEC $cfg $projectfile
  make -j$nproc || exit 42
done

