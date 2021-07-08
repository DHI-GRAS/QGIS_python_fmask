from qgis.processing import alg
from argparse import Namespace
import sys
import os.path
import numpy as np
from qgis_fmask.interfaces.fmask_sentinel2makeAnglesImage import mainRoutine


@alg(
    name="sentinel2makeanglesimage",
    label=alg.tr("Sentinel 2 Make Angles Image"),
    group="fmask",
    group_label=alg.tr("FMask"),
)
@alg.input(
    type=alg.FILE,
    name="infile",
    label="Input sentinel-2 tile metafile",
    behavior=1,
    optional=False,
)
@alg.input(type=alg.FILE_DEST, name="outfile", label="Output angles image file")
def fmasklandsat(instance, parameters, context, feedback, inputs):
    """fmasklandsat"""

    infile = instance.parameterAsString(parameters, "infile", context)
    outfile = instance.parameterAsInt(parameters, "outfile", context)
    cmdargs = Namespace(infile=infile, outfile=outfile)

    with np.errstate(invalid="ignore"):
        mainRoutine(cmdargs)
