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
        f.write(pack("<80xL", len(faces)))
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

def write_verts_xy(filepath, vertices):
    """ for use with gnuplot """
    with open(filepath,"w") as f:
        for x,y,z in vertices:
            f.write("%.10f %.10f\n" % (x,y))

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

def rounded_corner(ax, ay, bx, by, cx, cy, dx, dy, r):
    a,b,c,d = Vec(ax,ay), Vec(bx,by), Vec(cx,cy), Vec(dx,dy)
    p0 = b + (a-b).n() * r
    p1 = c + (d-c).n() * r
    return [(ax,ay),cubic_bezier(p0.x,p0.y,bx,by,cx,cy,p1.x,p1.y),(dx,dy)]

def translated(verts, off_x, c, s):
    result = []
    for x,y,z in verts:
        xx = x + off_x
        yy = c*y - s*z
        zz = s*y + c*z
        result += [(xx,yy,zz)]
    return result

def revolve(shape, num_steps, step_x, step_angle):
    """ shape is a set of vertices on XY plane, from right to left
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

def revolve_solid(shape, num_steps, step_x, step_angle, revolution_steps):

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


def polygon_tris(verts):
    verts = iter(verts)
    v0 = next(verts)
    v1 = next(verts)
    faces = []
    for v2 in verts:
        faces += [(v0,v1,v2)]
        v1 = v2
    return faces

def rounded_part(below, a, h):
    if below:
        pass
    else:
        pass
        # sin(a) = r / y
        # sin(a) = f / h
        # y = h + r
        # f = k*h
        # sin(a) = (y-h)/y

def thread_shape(H,P,cut_int,cut_ext,round_below_int,round_below_ext):
    """
    H: height of base triangle
    P: width of base triangle
    cut_int: where to cut internal corner (as a fraction of H)
    cut_int: where to cut external corner (as a fraction of H)
    round_below_int: should inner corner be rounded below the cutting line (vs above)
    round_below_ext: should external corner be rounded below the cutting line (vs above)
    """
    a = 0.5 * P / H
    #todo

def whitworth_thread_shape(args):

    minor_r = args.minor_diameter * 0.5
    major_r = args.major_diameter * 0.5

    base_triangle_height = args.major_diameter - args.minor_diameter
    base_triangle_width = args.thread_pitch
    alpha = atan(2*base_triangle_height / base_triangle_width)
    gamma = pi/2 - alpha

    tip_circle_pos = args.round_radius_tip / sin(alpha)
    tip_arc_angle = 2*alpha #2*(pi/2 - gamma)
    tip_arc_length = tip_arc_angle * args.round_radius_tip
    v_tip = make_arc(
        0,
        minor_r + base_triangle_height - args.round_radius_tip,
        args.round_radius_tip,
        pi/2 - tip_arc_angle*0.5,
        tip_arc_angle,
        args.segment_length)

    groove_circle_pos = args.round_radius_groove / sin(alpha)
    groove_arc_angle = tip_arc_angle
    groove_arc_length = groove_arc_angle * args.round_radius_groove
    v_groove = make_arc(
        -base_triangle_width*0.5,
        minor_r + args.round_radius_groove,
        args.round_radius_groove,
        -(pi/2 - groove_arc_angle*0.5),
        -groove_arc_angle,
        args.segment_length)

    v_groove_l = v_groove[:len(v_groove)//2]
    v_groove_r = [(v[0]+base_triangle_width,v[1],v[2]) for v in v_groove[len(v_groove)//2:]]
    v_profile_2d = v_groove_r + v_tip + v_groove_l

    print("verts / tip:", len(v_tip))
    print("verts / groove:", len(v_groove))
    print("verts / 2d profile:", len(v_profile_2d))

    return v_profile_2d

def iso_metric_thread(D,P,offset=0.2):
    """
    D: major diameter
    P: thread pitch
    offset: female positive, male negative
    """
    H = sqrt(3)/2.0*P
    R = offset + D/2
    r = R - 5/8*H

    base_triangle_height = H
    base_triangle_width = P

    v_profile_2d = [(P/2,r,0),(3/8*P,r,0),(P/16,R,0),(-P/16,R,0),(-3/8*P,r,0)]

    print("verts / 2d profile:", len(v_profile_2d))

    return (v_profile_2d,P)

def iso_metric_thread_m(m):
    params={
    # D, P
    "M2"         :  (2.0,  0.40),
    "M2-fine"    :  (2.0,  0.25),
    "M2.5"       :  (2.5,  0.45),
    "M2.5-fine"  :  (2.5,  0.35),
    "M3"         :  (3.0,  0.50),
    "M3-fine"    :  (3.0,  0.35),
    "M4"         :  (4.0,  0.50),
    "M4-fine"    :  (4.0,  0.35),
    "M5"         :  (5.0,  0.80),
    "M5-fine"    :  (5.0,  0.50),
    "M6"         :  (6.0,  1.00),
    "M6-fine"    :  (6.0,  0.75),
    "M8"         :  (8.0,  1.00),
    "M8-fine"    :  (8.0,  0.75),
    "M10"        :  (10.,  1.50),
    "M10-fine"   :  (10.,  1.25),
    "M10-finer"  :  (10.,  1.00),
    "M12"        :  (12.,  1.75),
    "M12-fine"   :  (12.,  1.50),
    "M12-finer"  :  (12.,  1.25),
    }
    p=params[m.upper()]
    return iso_metric_thread(p[0],p[1])

# whittsworth thread
def thread(args):
    verts=[]
    faces=[]

    if args.thread_preset[0].upper().startswith("M"):
        print("ISO metric thread")
        v_profile_2d, thread_pitch = iso_metric_thread_m(args.thread_preset[0])
    else:
        print("Whitworth thread")
        v_profile_2d, thread_pitch = whitworth_thread_shape(args)

    print("Thread pitch: %.8f" % thread_pitch)
    write_verts_xy("vertices.dat", v_profile_2d)

    major_diameter = max(v[1] for v in v_profile_2d)
    revolution_steps = int(pi*major_diameter / args.segment_length)
    rev_angle = 2*pi / revolution_steps
    rev_step_x = thread_pitch / revolution_steps

    """
    if args.thread_length:
        total_steps = int(args.thread_length / rev_step_x)
        num_revolutions=total_steps // revolution_steps
    elif args.num_revolutions:
        num_revolutions = args.num_revolutions
        total_steps = num_revolutions * revolution_steps
    else:
        num_revolutions = 10
        total_steps = revolution_steps
    """
    total_steps = int(args.thread_length / rev_step_x)
    num_revolutions=total_steps // revolution_steps

    v,f=revolve_solid(v_profile_2d, total_steps, rev_step_x, rev_angle, revolution_steps)

    print("revolutions:", num_revolutions)
    print("steps/revolution:", revolution_steps)

    #print("1st vertex:", v_profile_2d[0]) # x>0
    #print("last vertex:", v_profile_2d[-1]) # x<0
    #print("rev_step_x:", rev_step_x) # >0

    print("total vertices:", len(v))
    print("total facets:", len(f))
    return v,f

def main():
    from argparse import ArgumentParser
    p=ArgumentParser()
    p.add_argument("output", nargs="*")
    # defaults are for 1.25" pipe
    k=1.0
    k=0.3 #test
    p.add_argument("-t", "--thread-preset", nargs=1, type=str, default="whitworth")
    p.add_argument("-d", "--minor-diameter", nargs=1, type=float, default=38.952 * k)
    p.add_argument("-D", "--major-diameter", nargs=1, type=float, default=41.910 * k)
    p.add_argument("-r", "--round-radius-groove", nargs=1, type=float)
    p.add_argument("-R", "--round-radius-tip", nargs=1, type=float)
    p.add_argument("-f", "--flatness-groove", nargs=1, type=float, default=0)
    p.add_argument("-F", "--flatness-tip", nargs=1, type=float, default=0)
    p.add_argument("-p", "--thread-pitch", nargs=1, type=float, default=2.309)
    p.add_argument("-l", "--thread-length", nargs=1, type=float, default=20)
    p.add_argument("-s", "--segment-length", nargs=1, type=float, default=0.05)
    p.add_argument("-n", "--num-revolutions", nargs=1, type=int, help="alternative to --thread-length")
    p.add_argument("-e", "--export", nargs=2, type=str, action="append", help="export as FORMAT to FILE", metavar=("FORMAT","FILE"))
    args = p.parse_args()

    # sadflkjasdf test
    args.round_radius_groove = 0.137329 * args.thread_pitch
    args.round_radius_tip = 0.137329 * args.thread_pitch

    verts,faces = thread(args)

    exporters = {
        "obj":write_obj,
        "off":write_off,
        "stl":write_stl,
        "stlb":write_stl_binary,
    }

    for fn in args.output:
        ext = fn[-3:]
        print("Output to:", fn)
        func=exporters.get(ext, write_obj)
        func(fn, verts, faces)

    for e,fn in args.export:
        if e in exporters:
            print("Output with explicit filetype:", e, fn)
            exporters[e](fn, verts, faces)
        else:
            print("No such exporter:", e)

if __name__ == "__main__":
    main()

