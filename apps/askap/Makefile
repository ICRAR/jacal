#
# Skeleton Makefile to compile the code in this module as a shared library. It
# assumes ASKAPSoft can be found under ASKAP_ROOT and that DALiuGE is installed
# and can be loaded by the python executable
#
CXX=g++
CC=gcc

ifndef ASKAP_ROOT
$(error ASKAP_ROOT is not set)
endif

# Are we building against a patched askapsoft? (for multithread safety)
ifeq ($(ASKAP_PATCHED), 1)
WCSLIB_VERSION := 5.17
CASACORE_VERSION := 2.4.0
else
WCSLIB_VERSION := 4.18
CASACORE_VERSION := 2.0.3
endif

# DALiuGE include dir
DLG_INCDIRS = -I`python -c "import dlg; print(dlg.get_include_dir())"`

# ASKAPSoft dependencies
ASKAP_INCDIRS = -I$(ASKAP_ROOT)/3rdParty/log4cxx/log4cxx-0.10.0/install/include \
                -I$(ASKAP_ROOT)/3rdParty/LOFAR/Common/Common-3.3/install/include \
                -I$(ASKAP_ROOT)/3rdParty/LOFAR/Blob/Blob-1.2/install/include \
                -I$(ASKAP_ROOT)/3rdParty/boost/boost-1.56.0/install/include \
                -I$(ASKAP_ROOT)/3rdParty/wcslib/wcslib-$(WCSLIB_VERSION)/install/include \
                -I$(ASKAP_ROOT)/3rdParty/Ice/Ice-3.5.0/install/include \
                -I$(ASKAP_ROOT)/Code/Base/askap/current/ \
                -I$(ASKAP_ROOT)/Code/Base/accessors/current/install/include \
                -I$(ASKAP_ROOT)/Code/Base/askapparallel/current/install/include \
                -I$(ASKAP_ROOT)/Code/Base/scimath/current/install/include \
                -I$(ASKAP_ROOT)/Code/Components/Synthesis/synthesis/current/install/include \
                -I$(ASKAP_ROOT)/Code/Components/CP/askap_imager/current/install/include \
                -I$(ASKAP_ROOT)/Code/Components/Services/calibration/client-cpp/current/install/include \
                -I$(ASKAP_ROOT)/Code/Components/Services/cpdataservices/client-cpp/current/install/include \
                -I$(ASKAP_ROOT)/Code/Interfaces/cpp/current/install/include/icegenerated

ASKAP_DEFS = -DDEBUG
ifeq ($(ASKAP_PATCHED), 1)
ASKAP_DEFS += -DASKAP_PATCHED
endif

ASKAP_LIBDIRS = -L$(ASKAP_ROOT)/3rdParty/log4cxx/log4cxx-0.10.0/install/lib/ \
                -L$(ASKAP_ROOT)/3rdParty/LOFAR/Common/Common-3.3/install/lib \
                -L$(ASKAP_ROOT)/3rdParty/LOFAR/Blob/Blob-1.2/install/lib \
                -L$(ASKAP_ROOT)/3rdParty/cfitsio/cfitsio-3.35/cfitsio/ \
                -L$(ASKAP_ROOT)/3rdParty/boost/boost-1.56.0/install/lib \
                -L$(ASKAP_ROOT)/3rdParty/Ice/Ice-3.5.0/install/lib \
                -L$(ASKAP_ROOT)/Code/Base/askap/current/install/lib \
                -L$(ASKAP_ROOT)/Code/Base/accessors/current/install/lib \
                -L$(ASKAP_ROOT)/Code/Base/scimath/current/install/lib \
                -L$(ASKAP_ROOT)/Code/Components/Synthesis/synthesis/current/install/lib \
                -L$(ASKAP_ROOT)/Code/Components/CP/askap_imager/current/install/lib \
                -L$(ASKAP_ROOT)/Code/Components/Services/calibration/client-cpp/current/install/lib \
                -L$(ASKAP_ROOT)/Code/Components/Services/cpdataservices/client-cpp/current/install/lib \
                -L$(ASKAP_ROOT)/Code/Interfaces/cpp/current/install/lib

CASA_INCDIRS = -I$(ASKAP_ROOT)/3rdParty/casacore/casacore-$(CASACORE_VERSION)/install/include/
CASA_LIBDIRS = -L$(ASKAP_ROOT)/3rdParty/casacore/casacore-$(CASACORE_VERSION)/install/lib/

ASKAP_LIBS = -lIce -lIceUtil -llog4cxx -laskap_askap -lcommon -lblob -laskap_accessors -laskap_synthesis -laskap_scimath -laskap_imager -laskap_calserviceaccessor  -lboost_regex -lboost_system  -laskap_iceinterfaces
CASA_LIBS = -lcasa_ms -lcasa_tables -lcasa_casa -lcasa_measures -lcasa_coordinates -lcfitsio

# Combined flags
CXXFLAGS += -std=c++11 -fPIC -I. -g $(ASKAP_DEFS) $(ASKAP_INCDIRS) $(CASA_INCDIRS) $(DLG_INCDIRS)
LDFLAGS += $(ASKAP_LIBDIRS) $(ASKAP_LIBS) $(CASA_LIBDIRS) $(CASA_LIBS)


#
# These are the ones we need to build
#
OBJS = factory/DaliugeApplicationFactory.o \
       factory/Interface.o \
       factory/LoadParset.o \
       factory/LoadVis.o \
       factory/LoadNE.o \
       factory/NEUtils.o \
       factory/SolveNE.o \
       factory/CalcNE.o \
       factory/OutputParams.o \
       factory/SpectralCube.o \
       factory/InitSpectralCube.o \
       factory/JacalBPCalibrator.o \
       factory/MajorCycle.o \
       factory/RestoreSolver.o

.PHONY: all clean

all: libaskapsoft_dlg.so

clean:
	rm -f factory/*.o daliuge/*.o *.o *.so standalone standalone_cube

libaskapsoft_dlg.so: $(OBJS)
	$(CXX) -shared -o $@ $(OBJS) $(LDFLAGS)

standalone: standalone.o libaskapsoft_dlg.so
	$(CXX) -o $@ standalone.o -pthread -L. $(LDFLAGS) -laskapsoft_dlg
standalone_cube: standalone_cube.o libaskapsoft_dlg.so
	$(CXX) -o $@ standalone_cube.o -pthread -L. $(LDFLAGS) -laskapsoft_dlg

factory/%.s: factory/%.cc
	$(CXX) -S $< $(CXXFLAGS) -o $@

standalone.o: standalone.cpp
	$(CXX) -c $< $(CXXFLAGS) -o $@
standalone_cube.o: standalone_cube.cpp
	$(CXX) -c $< $(CXXFLAGS) -o $@
