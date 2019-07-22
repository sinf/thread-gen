
KIERRE=kierre1.25in.off kierre1.25in.obj kierre1.25in.stl
STUFF=$(KIERRE) liitin.stl
.PHONY: all clean

all: $(STUFF)

clean:
	rm -fv $(STUFF)

liitin.stl: liitin.scad threads.scad kierre1.25in.off
	openscad -o $@ $<

kierre1.25in.%: thread.py
	python3 thread.py $(KIERRE)


