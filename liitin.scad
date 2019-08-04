
D=6;
L=20;
module M() { import("m6x20m.stl"); }
module F() { import("m6x20f.stl"); }

/*
translate([40,0,0])
intersection() {
	cube([99,99,20],center=true);
	M();
}

translate([-40,0,0])
difference() {
	cylinder(h=20, d=16, center=true, $fn=60);
	F();
}

translate([0,40,0])
difference() {
	intersection() {
		F();
		cube([99,99,19],center=true);
	}
	import("m12x20m.stl");
}

translate([80,0,0])
difference() {
	M();
	cube([99,99,20],center=true);
}
*/

intersection() {
	difference() {
		union() {
			difference() {
				cylinder(h=25, d=D+3, center=true, $fn=60);
				F();
				translate([-50,-50,0]) cube([100,100,100]);
			}
			M();
		}
		translate([0,-50,-50]) cube([100,100,100]);
	}
	cube([100,100,20], center=true);
}

