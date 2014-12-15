
import datetime
import resource
import numpy as np

#import numm3 as numm
import numm


########################################
# https://github.com/dentearl/simpleHilbertCurve
# These functions refactored from those available at 
# wikipedia for Hilbert curves http://en.wikipedia.org/wiki/Hilbert_curve
def d2xy(n, d):
    """
    take a d value in [0, n**2 - 1] and map it to
    an x, y value (e.g. c, r).
    """
    assert(d <= n**2 - 1)
    t = d
    x = y = 0
    s = 1
    while (s < n):
        rx = 1 & (t / 2)
        ry = 1 & (t ^ rx)
        x, y = rot(s, x, y, rx, ry)
        x += s * rx
        y += s * ry
        t /= 4
        s *= 2
    return x, y

def xy2d(n, x, y):
    """
    take an x,y pair (what range?) and map it to a single point
    on [0, n**2 - 1]
    """
    d = 0
    s = n/2
    while (s > 0):
        rx = (x & s) > 0
        ry = (y & s) > 0
        d += s * s * ((3 * rx) ^ ry)
        x, y = rot(s, x, y, rx, ry)
        s /= 2
    assert(d <= n**2 - 1)
    return d

def rot(n, x, y, rx, ry):
    """
    rotate/flip a quadrant appropriately
    """
    if ry == 0:
        if rx == 1:
            x = n - 1 - x
            y = n - 1 - y
        return y, x
    return x, y
############################################3

def current_ram_usage():
    """Returns current megabytes of ram this process is using"""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage[2]*resource.getpagesize()/1000000.0

# image dimensions
OUTPUTW_POW = 11
OUTPUTW = 2**OUTPUTW_POW
GRIDS = 2**5
THUMBW = int(1.0*OUTPUTW/GRIDS)

OUTPUT_FRAMES = 500

global v
global i

print('v' in globals())

if not ('v' in dir()) and not ('v' in globals()):
    # we haven't loaded video yet
    print("Loading... (%d MB used)" % current_ram_usage())
    start = datetime.datetime.now()
    v = numm.video2np('johnny_64.avi', height=48)
    print("Done: got %d frames, took %d seconds, %d MB of RAM in use" %
        (len(v), (datetime.datetime.now() - start).total_seconds(), current_ram_usage()))

# calculate height and thumbnail sizes
OUTPUT_RATIO = 1. * len(v[0])/len(v[0][0])
OUTPUTH = int(OUTPUTW * OUTPUT_RATIO)
THUMBH = int(1.0*OUTPUTH/GRIDS)
DSCALE = GRIDS * 1.0 / len(v)
SCALE = 1.0 * len(v[0][0]) / THUMBW

# HACK
print (THUMBW, THUMBH, SCALE)
assert(THUMBW == 64)
assert(THUMBH == 48)
assert(SCALE == 1.0)

vo = np.zeros(shape=(OUTPUT_FRAMES, OUTPUTH, OUTPUTW, 3), dtype=np.uint8)

def percent2xy(percent):
    x, y = d2xy(OUTPUTW, int(percent * (OUTPUTW**2 -1)))
    return x, int(y * OUTPUT_RATIO)

def make_thumb(frame_num):
    "very naive re-size to thumb"
    global v
    frame_num = int(frame_num) % len(v)
    t = np.zeros(shape=(THUMBH, THUMBW, 3), dtype=np.uint8)
    f = v[frame_num]
    for y in range(THUMBH):
        for x in range(THUMBW):
            t[y][x] = f[y*SCALE][x*SCALE]
    return t

def insert(frame, thumb, percent):
    "This function copies a thumbnail from frame to a cell in the output image"
    global v
    global vo
    x, y = percent2xy(percent)
    x -= x % THUMBW
    y -= y % THUMBH
    for row in range(THUMBH):
        vo[frame][y+row][x:x+THUMBW] = thumb[row][:]

for frame in range(OUTPUT_FRAMES):
    print("frame: %d/%d" % (frame, OUTPUT_FRAMES))
    for d in range(GRIDS**2):
        percent = 1.0 * d/(GRIDS**2)
        #print(percent)
        #insert(frame, make_thumb(percent * len(v) + frame), percent)
        insert(frame, v[(percent * len(v) + frame) % len(v)], percent)

for fnum in range(len(v)-1):
    print("frame: %d/%d" % (fnum, len(v)-1))
    numm.np2image(vo[fnum], "frames/%d.png" % fnum)

#numm.np2video(vo, 'hilbert_johny_out.mkv')
#numm.np2image(vo[3], 'hilbert_johny_out.png')
#numm.np2image(i, 'hilbert_johny_out.png')

"""
ffmpeg -framerate 30 -i frames/%d.png -r 30 -pix_fmt yuv420p out.mp4
"""
