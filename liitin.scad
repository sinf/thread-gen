
translate([40,0,0])
intersection() {
	cube([99,99,20],center=true);
	import("m12x20m.stl");
}

translate([-40,0,0])
difference() {
	cylinder(h=20, d=16, center=true, $fn=60);
	import("m12x20f.stl");
}

translate([0,40,0])
difference() {
	intersection() {
		import("m12x20f.stl");
		cube([99,99,19],center=true);
	}
	import("m12x20m.stl");
}

translate([80,0,0])
difference() {
	import("m12x20m.stl");
	cube([99,99,20],center=true);
}

