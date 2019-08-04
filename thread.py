#!/usr/bin/python3
from math import *

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
    """ supported by OpenSCAD. maybe faster than STL because of index array """
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

    print("ISO metric thread")
    print("major diameter (before offset):", D)
    print("minor diameter (before offset):", D-H)

    #x0 = 5/8*P
    x1 = 3/8*P
    x2 = 1/16*P
    y0 = -1/4*H + y_p
    y1 = 3/8*H + y_p

    tol_x = cmd_args.tolerance_x[0]
    tol_y = cmd_args.tolerance_y[0]

    # if both internal and external thread use the same tolerance,
    # then tolerance needs to be halved
    tol_x *= 0.5
    tol_y *= 0.5

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
            x1 = max_x
            y0 = H/2 - x1 * tan(pi/3)
        y0 += off_y
        y1 += off_y
        verts = [(x1,y0),(x2,y1),(-x2,y1),(-x1,y0)]

    return verts, P

def rotate_90deg_ccw(x,y):
    return -y, x

def rotate_90deg_cw(x,y):
    return y, -x

def get_normals_xy(verts):
    normals = [(0,0)]
    for i in range(1,len(verts)-1):
        lx,ly = verts[i+1]
        rx,ry = verts[i-1]
        lx,ly = rotate_90deg_cw(lx,ly)
        rx,ry = rotate_90deg_ccw(rx,ry)
        nx = lx + rx
        ny = ly + ry
        n_len = sqrt(nx*nx + ny*ny)
        nx /= n_len
        ny /= n_len
        normals += [(nx,ny)]
    normals += [(0,0)]
    normals[0] = (-normals[1][0], normals[1][1])
    normals[-1] = normals[1]
    return normals

def line_intersection(line1, line2):
    # copy paste from stackoverflow
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])
    def det(a, b): return a[0]*b[1] - a[1]*b[0];
    div = det(xdiff, ydiff)
    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y

def squash(verts, offset_x, offset_y):
    normals = get_normals_xy(verts)
    v2 = []
    for v,n in zip(verts,normals):
        v2 += [(v[0]+n[0]*offset_x,v[1]+n[1]*offset_y)]
    # todo: fix malformed geometry
    return v2

preset_table={
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

    preset = args.thread_preset[0]
    thread_length = args.thread_length[0]
    seglen = args.segment_length[0]

    v_profile_2d, thread_pitch = get_2d_profile(args, preset)

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
    step_angle = 2*pi / revolution_steps
    step_x = thread_pitch / revolution_steps
    total_steps = num_revolutions * revolution_steps

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
    p.add_argument("output", nargs="*")
    p.add_argument("-t", "--thread-preset", nargs=1, type=str, help="M<integer> code")
    p.add_argument("-l", "--thread-length", nargs=1, type=float, default=[15], help="Length of the usable thread (total length is slightly longer)")
    p.add_argument("-s", "--segment-length", nargs=1, type=float, default=[0.2], help="Maximum length for a segment. Controls the final vertex count")
    p.add_argument("-i", "--internal", action="store_true", help="set thread to be internal (nut / to be CSG-subtracted from a solid) instead of external (bolt / to be CSG-unioned to a solid)")
    p.add_argument("-x", "--tolerance-x", nargs=1, type=float, default=[0.12], help="Tolerance along length of the screw")
    p.add_argument("-y", "--tolerance-y", nargs=1, type=float, default=[0.0], help="Tolerance along diameter of the screw")
    p.add_argument("-z", "--z-major", action="store_true", help="have the bolt be parallel to Z axis instead of X")
    p.add_argument("-2", "--output-2d", nargs=1, type=str, help="write XY vertices to this file")
    args = p.parse_args()

    if args.thread_preset is None:
        print("Thread presets:")
        for k in preset_table.keys():
            print(k)
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

if __name__ == "__main__":
    main()

