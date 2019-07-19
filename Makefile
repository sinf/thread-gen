kierre1.25in.obj: thread.py
	python3 thread.py $@


liitin.stl: liitin.scad threads.scad kierre1.25in.obj
	openscad -o $@ $<

