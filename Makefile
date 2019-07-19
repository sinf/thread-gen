
STUFF=kierre1.25in.off kierre1.25in.obj
.PHONY: all clean

all: $(STUFF)

clean:
	rm -fv $(STUFF)

liitin.stl: liitin.scad threads.scad kierre1.25in.off
	openscad -o $@ $<

kierre1.25in.off: thread.py
	python3 thread.py $@

kierre1.25in.obj: thread.py
	python3 thread.py $@

