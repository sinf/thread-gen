
.PHONY: all clean plot

# dependencies of demo.scad
all: stuff/m6x20m.stl stuff/m6x20f.stl ;

stuff/m6x20m.stl:
	python3 thread.py $@ -t m6 -l 20 -s600 -x200 -y50 -z

stuff/m6x20f.stl:
	python3 thread.py $@ -t m6 -l 20 -s600 -x200 -y50 -z -i

# view 2d profile of thread
plot: stuff/vertices.ps
	nohup okular $< >/dev/null 2>&1 &

stuff/vertices.ps: stuff/vertices.txt stuff/plot.p
	rm -f $@
	gnuplot stuff/plot.p

stuff/vertices.txt: thread.py Makefile
	python3 thread.py --output-2d $@ -t m12 -l20

clean:
	rm -fv stuff/vertices.ps stuff/vertices.txt


