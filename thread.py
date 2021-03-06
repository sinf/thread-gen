#!/usr/bin/python3
from math import *

# vim: set expandtab:
# vim: set shiftwidth=4:
# vim: set tabstop=4:

class Vec:
    def __init__(self,x,y=None,z=0):
        self.x = x
        self.y = y if y is not None else x
        self.z = z if y is not None else x
    def length(self):
        return sqrt(self.x**2 + self.y**2 + self.z**2)
    def fma(self, other, t=1.0):
        return Vec(self.x + other.x*t, self.y + other.y*t, self.z + other.z*t)
    def cross(self, other):
        return Vec(
            self.y*other.z - other.y*self.z,
            other.x*self.z - self.x*other.z,
            self.x*other.y - other.x*self.y)
    def __mul__(self, t):
        return Vec(self.x*t, self.y*t, self.z*t)
    def __add__(self, other):
        return self.fma(other,1.0)
    def __sub__(self, other):
        return self.fma(other,-1.0)
    def n(self):
        return self * (1.0/self.length())

def write_stl(filepath, vertices, faces):
    """ header is junk, positive octant rule ignored, triangle sorting rule ignored """
    from struct import pack
    with open(filepath,"wb") as f:
        f.write(pack("<80sL", (b'STL'*27)[:80], len(faces)))
        for face in faces:
            v = [vertices[i] for i in face]
            v0,v1,v2 = Vec(*v[0]), Vec(*v[1]), Vec(*v[2])
            n = (v1-v0).cross(v2-v1)
            n = n * (1.0/n.length())
            f.write(pack("3f", n.x, n.y, n.z))
            for x,y,z in v:
                f.write(pack("3f", x, y, z))
            f.write(pack("H", 0))

def write_obj(filepath, vertices, faces):
    with open(filepath,"w") as f:
        for v in vertices:
            f.write("v %.8f %.8f %.8f\n" % v)
        for face in faces:
            f.write("f")
            for i in face:
                f.write(" %d" % (i+1))
            f.write("\n")

def write_off(filepath, vertices, faces):
    """ supported by OpenSCAD. smaller and better than STL because of index array """
    with open(filepath,"w") as f:
        f.write("OFF\n")
        f.write("%d %d 0\n" % (len(vertices),len(faces)))
        for v in vertices:
            f.write("%.8f %.8f %.8f\n" % v)
        for face in faces:
            f.write("%d" % len(face))
            for i in face:
                f.write(" %d" % i)
            f.write("\n")

def quad_strip(idx_a, idx_b):
    """ connect 2 paths (=index arrays) with quads """
    faces = []
    idx_a = iter(idx_a)
    idx_b = iter(idx_b)
    a0 = next(idx_a)
    b0 = next(idx_b)
    for a1,b1 in zip(idx_a, idx_b):
        #faces += [(a0,b0,a1),(a1,b0,b1)]
        faces += [(b0,a0,a1),(b0,a1,b1)]
        a0 = a1
        b0 = b1
    return faces

def make_arc(ox, oy, radius, angle_start, angle_delta, seglen):
    num_segs = int(abs(radius*angle_delta/seglen))
    ##num_segs += (num_segs%2) # force even number of vertices
    num_segs = max(1, num_segs)
    num_verts = num_segs + 1
    angle_inc = angle_delta/num_segs
    angle = angle_start
    v=[]
    for i in range(num_verts):
        x = ox + cos(angle) * radius
        y = oy + sin(angle) * radius
        v += [(x,y,0)]
        angle += angle_inc
    return v

def cubic_bezier(x0, y0, x1, y1, x2, y2, x3, y3, n):
    pts = []
    for i in range(n):
        t = i / (n-1)
        a = (1. - t)**3
        b = 3. * t * (1. - t)**2
        c = 3.0 * t**2 * (1.0 - t)
        d = t**3
        x = a * x0 + b * x1 + c * x2 + d * x3
        y = a * y0 + b * y1 + c * y2 + d * y3
        pts += [x,y]
    return pts

def translated(verts, off_x, c, s):
    result = []
    for x,y,z in verts:
        xx = x + off_x
        yy = c*y - s*z
        zz = s*y + c*z
        result += [(xx,yy,zz)]
    return result

def tip_cubic(w,h,a,n,scale_y,ox,oy):
    """ Make a rounded tip shape using cubic bezier
    w: half of tip width
    h: height of rounded bit. negative to put the curve below line y=0, positive for above
    a: angle of the base triangle's groove part
    """
    u = abs(h)*tan(a*0.5)
    if h<0:
        verts=cubic_bezier(w+u,h,w,0,-w,0,w-u,h,n)
    else:
        verts=cubic_bezier(w,0,w-u,h,-w+u,h,-w,0,n)
    return [(x+ox,scale_y*y+oy) for x,y in verts]

def revolve(shape, num_steps, step_x, step_angle):
    """ shape is a list of (x,y,z) vertices on XY plane, from right to left
    y
    |       ...
    | vN   /   \   v0
    |   ../     \..
    +------------> x
    """
    verts = []
    faces = []
    angle = 0
    pos_x = 0
    verts += translated(shape, 0, 1, 0)
    nv = len(shape)

    for i in range(num_steps-1):
        angle = fmod(angle + step_angle, 2*pi)
        pos_x += step_x
        c = cos(angle)
        s = sin(angle)
        verts += translated(shape, pos_x, c, s)
        i0 = len(verts) - 2*nv
        i1 = len(verts) - nv
        faces += quad_strip(range(i0, i0+nv), range(i1, i1+nv))

    return verts, faces

def polygon_tris(verts):
    verts = iter(verts)
    v0 = next(verts)
    v1 = next(verts)
    faces = []
    for v2 in verts:
        faces += [(v0,v1,v2)]
        v1 = v2
    return faces

def revolve_solid(shape, num_steps, step_x, step_angle, revolution_steps):
    """ like revolve() but also add caps to produce a closed mesh """

    v,f = revolve(shape, num_steps, step_x, step_angle)

    # bridge gap between groove halves
    skip = len(shape)
    rev_vertex_count = skip * revolution_steps
    i0 = 0
    i1 = skip - 1 + rev_vertex_count
    f += quad_strip(range(i0, len(v), skip), range(i1, len(v), skip))

    # cap end
    i0 = len(v) - rev_vertex_count
    i0 -= skip
    i1 = i0 + rev_vertex_count // 2
    i1 -= i1 % skip
    f += polygon_tris(range(i0, i1+skip, skip))
    f += polygon_tris(range(i1, len(v), skip))
    f += polygon_tris([i1] + list(range(len(v)-skip, len(v))) + [i0])

    # cap start
    i0 = skip - 1
    i1 = i0 + revolution_steps//2*skip
    f += polygon_tris(reversed(range(i0, i1+skip, skip)))
    f += polygon_tris(reversed(range(i1, rev_vertex_count+skip, skip)))
    f += polygon_tris([i1] + list(reversed([rev_vertex_count+skip-1] + list(range(skip)))))

    return v,f

def iso_metric_thread(cmd_args, D,P):
    """
    D: major diameter
    P: thread pitch
    """
    H = sqrt(3)/2.0*P
    y_p = D/2 - H/2

    #x0 = 5/8*P
    x1 = 3/8*P
    x2 = 1/16*P
    y0 = -1/4*H + y_p
    y1 = 3/8*H + y_p

    tol_x = cmd_args.tolerance_x[0] / 1000
    tol_y = cmd_args.tolerance_y[0] / 1000

    print("ISO metric thread")
    print("major diameter (before offset):", D)
    print("minor diameter (before offset):", D-H)
    print("tolerance x:", tol_x)
    print("tolerance y:", tol_y)

    off_sign = 1 if cmd_args.internal else -1
    off_x = off_sign * tol_x
    off_y = off_sign * tol_y

    if off_x < -x2:
        # external thread: negative offset
        # x tolerance exceeds width of tip
        # so the flat tip needs to be turned into a sharp triangle
        # surplus is converted to y offset to meet tolerance
        off_y = min(off_y, tan(pi/3) * (off_x + x2))
        off_x = -x2
        x1 += off_x
        x2 = 0
        y0 += off_y
        y1 += off_y
        verts = [(x1,y0),(x2,y1),(-x1,y0)]
    else:
        # internal thread: positive offset
        x1 += off_x
        x2 += off_x
        max_x = 1/2*P - 1e-6
        if x1 > max_x:
            # clip the line going down to the valley
            dy = (x1-max_x) * tan(pi/3)
            y0 += dy
            print("clipping internal thread x1; x1=%.8f, max_x=%.8f, dy=%.8f" % (x1,max_x,dy))
            x1 = max_x
        y0 += off_y
        y1 += off_y
        verts = [(x1,y0),(x2,y1),(-x2,y1),(-x1,y0)]

    return verts, P

def rotate_90deg_ccw(x,y):
    return -y, x

def rotate_90deg_cw(x,y):
    return y, -x

preset_table={
# https://en.wikipedia.org/wiki/ISO_metric_screw_thread
"m2"         :  (iso_metric_thread, (2.0, 0.40)),
"m2-fine"    :  (iso_metric_thread, (2.0, 0.25)),
"m2.5"       :  (iso_metric_thread, (2.5, 0.45)),
"m2.5-fine"  :  (iso_metric_thread, (2.5, 0.35)),
"m3"         :  (iso_metric_thread, (3.0, 0.50)),
"m3-fine"    :  (iso_metric_thread, (3.0, 0.35)),
"m4"         :  (iso_metric_thread, (4.0, 0.50)),
"m4-fine"    :  (iso_metric_thread, (4.0, 0.35)),
"m5"         :  (iso_metric_thread, (5.0, 0.80)),
"m5-fine"    :  (iso_metric_thread, (5.0, 0.50)),
"m6"         :  (iso_metric_thread, (6.0, 1.00)),
"m6-fine"    :  (iso_metric_thread, (6.0, 0.75)),
"m8"         :  (iso_metric_thread, (8.0, 1.00)),
"m8-fine"    :  (iso_metric_thread, (8.0, 0.75)),
"m10"        :  (iso_metric_thread, (10., 1.50)),
"m10-fine"   :  (iso_metric_thread, (10., 1.25)),
"m10-finer"  :  (iso_metric_thread, (10., 1.00)),
"m12"        :  (iso_metric_thread, (12., 1.75)),
"m12-fine"   :  (iso_metric_thread, (12., 1.50)),
"m12-finer"  :  (iso_metric_thread, (12., 1.25)),
"m14"        :  (iso_metric_thread, (14., 2.00)),
"m14-fine"   :  (iso_metric_thread, (14., 1.50)),
"m16"        :  (iso_metric_thread, (16., 2.00)),
"m16-fine"   :  (iso_metric_thread, (16., 1.50)),
"m18"        :  (iso_metric_thread, (18., 2.50)),
"m18-fine"   :  (iso_metric_thread, (18., 2.00)),
"m18-finer"  :  (iso_metric_thread, (18., 1.50)),
"m20"        :  (iso_metric_thread, (20., 2.50)),
"m20-fine"   :  (iso_metric_thread, (20., 2.00)),
"m20-finer"  :  (iso_metric_thread, (20., 1.50)),
"m22"        :  (iso_metric_thread, (22., 2.50)),
"m22-fine"   :  (iso_metric_thread, (22., 2.00)),
"m22-finer"  :  (iso_metric_thread, (22., 1.50)),
"m24"        :  (iso_metric_thread, (24., 3.00)),
"m24-fine"   :  (iso_metric_thread, (24., 2.00)),
"m27"        :  (iso_metric_thread, (27., 3.00)),
"m27-fine"   :  (iso_metric_thread, (27., 2.00)),
"m30"        :  (iso_metric_thread, (30., 3.50)),
"m30-fine"   :  (iso_metric_thread, (30., 2.00)),
"m33"        :  (iso_metric_thread, (33., 3.50)),
"m33-fine"   :  (iso_metric_thread, (33., 2.00)),
"m36"        :  (iso_metric_thread, (36., 4.00)),
"m36-fine"   :  (iso_metric_thread, (36., 3.00)),
"m39"        :  (iso_metric_thread, (39., 4.00)),
"m39-fine"   :  (iso_metric_thread, (39., 3.00)),
"m42"        :  (iso_metric_thread, (42., 4.50)),
"m42-fine"   :  (iso_metric_thread, (42., 3.00)),
"m45"        :  (iso_metric_thread, (45., 4.50)),
"m45-fine"   :  (iso_metric_thread, (45., 3.00)),
"m48"        :  (iso_metric_thread, (48., 5.00)),
"m48-fine"   :  (iso_metric_thread, (48., 3.00)),
"m52"        :  (iso_metric_thread, (52., 5.00)),
"m52-fine"   :  (iso_metric_thread, (52., 4.00)),
"m56"        :  (iso_metric_thread, (56., 5.50)),
"m56-fine"   :  (iso_metric_thread, (56., 4.00)),
"m60"        :  (iso_metric_thread, (60., 5.50)),
"m60-fine"   :  (iso_metric_thread, (60., 4.00)),
"m64"        :  (iso_metric_thread, (64., 6.00)),
"m64-fine"   :  (iso_metric_thread, (64., 4.00)),
}

def get_2d_profile(cmd_args, preset):
    preset = preset.lower()
    if preset not in preset_table:
        print("Unknown preset:", preset)
    else:
        func, params = preset_table[preset]
        return func(cmd_args, *params)

def thread(args):
    verts=[]
    faces=[]

    thread_length = args.thread_length[0]
    seglen = args.segment_length[0] / 1000


    if args.thread_preset is None:
      v_profile_2d, thread_pitch = iso_metric_thread(args, args.thread_diameter, args.thread_pitch)
    else:
      v_profile_2d, thread_pitch = get_2d_profile(args, args.thread_preset)

    if args.output_2d:
        print("Dumping 2d vertices to", args.output_2d[0])
        with open(args.output_2d[0],"w") as f:
            for x,y in v_profile_2d:
                f.write("%.10f %.10f\n" % (x,y))

    center_x = thread_pitch + thread_length/2

    # add z coordinates
    v_profile_2d_z = [(x-center_x,y,0) for x,y in v_profile_2d]

    num_revolutions = ceil(thread_length / thread_pitch) + 2

    max_y = max(v[1] for v in v_profile_2d_z)
    min_y = min(v[1] for v in v_profile_2d_z)
    revolution_steps = ceil(2*pi*max_y / seglen)

    revolution_steps = min(revolution_steps, 5000)
    revolution_steps = max(revolution_steps, 16)

    step_angle = 2*pi / revolution_steps
    step_x = thread_pitch / revolution_steps
    total_steps = num_revolutions * revolution_steps

    print("max segment length:", seglen)
    print("thread pitch: %.8f" % thread_pitch)
    print("y coords range: [%.8f, %.8f]" % (min_y, max_y))

    print("revolutions:", num_revolutions)
    print("steps/revolution:", revolution_steps)

    from os import getpid
    print("process id:", getpid())

    v,f=revolve_solid(v_profile_2d_z, total_steps, step_x, step_angle, revolution_steps)

    print("total vertices:", len(v))
    print("total facets:", len(f))

    if args.z_major:
        v = [(a[2],-a[1],a[0]) for a in v]

    return v,f

def main():
    from argparse import ArgumentParser
    p=ArgumentParser()
    p.add_argument("output", nargs="*", help="suffix can be one of: .off .obj .stl")
    p.add_argument("-t", "--thread-preset", type=str, default=None, help="preset name or \"list\" or \"list-all\"")
    p.add_argument("-d", "--thread-diameter", type=float, help="major diameter. used if -t not specified")
    p.add_argument("-p", "--thread-pitch", type=float, help="thread pitch. used if -t not specified")
    p.add_argument("-l", "--thread-length", nargs=1, type=float, default=[15], help="Length of the usable thread (total length is slightly longer) as millimeters")
    p.add_argument("-s", "--segment-length", nargs=1, type=float, default=[200], help="Maximum length for a segment as micrometers. Controls the final vertex count")
    p.add_argument("-i", "--internal", action="store_true", help="set thread to be internal (nut / to be CSG-subtracted from a solid) instead of external (bolt / to be CSG-unioned to a solid)")
    p.add_argument("-x", "--tolerance-x", nargs=1, type=float, default=[120], help="Tolerance along length of the screw as micrometers")
    p.add_argument("-y", "--tolerance-y", nargs=1, type=float, default=[150], help="Tolerance along diameter of the screw as micrometers")
    p.add_argument("-z", "--z-major", action="store_true", help="have the bolt be parallel to Z axis instead of X")
    p.add_argument("-2", "--output-2d", nargs=1, type=str, help="write XY vertices to this file")
    args = p.parse_args()

    if args.thread_preset and "list" in args.thread_preset.lower():
        print("%-15s | %-8s | %-8s" % ("Preset","Diameter","Pitch"))
        for k in preset_table.keys():
            if "all" in args.thread_preset.lower() or "fine" not in k:
               print("%-15s , %-8.2f , %-8.2f" % ((k,)+preset_table[k][1]))
        exit(0)

    verts,faces = thread(args)

    exporters = {
        "obj":write_obj,
        "off":write_off,
        "stl":write_stl,
    }

    for fn in args.output:
        ext = fn[-3:]
        print("Output to:", fn)
        func=exporters.get(ext, write_obj)
        func(fn, verts, faces)

    if len(args.output) == 0:
        print("No output files")

if __name__ == "__main__":
    main()

