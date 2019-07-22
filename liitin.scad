
/*
module english_thread (diameter=0.25, threads_per_inch=20, length=1,
                      internal=false, n_starts=1, thread_size=-1, groove=false,
                      square=false, rectangle=0, angle=30, taper=0, leadin=0,
                      leadfac=1.0, test=false)
*/

$fn=50;


/*
difference() {
	cylinder(h=10, d=30);
	import("kierre1.25in.off");
}
*/

module kierre() {
	import("kierre1.25in.off");
}

kierre();

