
.PHONY: all clean plot

all: liitin.stl

plot: vertices.ps
	nohup okular $< >/dev/null 2>&1 &

clean:
	rm -fv $(wildcard *.stl)

m12x20m.stl: thread.py Makefile
	python3 thread.py -t m12 -l 20 -y -0.2 -s 0.6 -z m12x20m.stl
	python3 thread.py -t m12 -l 20 -y 0.2 -s 0.6 -z m12x20f.stl

m12x20f.stl: m12x20m.stl


liitin.stl: liitin.scad m12x20m.stl m12x20f.stl
	openscad -o $@ $<

#	openscad -o liitin.csg $<
#	hob3l liitin.csg -o $@

vertices.ps: vertices.dat plot.p
	rm -f $@
	gnuplot plot.p

