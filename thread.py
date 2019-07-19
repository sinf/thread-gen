#!/usr/bin/python3
from math import *

def write_obj(filepath, vertices, faces):
    with open(filepath,"w") as f:
        for v in vertices:
            f.write("v %.8f %.8f %.8f\n" % v)
        for face in faces:
            f.write("f")
            for i in face:
                f.write(" %d" % (i+1))
            f.write("\n")

# connect 2 paths (=index arrays) with quads
def quad_strip(idx_a, idx_b):
    faces = []
    idx_a = iter(idx_a)
    idx_b = iter(idx_b)
    a0 = next(idx_a)
    b0 = next(idx_b)
    for a1,b1 in zip(idx_a, idx_b):
        faces += [(a0,b0,a1),(a1,b0,b1)]
        a0 = a1
        b0 = b1
    return faces

def make_arc(ox, oy, radius, angle_start, angle_delta, seglen):
    num_segs = int(abs(radius*angle_delta/seglen))
    num_segs += (num_segs%2) # force even number of vertices
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

def translated(verts, off_x, c, s):
    result = []
    for x,y,z in verts:
        xx = x + off_x
        yy = c*y - s*z
        zz = s*y + c*z
        result += [(xx,yy,zz)]
    return result

def revolve(shape, num_steps, step_x, step_angle):
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

def thread(args):
    verts=[]
    faces=[]

    base_triangle_height = args.major_diameter - args.minor_diameter
    base_triangle_width = args.thread_pitch
    alpha = atan(2*base_triangle_height / base_triangle_width)
    gamma = pi/2 - alpha

    tip_circle_pos = args.round_radius_tip / sin(alpha)
    tip_arc_angle = 2*alpha #2*(pi/2 - gamma)
    tip_arc_length = tip_arc_angle * args.round_radius_tip
    v_tip = make_arc(
        0,
        args.minor_diameter + base_triangle_height - args.round_radius_tip,
        args.round_radius_tip,
        pi/2 - tip_arc_angle*0.5,
        tip_arc_angle,
        args.segment_length)

    groove_circle_pos = args.round_radius_groove / sin(alpha)
    groove_arc_angle = tip_arc_angle
    groove_arc_length = groove_arc_angle * args.round_radius_groove
    v_groove = make_arc(
        -base_triangle_width*0.5,
        args.minor_diameter + args.round_radius_groove,
        args.round_radius_groove,
        -(pi/2 - groove_arc_angle*0.5),
        -groove_arc_angle,
        args.segment_length)

    v_groove_l = v_groove[:len(v_groove)//2]
    v_groove_r = [(v[0]+base_triangle_width,v[1],v[2]) for v in v_groove[len(v_groove)//2:]]
    v_profile_2d = v_groove_r + v_tip + v_groove_l

    revolution_steps = int(pi*args.major_diameter / args.segment_length)
    rev_angle = 2*pi / revolution_steps
    rev_step_x = base_triangle_width / revolution_steps
    total_steps = int(args.thread_length / rev_step_x)

    #temp = make_arc(0,0,1,10,0,pi/2/10);
    #temp = v_profile_2d
    #return temp,[(i-1,i) for i in range(1,len(temp))]

    num_revolutions=total_steps // revolution_steps
    rev_vertex_count=revolution_steps * len(v_profile_2d)

    num_revolutions = 2
    total_steps = num_revolutions * revolution_steps

    v,f=revolve(v_profile_2d, total_steps, rev_step_x, rev_angle)

    print("revolutions:", num_revolutions)
    print("2d profile:", len(v_profile_2d), "verts")
    print("verts/revolution:", rev_vertex_count)
    print("steps/revolution:", revolution_steps)

    skip = len(v_profile_2d)
    n = rev_vertex_count
    i0 = 0
    i1 = n - skip + 1
    f += quad_strip(
            range(i0, i0+n, skip),
            range(i1, i1+n, skip))

    print("total vertices:", len(v))
    print("total facets:", len(f))
    
    return v,f

def main():
    from argparse import ArgumentParser
    p=ArgumentParser()
    p.add_argument("output")
    # defaults are for 1.25" pipe
    k=0.3
    p.add_argument("-d", "--minor-diameter", nargs=1, type=float, default=38.952 * k)
    p.add_argument("-D", "--major-diameter", nargs=1, type=float, default=41.910 * k)
    p.add_argument("-r", "--round-radius-groove", nargs=1, type=float)
    p.add_argument("-R", "--round-radius-tip", nargs=1, type=float)
    p.add_argument("-f", "--flatness-groove", nargs=1, type=float, default=0)
    p.add_argument("-F", "--flatness-tip", nargs=1, type=float, default=0)
    p.add_argument("-p", "--thread-pitch", nargs=1, type=float, default=2.309)
    p.add_argument("-l", "--thread-length", nargs=1, type=float, default=20)
    p.add_argument("-s", "--segment-length", nargs=1, type=float, default=0.1)
    args = p.parse_args()

    # sadflkjasdf
    args.round_radius_groove = 0.137329 * args.thread_pitch
    args.round_radius_tip = 0.137329 * args.thread_pitch

    verts,faces = thread(args)
    write_obj(args.output, verts, faces)

if __name__ == "__main__":
    main()
