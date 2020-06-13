TARGETS := \
		  raw_pointers \
		  stl_example

BOOST ?= 1
EIGEN ?= 1

CXXFLAGS := -g -O0


ifeq ($(BOOST),1)
TARGETS += eigen_example
endif

ifeq ($(EIGEN),1)
TARGETS += boost_numerics_example
endif

_TARGETS := $(TARGETS:%=build/%)


all: $(_TARGETS)

build/eigen_example: eigen_example.cpp | build
	$(CXX) $(CXXFLAGS) $# $< -o $@ `pkg-config --cflags eigen3`

build/%: %.cpp | build
	$(CXX) $(CXXFLAGS) $# $< -o $@

build:
	mkdir -p build

clean:
	rm -r ./build/
