#
# Skeleton Makefile to compile the code in this module as a shared library. It
# assumes ASKAPSoft can be found under ASKAP_ROOT and that DALiuGE is installed
# and can be loaded by the python executable
#

# DALiuGE include dir
DLG_INCDIRS = -I`python -c "import dfms; print(dfms.get_include_dir())"`

# ASKAPSoft dependencies
ASKAP_INCDIRS = -I$(ASKAP_ROOT)/3rdParty/log4cxx/log4cxx-0.10.0/install/include \
                -I$(ASKAP_ROOT)/3rdParty/LOFAR/Common/Common-3.3/Common-3.3/include \
                -I$(ASKAP_ROOT)/Code/Base/askap/current/
ASKAP_LIBDIRS = -L$(ASKAP_ROOT)/3rdParty/log4cxx/log4cxx-0.10.0/install/lib/ \
				    -L$(ASKAP_ROOT)/3rdParty/LOFAR/Common \
                    -L$(ASKAP_ROOT)/Code/Base/askap/current/install/lib

CASA_INCDIRS = -I$(ASKAP_ROOT)/3rdParty/casacore/casacore-2.0.3/install/include/
CASA_LIBDIRS = -L$(ASKAP_ROOT)/3rdParty/casacore/casacore-2.0.3/install/lib/

ASKAP_LIBS = -llog4cxx -laskap_askap
CASA_LIBS = -lcasa_casa

# Combined flags
CXXFLAGS += -fPIC -I. $(ASKAP_INCDIRS) $(DLG_INCDIRS)
LDFLAGS += $(ASKAP_LIBDIRS) $(ASKAP_LIBS) $(CASA_LIBDIRS) $(CASA_LIBS)


#
# These are the ones we need to build
#
OBJS = daliuge/DaliugeApplication.o \
       factory/DaliugeApplicationFactory.o \
       factory/Example.o \
       factory/Interface.o

.PHONY: all clean

all: libaskapsoft_dlg.so

clean:
	rm -f factory/*.o daliuge/*.o

libaskapsoft_dlg.so: $(OBJS)
	$(CXX) -shared -o $@ $(OBJS) $(LDFLAGS)
