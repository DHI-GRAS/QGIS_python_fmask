from qgis.processing import alg
from argparse import Namespace
import sys
import os.path
import numpy as np

from qgis_fmask.interfaces.fmask_usgsLandsatMakeAnglesImage import mainRoutine


@alg(
    name="landsatmakeanglesimage",
    label=alg.tr("Landsat Make Angles Image"),
    group="fmask",
    group_label=alg.tr("FMask"),
)
@alg.input(
    type=alg.FILE,
    name="mtl",
    label="MTL file",
    behavior=0,
    optional=False,
    fileFilter="tif",
)
@alg.input(
    type=alg.FILE,
    name="templateimg",
    label="Image file name to use as template for output angles image",
    behavior=0,
    optional=False,
    fileFilter="tif",
)
@alg.input(type=alg.FILE_DEST, name="outfile", label="Output angles image file")
def landsatmakeanglesimage(instance, parameters, context, feedback, inputs):
    """landsatmakeanglesimage"""
    mtl = instance.parameterAsString(parameters, "mtl", context)
    templateimg = instance.parameterAsString(parameters, "templateimg", context)
    outfile = instance.parameterAsString(parameters, "outfile", context)

    cmdargs = Namespace(mtl=mtl, templateimg=templateimg, outfile=outfile)

    with np.errstate(invalid="ignore"):
        mainRoutine(cmdargs)
