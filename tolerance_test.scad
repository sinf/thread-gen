

// microns
tol_radial=[10, 30, 60, 100];
tol_layer=[50, 70, 90, 110, 150, 170, 200, 220];
columns = 4;
rows = 8;

font = "Noto Sans UI:style=Bold";
//use <pcf6x13B.ttf>; font = "pcf6x13B";

d = 6; // hole diameter
spacing = 2;
z_top = 5;
z_text = z_top-0.8;
border_n = 12;
border_p = 7;

fake_holes = false;

$fs = 1;
$fa = 10;

module rounded_plate(dim, r=7) {
	z = 0;
	h = dim[2];
	x0 = r;
	x1 = dim[0] - r;
	y0 = r;
	y1 = dim[1] - r;
	hull() {
		translate([x0,y0,z]) cylinder(r=r,h=h);
		translate([x1,y0,z]) cylinder(r=r,h=h);
		translate([x0,y1,z]) cylinder(r=r,h=h);
		translate([x1,y1,z]) cylinder(r=r,h=h);
	}
}

module number_label(x, y, h, v, t) {
	translate([x,y,0])
	scale([2.0/len(t), 1.3, 1])
	text(t, 3.5, font, halign=h, valign=v, spacing=1.25);
}

difference() {
	translate([-border_n,-border_n,0])
	rounded_plate([
		(columns-1)*(d+spacing) + border_n + border_p,
		(rows-1)*(d+spacing) + border_n + border_p,
		z_top]);

	// subtract internal threads
	for(c=[0:columns-1]) {
		for(r=[0:rows-1]) {
			translate([c*(d+spacing), r*(d+spacing), z_top/2]) {
				if (fake_holes) {
					cylinder(d=d,h=z_top+2,center=true);
				} else {
					import(str("tolerance_test/m6-",tol_radial[c],"-",tol_layer[r],".stl"));
				}
			}
		}
	}

	// engrave text
	translate([0,0,z_text])
	linear_extrude(100.0) {
		for(col=[0:columns-1])
			number_label(col*(d+spacing), -d-spacing+3, "center", "top", str(tol_radial[col]));
		for(row=[0:rows-1])
			number_label(-d-spacing+4,row*(d+spacing),"right", "center", str(tol_layer[row]));
	}
}

