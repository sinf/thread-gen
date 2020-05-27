
module test_piece(f1, f2, l) {
	z=l/2-1;
	w=15;

	difference() {
		color("lightblue")
		translate([-w/2,-w/2,0])
		cube([w, w, 10]);

		translate([0,0,z])
		rotate(-90,[0,1,0])
		import(f2);

		color("red")
		translate([0,-100,-100])
		cube([100, 200, 200]);
	}

	translate([0,0,z])
	rotate(-90,[0,1,0])
	color("green") import(f1);
}

m=[3,5,6];
l=[20,30,40];

for(i=[0:2]) {
	for(j=[0:2]) {
		echo(str("ex/M",m[i],"x",l[j],".stl"));
		translate([i*30, j*30, 0])
		test_piece(
			str("ex/M",m[i],"x",l[j],".stl"),
			str("ex/M",m[i],"x",l[j],"i.stl"),
			l[j]);
	}
}

