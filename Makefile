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
FFTW = true
OMP = false
ARCH = MAC
LIBPATH=$(HOME)/lib
INSTALLDIR=$(LIBPATH)/modules

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

#Extra libraries and includes:
ifeq ($(FFTW),true)
FFTWINCLUDE=-I$(FFTW_DIR)/include
LDFFTW=-L$(FFTW_DIR)/lib
LIBADDFFTW=-lfftw3
FFTWDEFINE=-DFFTW
endif

#Compiler Optimization Level:
ifeq ($(ARCH),INTEL)
OPT              = -O2 -march=native -ipo
FLAGS            = -fPIC -Wall -debug -std=c++11
LD               = icpc
LAPACKFLAGS      =
#LAPACKLIBS       = -lmkl_intel_lp64 -lmkl_core -lmkl_intel_thread -lmkl_lapack95_lp64 -lmkl_blas95_lp64
LAPACKLIBS       = -mkl
LINK             = ${LAPACKLIBS} -shared -Wl,-soname,PyModules.so -o PyModules.so.1.0 *.o
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
LINK             = $(LAPACKLIBS) -shared -Wl,-soname,PyModules.so -o PyModules.so.1.0 *.o
FINISH           = cp PyModules.so.1.0 ${INSTALLDIR}/; ln -sf ${INSTALLDIR}/PyModules.so.1.0 ${INSTALLDIR}/PyModules.so
endif

ifeq ($(ARCH),MAC)
OPT              = -O2 -march=native
FLAGS            = -fPIC -Wall -g
LIBADDPYTHON         = -L$(PYTHON_DIR) -lpython2.7
LIBADDBOOST      = -lboost_python
LD               = g++
LINK             = -framework Accelerate -dynamiclib $(LDFFTW) $(LIBADDFFTW) -L$(LIBPATH) $(LIBADDBOOST) $(LIBADDPYTHON) -lmathutils -lpertutils
FINISH           = ln -sf
endif



ifeq ($(ARCH),INTEL)
LIBADD = $(LDFFTW) $(LIBADDFFTW) -lpthread -lm
MYINCLUDEDIR = -I./ $(FFTWINCLUDE) -I../mathutils/ -I../pertutils/
DEFINES = -DINTEL $(FFTWDEFINE)
endif

ifeq ($(ARCH),VAN)
LIBADD = $(LDFFTW) $(LIBADDFFTW) -lpthread -lm
MYINCLUDEDIR = -I./ $(FFTWINCLUDE) -I../mathutils/ -I../pertutils/
DEFINES = -DVAN $(FFTWDEFINE)
endif

ifeq ($(ARCH),CRAY)
LIBADD = $(LDFFTW) $(LIBADDFFTW) -lpthread -lm
MYINCLUDEDIR = -I./ $(FFTWINCLUDE) -I../mathutils/ -I../pertutils/
DEFINES = -DVAN -DCRAY $(FFTWDEFINE)
endif

ifeq ($(ARCH),MAC)
LIBADD = $(LDFFTW) $(LIBADDFFTW) -lpthread -lm
MYINCLUDEDIR = -I./ $(FFTWINCLUDE) -I../mathutils/ -I../pertutils/ -I/opt/local/include -I$(PYTHON_DIR)/include/python2.7
DEFINES = -DMAC $(FFTWDEFINE)
endif

#Complete Set of Flags:
CFLAGS = ${DEFINES} ${MYINCLUDEDIR} ${FLAGS} ${OPT}

all::
	${CC} ${CFLAGS} -c LuscherClm.cpp -o LuscherClm.o ${LIBADD}
	${LD} ${LINK} -o $(INSTALLDIR)/LuscherClm.1.0.so LuscherClm.o
	${FINISH} ${INSTALLDIR}/LuscherClm.1.0.so ${INSTALLDIR}/LuscherClm.so

clean::
	-/bin/rm -f *.o *.a *.so.*
