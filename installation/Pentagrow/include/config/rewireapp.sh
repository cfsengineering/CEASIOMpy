#! /bin/bash
#
# Change Qt dynamic library names inside app bundle

if (($# != 1)); then
  echo "Usage: rewireapp.sh appbasename"
  exit
fi

itl=install_name_tool
appname=$1
sumodir=$HOME/bin/$appname.app
contents=$sumodir/Contents
appbinary=$contents/MacOS/$appname
QTV=5
#qtpath=/Library/Frameworks
#qtpath=/Users/david/Qt/4.8.5/lib
#qtpath=/Users/david/Qt/5.2.1/5.2.1/clang_64/lib

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
echo "Using Qt installation in " $QTROOT
qtpath=$QTROOT/lib

plugindir=$qtpath/../plugins/
dylibs="/usr/local/opt/tbb/lib/libtbb.dylib /usr/local/opt/libomp/lib/libomp.dylib /usr/local/opt/tbb/lib/libtbbmalloc.dylib"

rm -rf $contents/Frameworks
mkdir -p $contents/Frameworks
mkdir -p $contents/PlugIns
cp $QTROOT/bin/qt.conf $contents/Resources

libs="QtCore QtGui QtWidgets QtOpenGL QtXml QtSvg QtDBus QtNetwork QtPrintSupport"
for lib in $libs; do
	echo "Relinking " x.$lib.x 
	cp -R $qtpath/$lib.framework $contents/Frameworks
	
	# change identification inside lib files
	$itl -id @executable_path/../Frameworks/$lib.framework/Versions/$QTV/$lib $contents/Frameworks/$lib.framework/Versions/$QTV/$lib	
	
	# change the link path inside the executable
	$itl -change $qtpath/$lib.framework/Versions/$QTV/$lib @executable_path/../Frameworks/$lib.framework/Versions/$QTV/$lib $contents/MacOS/$appname
done


for lib in $dylibs; do
	if [[ -f $lib ]]; then
	    blib=$(basename $lib)
	    libpfx=$(basename $blib .dylib)
	    if otool -L $appbinary | grep -q "$libpfx"; then 
	    	
		    echo "Relinking " $blib
		    cp $lib $contents/Frameworks
		    chmod 644 $contents/Frameworks/$blib
	
		    # change identification inside lib files
		    $itl -id $contents/Frameworks/$blib $contents/Frameworks/$blib 
	
		    # change the link path inside the executable
		    $itl -change $lib @executable_path/../Frameworks/$blib $contents/MacOS/$appname
		    $itl -change $blib @executable_path/../Frameworks/$blib $contents/MacOS/$appname
		else 
		    echo $blib " not needed."
		fi
	fi
done

alldeps=$(otool -L $appbinary | cut -d " " -f 1)
for dep in $alldeps; do
	if echo $dep | grep -q "/usr/local"; then
	    blib=$(basename $dep)
        echo "Relinking: " $dep
        cp $dep $contents/Frameworks
		chmod 644 $contents/Frameworks/$blib
	
		# change identification inside lib files
		$itl -id $contents/Frameworks/$blib $contents/Frameworks/$blib 
	
	    # change the link path inside the executable
		$itl -change $dep @executable_path/../Frameworks/$blib $appbinary
		$itl -change $blib @executable_path/../Frameworks/$blib $appbinary
    else 
        echo "Ignored: " $dep
	fi
done

# change  the link path inside the lib files which depend on QtCore
coredeps="QtGui QtWidgets QtOpenGL QtXml QtSvg QtNetwork QtPrintSupport"
for lib in $coredeps; do
	echo "Relinking QtCore in " x.$lib.x 
	$itl -change $qtpath/QtCore.framework/Versions/$QTV/QtCore @executable_path/../Frameworks/QtCore.framework/Versions/$QTV/QtCore $contents/Frameworks/$lib.framework/Versions/$QTV/$lib
	$itl -change $qtpath/QtGui.framework/Versions/$QTV/QtGui @executable_path/../Frameworks/QtGui.framework/Versions/$QTV/QtGui $contents/Frameworks/$lib.framework/Versions/$QTV/$lib
	$itl -change $qtpath/QtWidgets.framework/Versions/$QTV/QtWidgets @executable_path/../Frameworks/QtWidgets.framework/Versions/$QTV/QtWidgets $contents/Frameworks/$lib.framework/Versions/$QTV/$lib
done

# deploy plugins
pluginsubdirs="accessible bearer printsupport platforms iconengines imageformats styles"
for psd in $pluginsubdirs; do
    if [ -d "$plugindir/$psd" ]; then
		cp -R $plugindir/$psd $contents/PlugIns
		for pfile in $(ls $contents/PlugIns/$psd); do
		    if [[ $pfile == *".dSYM" ]]
		    then 
		        echo "Debugging symbols: " $pfile
		    else
			    for lib in $libs; do
				    $itl -change $qtpath/$lib.framework/Versions/$QTV/$lib @executable_path/../Frameworks/$lib.framework/Versions/$QTV/$lib $contents/PlugIns/$psd/$pfile
			    done
			    $itl -id @executable_path/../PlugIns/$psd/$pfile $contents/PlugIns/$psd/$pfile	
			    #otool -L $contents/Plugins/$psd/$pfile
			fi
	done
	fi
done

rm -f $contents/PlugIns/accessible/libqtaccessiblecompatwidgets.dylib

# QtOpenGL and QtSvg depend on QtGui as well
#$itl -change QtGui.framework/Versions/$QTV/QtGui @executable_path/../Frameworks/QtGui.framework/Versions/$QTV/QtGui $contents/Frameworks/QtOpenGL.framework/Versions/$QTV/QtOpenGL
#$itl -change QtGui.framework/Versions/$QTV/QtGui @executable_path/../Frameworks/QtGui.framework/Versions/$QTV/QtGui $contents/Frameworks/QtOpenGL.framework/Versions/$QTV/QtOpenGL

find $contents/Frameworks -name "*_debug*" | xargs rm -rf
find $contents/Frameworks -name "Headers" | xargs rm -rf

strip -u -r $appbinary
otool -L $appbinary

# change identification inside lib files
# install_name_tool -id @executable_path/../Frameworks/libexpat.1.5.0.dylib $contents/Frameworks/libexpat.1.5.0.dylib
# install_name_tool -id @executable_path/../Frameworks/QtCore.framework/Versions/$QTV/QtCore $contents/Frameworks/QtCore.framework/Versions/$QTV/QtCore
# install_name_tool -id @executable_path/../Frameworks/QtGui.framework/Versions/$QTV/QtCore $contents/Frameworks/QtGui.framework/Versions/$QTV/QtGui
# install_name_tool -id @executable_path/../Frameworks/QtOpenGL.framework/Versions/$QTV/QtCore $contents/Frameworks/QtOpenGL.framework/Versions/$QTV/QtOpenGL
# install_name_tool -id @executable_path/../Frameworks/QtXml.framework/Versions/$QTV/QtCore $contents/Frameworks/QtXml.framework/Versions/$QTV/QtXml
# 
# change the link path inside the dependent libs
# install_name_tool -change QtCore.framework/Versions/$QTV/QtCore @executable_path/../Frameworks/QtCore.framework/Versions/$QTV/QtCore $contents/Frameworks/QtGui.framework/Versions/$QTV/QtGui
# install_name_tool -change QtCore.framework/Versions/$QTV/QtCore @executable_path/../Frameworks/QtCore.framework/Versions/$QTV/QtCore $contents/Frameworks/QtOpenGL.framework/Versions/$QTV/QtOpenGL
# install_name_tool -change QtCore.framework/Versions/$QTV/QtCore @executable_path/../Frameworks/QtCore.framework/Versions/$QTV/QtCore $contents/Frameworks/QtXml.framework/Versions/$QTV/QtXml
# install_name_tool -change QtGui.framework/Versions/$QTV/QtGui @executable_path/../Frameworks/QtGui.framework/Versions/$QTV/QtGui $contents/Frameworks/QtOpenGL.framework/Versions/$QTV/QtOpenGL
# 
# change the link path inside the executable
# install_name_tool -change /usr/lib/libexpat.1.dylib @executable_path/../Frameworks/libexpat.1.5.0.dylib $contents/MacOS/dwfsumo
# install_name_tool -change QtCore.framework/Versions/$QTV/QtCore @executable_path/../Frameworks/QtCore.framework/Versions/$QTV/QtCore $contents/MacOS/dwfsumo
# install_name_tool -change QtGui.framework/Versions/$QTV/QtGui @executable_path/../Frameworks/QtGui.framework/Versions/$QTV/QtGui $contents/MacOS/dwfsumo
# install_name_tool -change QtOpenGL.framework/Versions/$QTV/QtOpenGL @executable_path/../Frameworks/QtOpenGL.framework/Versions/$QTV/QtOpenGL $contents/MacOS/dwfsumo
# install_name_tool -change QtXml.framework/Versions/$QTV/QtXml @executable_path/../Frameworks/QtXml.framework/Versions/$QTV/QtXml $contents/MacOS/dwfsumo

