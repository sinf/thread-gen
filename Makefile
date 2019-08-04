
.PHONY: all clean plot

M=m6
L=20
ARGS=-t$(M) -l$(L) -s0.6 -x0.2 -y0.05 -z

all: liitin.stl

clean:
	rm -fv $(wildcard *.stl) $(wildcard *.obj) vertices.ps vertices.txt

$(M)x$(L)m.stl: $(M)x$(L)f.stl
	python3 thread.py $@ $(ARGS)

$(M)x$(L)f.stl: thread.py Makefile
	python3 thread.py $@ $(ARGS) -i

liitin.stl: liitin.scad $(M)x$(L)m.stl $(M)x$(L)f.stl
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

