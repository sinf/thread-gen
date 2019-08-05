tol_radial=[25, 50, 100, 150];
tol_layer=[50, 70, 90, 110, 150, 170, 200, 220];
// above: microns. must be the first 2 lines

columns = len(tol_radial);
rows = len(tol_layer);

//font = "Noto Sans UI:style=Bold";
font = "Tahoma:style=bold";
//use <pcf6x13B.ttf>; font = "pcf6x13B";

d = 6; // hole diameter
spacing = 2;
z_top = 5;
text_depth = 0.8;
text_size = 3.4;
text_bevel = 0.3;
z_text = z_top-text_depth;
border_n = 12;
border_p = 7;

enable_threads = true;
enable_text_bevel = true;

if ($preview) {
	enable_threads = false;
	enable_text_bevel = false;
}

$fs = 1;
$fa = 40;

module rounded_plate(dim, r=7) {
	z = 0;
	h = dim[2];
	x0 = r;
	x1 = dim[0] - r;
	y0 = r;
	y1 = dim[1] - r;
	n = 30;
	hull() {
		translate([x0,y0,z]) cylinder(r=r,h=h,$fn=n);
		translate([x1,y0,z]) cylinder(r=r,h=h,$fn=n);
		translate([x0,y1,z]) cylinder(r=r,h=h,$fn=n);
		translate([x1,y1,z]) cylinder(r=r,h=h,$fn=n);
	}
}

module number_label(x, y, h, v, t) {
	translate([x,y,0])
	scale([2.0/len(t), 1, 1])
	text(t, text_size, font, halign=h, valign=v, spacing=1.2);
}

module text_outline_2d() {
	for(c=[0:columns-1])
		number_label(c*(d+spacing), -d-spacing+3, "center", "top", str(tol_radial[c]));
	for(r=[0:rows-1])
		number_label(-d-spacing+4,r*(d+spacing),"right", "center", str(tol_layer[r]));
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
				if (enable_threads) {
					import(str("tolerance_test/m6-",tol_radial[c],"-",tol_layer[r],".stl"));
				} else {
					cylinder(d=d,h=z_top+2,center=true);
				}
			}
		}
	}

	// engrave text
	translate([0,0,z_text]) {
		union() {
			linear_extrude(100.0)
			text_outline_2d();

			if (enable_text_bevel) {
				translate([0,0,text_depth])
				minkowski() {
					linear_extrude(0.001) // workaround mixing 2d and 3d
					offset(delta=-0.001)
					text_outline_2d();

					cylinder(h=2*text_bevel, r1=0, r2=2*text_bevel, center=true);
				}
			}
		}
	}
}

