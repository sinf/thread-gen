tol_radial=[150, 180, 210, 240];
tol_layer=[100, 150, 200, 250];
// above: microns. must be the first 2 lines

columns = len(tol_radial);
rows = len(tol_layer);

//font = "Noto Sans UI:style=Bold";
font = "Tahoma:style=bold";
//use <pcf6x13B.ttf>; font = "pcf6x13B";

d = 6; // hole diameter
spacing = 2;
z_top = 4; // also thickness of the plate
text_depth = 0.8;
text_size = 3.7;
text_bevel = 0.3;
border_nx = 13.5;
border_ny = 11;
border_p = 7;
z_text = z_top-text_depth;

enable_threads = true;
enable_text_bevel = true;

if ($preview == true) {
	enable_threads = false;
	enable_text_bevel = false;
}

echo("Import thread models:", enable_threads);
echo("Minkowski text bevel:", enable_text_bevel);

$fs = 1;
$fa = 40;

module beveled_cylinder(r, h, b1, b2) {
	n=30;
	hull() {
		cylinder(h=min(b1,h/2), r1=r-b1, r2=r, $fn=n);
		translate([0,0,h-b2]) cylinder(h=min(b2,h/2), r1=r, r2=r-b2, $fn=n);
	}
}

module rounded_plate(dim, r=7) {
	z = 0;
	h = dim[2];
	x0 = r;
	x1 = dim[0] - r;
	y0 = r;
	y1 = dim[1] - r;
	b1 = 2;
	b2 = 1;
	hull() {
		translate([x0,y0,z]) beveled_cylinder(r=r,h=h,b1=b1,b2=b2);
		translate([x1,y0,z]) beveled_cylinder(r=r,h=h,b1=b1,b2=b2);
		translate([x0,y1,z]) beveled_cylinder(r=r,h=h,b1=b1,b2=b2);
		translate([x1,y1,z]) beveled_cylinder(r=r,h=h,b1=b1,b2=b2);
	}
}

module number_label(x, y, h, v, t) {
	translate([x,y,0])
	scale([2.0/len(t), 1, 1])
	text(t, text_size, font, halign=h, valign=v, spacing=1.17);
}

module text_outline_2d() {
	for(c=[0:columns-1])
		number_label(c*(d+spacing), -d-spacing+3, "center", "top", str(tol_radial[c]));
	for(r=[0:rows-1])
		number_label(-d-spacing+4,r*(d+spacing),"right", "center", str(tol_layer[r]));
}

difference() {
	translate([-border_nx,-border_ny,0])
	rounded_plate([
		(columns-1)*(d+spacing) + border_nx + border_p,
		(rows-1)*(d+spacing) + border_ny + border_p,
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
		if (enable_text_bevel) {
			union() {
				linear_extrude(100.0)
				text_outline_2d();

				translate([0,0,text_depth])
				minkowski() {
					linear_extrude(0.001) // workaround mixing 2d and 3d
					offset(delta=-0.001)
					text_outline_2d();

					cylinder(h=2*text_bevel, r1=0, r2=2*text_bevel, center=true);
				}
			}
		} else {
			linear_extrude(100.0)
			text_outline_2d();
		}
	}
}

