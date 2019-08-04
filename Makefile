
.PHONY: all clean plot

all: liitin.stl

clean:
	rm -fv $(wildcard *.stl) $(wildcard *.obj) vertices.ps vertices.txt

m12x20m.stl: m12x20f.stl
	python3 thread.py $@ -t m12 -l 20 -s 0.6 -z -x0.2 -y0.05

m12x20f.stl: thread.py Makefile
	python3 thread.py $@ -t m12 -l 20 -s 0.6 -z -x0.2 -y0.05 -i

liitin.stl: liitin.scad m12x20m.stl m12x20f.stl
	openscad -o $@ $<

#	openscad -o liitin.csg $<
#	hob3l liitin.csg -o $@

plot: vertices.ps
	nohup okular $< >/dev/null 2>&1 &

vertices.ps: vertices.txt plot.p
	rm -f $@
	gnuplot plot.p

vertices.txt: thread.py Makefile
	python3 thread.py --output-2d $@ -t m12 -l 20

