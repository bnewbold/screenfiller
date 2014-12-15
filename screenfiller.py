#!/usr/bin/env python
"""
..
    Copyright: Sigh
    License: Indeterminate
    Author: All of Us
    Date: Just Now

Screen filler!

I need numm3 (branch): http://readmes.numm.org/numm/
"""

from __future__ import absolute_import, division, print_function
import sys
import argparse
import logging as log
import datetime
import resource
import math
import os
import shutil
import tempfile
import numpy as np

# can't import numm here b/c it clobbers argparse?
#import numm

from curves import *

raw = None

def current_ram_usage():
    """Returns current megabytes of ram this process is using"""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage[2]*resource.getpagesize()/1e6

def insert_thumb(thumb, x, y, output_index, video_out):
    "This function copies a thumbnail from frame to a cell in the output image"
    height = len(thumb)
    width = len(thumb[0])
    for row in range(height):
        video_out[output_index][y+row][x:x+width] = thumb[row][:]

def load_video(args):
    import numm
    # we haven't loaded video yet
    print("Loading %s... (%d MB used)" % (args.inputvideofile, current_ram_usage()))
    start = datetime.datetime.now()
    v = numm.video2np(args.inputvideofile, height=args.height)
    print("Done: got %d frames, took %d seconds, %d MB of RAM in use" %
        (len(v), (datetime.datetime.now() - start).total_seconds(), current_ram_usage()))
    return v

def fill_frames(args, start=0):

    global raw

    if raw is None:
        raw = load_video(args)

    if args.frame_limit:
        output_frames = min(args.frame_limit, len(raw) - start)
    else:
        output_frames = len(raw) - start

    thumb_height = args.height
    thumb_width = len(raw[0][0])
    output_height = thumb_height * args.grid_edge
    output_width = thumb_width * args.grid_edge
    output_ratio = 1.0 * output_height / output_width

    vo = np.zeros(shape=(output_frames, output_height, output_width, 3), dtype=np.uint8)

    if args.hilbert:
        d2xy = d2xy_hilbert
    else:
        d2xy = d2xy_moore

    def percent2xy(percent):
        x, y = d2xy(output_width, int(percent * (output_width**2 -1)))
        return x, int(y * output_ratio)

    print()
    print("Processing video frames:")
    for frame in range(start, start+output_frames):
        sys.stdout.write("\b" * 50)
        sys.stdout.write("processing frame: %d/%d" % (frame, output_frames-1))
        for d in range(args.grid_edge**2):
            percent = 1.0 * d/(args.grid_edge**2)
            x, y = percent2xy(percent)
            x -= x % thumb_width
            y -= y % thumb_height
            insert_thumb(raw[(percent * len(raw) + frame) % len(raw)],
                   x, y, frame-start, vo)

    print()
    return vo

def do_video(args):
    
    import numm

    if args.output:
        output_fname = args.output
    else:
        output_fname = "%s_filled.mp4" % args.inputvideofile

    if args.np2video:
        frames = fill_frames(args)
        print("Now running numm.np2video to create video file (could be huge)")
        numm.np2video(frames, output_fname)
        return

    work_dir = tempfile.mkdtemp(suffix="_screenfiller_frames")

    print("Saving frames as .png files in batches of 100")

    global raw
    raw = load_video(args)

    if args.frame_limit:
        args.output_frames = args.frame_limit
    else:
        args.output_frames = len(raw)

    for coarse in range(0, args.output_frames, 100):
        args.frame_limit = 100
        frames = fill_frames(args, start=coarse)
        for fnum in range(coarse, coarse+len(frames)):
            sys.stdout.write("\b" * 50)
            sys.stdout.write("saving frame: %d/%d" % (fnum, args.output_frames-1))
            numm.np2image(frames[fnum-coarse], "%s/%d.png" % (work_dir, fnum))

    print()
    print("Now running ffmpeg to create video file")
    os.system("ffmpeg -framerate 30 -i %s/%%d.png -r 30 -pix_fmt yuv420p -y %s" % (work_dir, output_fname))

    print("Cleaning up...")
    shutil.rmtree(work_dir)
    

def do_image(args):
    print("Doing just the one frame, saved as an image")
    import numm
    # do_video with just one frame and save that
    args.frame_limit = 1
    frames = fill_frames(args)
    image = frames[0]
    numm.np2image(image, args.inputvideofile + ".png")

def main():
    parser = argparse.ArgumentParser(
        description="filler of pixels",
        usage="%(prog)s <inputvideofile> [args] <command>")
    parser.add_argument("-v", "--verbose",
        action="count",
        help="Show more debugging statements")
    parser.add_argument('inputvideofile',
        type=str,
        help="input video to work with")
    parser.add_argument('-o', '--output',
        type=str,
        help="output file name")
    parser.add_argument('--height',
        type=int,
        default=48,
        help="thumb height. output height will be this times grid-edge")
    parser.add_argument('-g', '--grid-edge',
        type=int,
        default=8,
        help="number of frames on a grid. must be power of 2.")
    parser.add_argument('--frame-limit',
        type=int,
        help="only output this number of frames")
    parser.add_argument('--video',
        action='store_true',
        help="output animated video")
    parser.add_argument('--image',
        action='store_true',
        help="output a single image frame")
    parser.add_argument('--hilbert',
        action='store_true',
        help="use a hilbert curve")
    parser.add_argument('--moore',
        action='store_true',
        help="use a moore curve (default)")
    parser.add_argument('--np2video',
        action='store_true',
        help="try to use np2video instead of ffmpeg for video creation")

    args = parser.parse_args()

    if args.grid_edge is not None:
        log2 = math.log(args.grid_edge)/math.log(2)
        if int(log2) != log2:
            parser.error("grid not a power of two! %d" % args.grid)

    if args.verbose > 0:
        log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)
    else:
        log.basicConfig(format="%(levelname)s: %(message)s")

    # ensure we can import before running; can't do it at top b/c it clobbers
    # argparse
    import numm

    if (not args.image) and (not args.video):
        args.error("Must make video or image output!")

    if not args.hilbert:
        # default to moore curve
        args.moore = True

    if args.image:
        do_image(args)
    if args.video:
        do_video(args)
    print("Done!")

if __name__ == '__main__':
    main()
