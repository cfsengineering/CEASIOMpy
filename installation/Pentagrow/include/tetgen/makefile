###############################################################################
#                                                                             #
# makefile for TetGen                                                         #
#                                                                             #
# Type "make" to compile TetGen into an executable program (tetgen).          #
# Type "make tetlib" to compile TetGen into a library (libtet.a).             #
# Type "make distclean" to delete all object (*.o) files.                     #
#                                                                             #
###############################################################################

# CXX should be set to the name of your favorite C++ compiler.
# ===========================================================

ifndef CXX
CXX = g++
endif

#CXX = icl
#CXX = icpc
#CXX = clang++

# CXXFLAGS is the level of optimiztion, default is -O. One should try
# -O2, -O3 ... to find the best optimization level.
# ===================================================================

CXXFLAGS = -O3 -march=core2 -msse3 -mtune=corei7 -ffinite-math-only 
#CXXFLAGS = -O3 -xHost -ip -fp-model precise -fp-model source

# PREDCXXFLAGS is for compiling J. Shewchuk's predicates. 

PREDCXXFLAGS = -Os -march=core2 -msse3 -mfpmath=sse
#PREDCXXFLAGS = -Os -xHost -fp-model precise -fp-model source

LIBS = 
#LIBS = -L/opt/intel/lib/intel64/ -listrconv

# SWITCHES is a list of switches to compile TetGen.
# =================================================
#
# By default, TetGen uses double precision floating point numbers.  If you
#   prefer single precision, use the -DSINGLE switch. 
#
# The source code of TetGen includes a lot of assertions, which are mainly
#   used for catching bugs at that places.  These assertions somewhat slow
#   down the speed of TetGen.  They can be skipped by define the -DNDEBUG
#   switch.

SWITCHES = -DNDEBUG

# RM should be set to the name of your favorite rm (file deletion program).

RM = /bin/rm -f

# The action starts here.

tetgen:	tetgen.cxx predicates.o
	$(CXX) $(CXXFLAGS) $(SWITCHES) -o tetgen tetgen.cxx predicates.o $(LIBS)

tetlib: tetgen.cxx predicates.o
	$(CXX) $(CXXFLAGS) $(SWITCHES) -DTETLIBRARY -c tetgen.cxx
	ar r libtet.a tetgen.o predicates.o

tetgen.o: tetgen.cxx 
	$(CXX) $(CXXFLAGS) $(SWITCHES) -c tetgen.cxx 

predicates.o: predicates.cxx
	$(CXX) $(PREDCXXFLAGS) -c predicates.cxx

clean:
	$(RM) *.o *.a tetgen *~




