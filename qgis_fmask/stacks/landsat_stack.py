import os
import glob

import sys

if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))
import buildvrt as bv


bandfile_patterns = {
    "8": {"ref": "LC*_B[1-7,9].TIF", "thermal": "LC*_B1[0,1].TIF"},
    "4&5": {"ref": "L*_B[1,2,3,4,5,7].TIF", "thermal": "L*_B6.TIF"},
    "7": {"ref": "L*_B[1,2,3,4,5,7].TIF", "thermal": "L*_B6_VCID_?.TIF"},
}


def create_landsat_stack(productdir, outfile, landsatkey, imagename):
    pattern = os.path.join(productdir, bandfile_patterns[landsatkey][imagename])
    infiles = sorted(glob.glob(pattern))
    if not infiles:
        raise RuntimeError("No files found for pattern '{}'.".format(pattern))
    bv.buildvrt(infiles, outfile, separate=True)


def create_landsat_stacks(productdir, outfile_template, landsatkey):
    patterns = bandfile_patterns[landsatkey]
    outfiles = {}
    for imagename in patterns:
        outfile = outfile_template.format(landsatkey=landsatkey, imagename=imagename)
        create_landsat_stack(
            productdir, outfile=outfile, landsatkey=landsatkey, imagename=imagename
        )
        outfiles[imagename] = outfile
    return outfiles
