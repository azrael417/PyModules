# This file
MAKEFILE = Makefile

#----------------------------------------------------------------------
#  User choices - edit to suit
#----------------------------------------------------------------------
# 0. Shell (if it really matters)

#SHELL = /bin/bash

#----------------------------------------------------------------------
# 1. Architecture

# Compiling for a parallel machine?  blank for a scalar machine
OMP = false
ARCH = MAC
INSTALLDIR=${HOME}/lib/modules

#Compiler Type:
ifeq ($(ARCH),INTEL)
ifeq ($(strip ${OMP}),true)
CC = icpc -openmp
else
CC = icpc
endif
endif

ifeq ($(ARCH),VAN)
ifeq ($(strip ${OMP}),true)
CC = g++ -fopenmp
else
CC = g++
endif
endif

ifeq ($(ARCH),CRAY)
CC = CC
endif

ifeq ($(ARCH),MAC)
ifeq ($(strip ${OMP}),true)
CC = g++ -fopenmp
else
CC = g++
endif
endif


#Compiler Optimization Level:
ifeq ($(ARCH),INTEL)
OPT              = -O2 -march=native -ipo
FLAGS            = -fPIC -Wall -debug -std=c++11
LD               = icpc
LAPACKFLAGS      =
#LAPACKLIBS       = -lmkl_intel_lp64 -lmkl_core -lmkl_intel_thread -lmkl_lapack95_lp64 -lmkl_blas95_lp64
LAPACKLIBS       = -mkl
LINK             = ${LAPACKLIBS} -shared -Wl,-soname,libmathutils.so -o libmathutils.so.1.0 *.o
FINISH           = cp PyModules.so.1.0 ${INSTALLDIR}/; ln -sf ${INSTALLDIR}/PyModules.so.1.0 ${HOME}/lib/PyModules.so
endif

ifneq (,$(filter $(ARCH),VAN CRAY))
OPT              = -O2 -march=native
FLAGS            = -fPIC -Wall -g
LD               = g++
ifeq ($(ARCH),VAN)
LAPACKLIBS       = -lgsl -lgslcblas -lblas -llapack
endif
ifeq ($(ARCH),CRAY)
LAPACKLIBS       =
endif
LINK             = $(LAPACKLIBS) -shared -Wl,-soname,libmathutils.so -o libmathutils.so.1.0 *.o
FINISH           = cp PyModules.so.1.0 ${INSTALLDIR}/; ln -sf ${INSTALLDIR}/PyModules.so.1.0 ${INSTALLDIR}/PyModules.so
endif

ifeq ($(ARCH),MAC)
OPT              = -O2 -march=native
FLAGS            = -fPIC -Wall -g
LD               = g++
LINK             = -dynamiclib -Wl,-headerpad_max_install_names,-undefined,dynamic_lookup,-compatibility_version,1.0,-current_version,1.0,-install_name,${INSTALLDIR}/PyModules.dylib -o ${INSTALLDIR}/PyModules.1.0.dylib *.o
LAPACKFLAGS      = -framework Accelerate
LAPACKLIBS       =
FINISH           = ln -sf ${INSTALLDIR}/PyModules.1.0.dylib ${INSTALLDIR}/PyModules.dylib
endif


#Extra libraries and includes:

ifeq ($(ARCH),INTEL)
LIBADD = -lpthread -lm
MYINCLUDEDIR = -I./
DEFINES = -DINTEL
endif

ifeq ($(ARCH),VAN)
LIBADD = -lpthread -lm
MYINCLUDEDIR = -I./
DEFINES = -DVAN
endif

ifeq ($(ARCH),CRAY)
LIBADD = -lpthread -lm
MYINCLUDEDIR = -I./
DEFINES = -DVAN -DCRAY
endif

ifeq ($(ARCH),MAC)
LIBADD = -lpthread -lm
MYINCLUDEDIR = -I./
DEFINES = -DMAC
endif

#Complete Set of Flags:
CFLAGS = ${DEFINES} ${MYINCLUDEDIR} ${FLAGS} ${OPT}

all::
${CC} ${CFLAGS} -c PyClm.cpp -o PyClm.o ${LIBADD}
${LD} ${LINK}
${FINISH}

clean::
-/bin/rm -f *.o *.a *.so.*
