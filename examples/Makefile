TARGETS = \
		  raw_pointers \
		  stl_example \
		  boost_numerics_example \
		  eigen_example

CXXFLAGS = -g -O0
TARGETS_BUILD = $(TARGETS:%=build/%)

all: $(TARGETS_BUILD)

build/eigen_example: eigen_example.cpp | build
	$(CXX) $(CXXFLAGS) $# $< -o $@ `pkg-config --cflags eigen3`

build/%: %.cpp | build
	$(CXX) $(CXXFLAGS) $# $< -o $@

build:
	mkdir -p build

clean:
	rm -r ./build/
