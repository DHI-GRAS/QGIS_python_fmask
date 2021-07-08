from qgis.processing import alg
from argparse import Namespace
import sys
import os.path
import numpy as np

from qgis_fmask.interfaces.fmask_usgsLandsatSaturationMask import mainRoutine


@alg(
    name="landsatsaturationmask",
    label=alg.tr("Landsat Saturation Mask"),
    group="fmask",
    group_label=alg.tr("FMask"),
)
@alg.input(
    type=alg.FILE,
    name="infile",
    label="Input raw DN radiance image",
    behavior=0,
    optional=False,
)
@alg.input(
    type=alg.FILE,
    name="mtl",
    label="MTL file",
    behavior=0,
    optional=False,
    fileFilter="txt",
)
@alg.input(
    type=alg.FILE,
    name="anglesfile",
    label="Input angles file containing satellite and sun azimuth and zenith",
    behavior=0,
    optional=True,
)
@alg.input(type=alg.FILE_DEST, name="outfile", label="Output angles image file")
def landsatsaturationmask(instance, parameters, context, feedback, inputs):
    """landsatsaturationmask"""
    infile = instance.parameterAsString(parameters, "infile", context)
    mtl = instance.parameterAsString(parameters, "mtl", context)
    anglesfile = instance.parameterAsString(parameters, "anglesfile", context)
    outfile = instance.parameterAsString(parameters, "outfile", context)

    cmdargs = Namespace(infile=infile, mtl=mtl, outfile=outfile)

    with np.errstate(invalid="ignore"):
        mainRoutine(cmdargs)
