
D=6;
L=20;
module M() { import("stuff/m6x20m.stl"); }
module F() { import("stuff/m6x20f.stl"); }

render(convexity=10)
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

