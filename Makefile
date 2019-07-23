
KIERRE=kierre1.25in.off kierre1.25in.obj kierre1.25in.stl
STUFF=$(KIERRE) liitin.stl
.PHONY: all clean plot

plot: vertices.ps
	nohup okular $< >/dev/null 2>&1 &

all: $(STUFF)

clean:
	rm -fv $(STUFF)

liitin.stl: liitin.scad kierre1.25in.stl
	openscad -o $@ $<

#	openscad -o liitin.csg $<
#	hob3l liitin.csg -o $@

kierre1.25in.%: thread.py
	python3 thread.py $(KIERRE)

vertices.dat: kierre1.25in.stl

vertices.ps: vertices.dat plot.p
	rm -f $@
	gnuplot plot.p

