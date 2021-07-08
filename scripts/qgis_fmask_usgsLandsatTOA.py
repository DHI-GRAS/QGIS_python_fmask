from argparse import Namespace
import os.path
import shutil
import tempfile

import numpy as np
from processing.tools import dataobjects
from qgis.processing import alg

from qgis_fmask.stacks.landsat_stack import create_landsat_stack
from qgis_fmask.interfaces.fmask_usgsLandsatTOA import mainRoutine
from qgis_fmask.interfaces.fmask_usgsLandsatMakeAnglesImage import (
    mainRoutine as mainRoutine_angles,
)
from qgis_fmask.interfaces.redirect_stdout import redirect_stdout_to_feedback
from qgis_fmask.interfaces.landsatmeta import find_mtl_in_product_dir


@alg(
    name="landsattopofatmosphere",
    label=alg.tr("FMask Landsat - Top Of Atmosphere"),
    group="fmask",
    group_label=alg.tr("Not Updated"),
)
@alg.input(
    type=alg.FILE,
    name="productdir",
    label="Directory of Landsat product",
    behavior=1,
    optional=False,
)
@alg.input(
    type=alg.ENUM,
    name="landsatkeynr",
    label="Landsat sensor",
    options=["Landsat 4&5", "Landsat 7", "Landsat 8"],
    default=2,
)
@alg.input(
    type=alg.FILE_DEST,
    name="anglesfile",
    label="Angles file. If not existing, it will be created in this location.",
)
@alg.input(type=alg.FILE_DEST, name="output", label="Output cloud mask")
@redirect_stdout_to_feedback
def landsattopofatmosphere(instance, parameters, context, feedback, inputs):
    """landsattopofatmosphere"""
    productdir = instance.parameterAsString(parameters, "productdir", context)
    landsatkeynr = instance.parameterAsInt(parameters, "landsatkeynr", context)
    anglesfile = instance.parameterAsString(parameters, "anglesfile", context)
    outfile = instance.parameterAsString(parameters, "output", context)

    landsatkey = ["4&5", "7", "8"][landsatkeynr]

    tempdir = tempfile.mkdtemp()
    try:
        mtl = find_mtl_in_product_dir(productdir)

        # create band stack
        feedback.pushConsoleInfo("Creating band stack ...")
        refimg = os.path.join(tempdir, "ref.vrt")
        create_landsat_stack(
            productdir, outfile=refimg, imagename="ref", landsatkey=landsatkey
        )
        feedback.pushConsoleInfo("Done.")

        # create angles file
        anglesfile = anglesfile or os.path.join(tempdir, "angles.img")
        if not os.path.isfile(anglesfile):
            feedback.pushConsoleInfo("Creating angles file ...")
            with np.errstate(invalid="ignore"):
                mainRoutine_angles(
                    Namespace(mtl=mtl, templateimg=refimg, outfile=anglesfile)
                )
            feedback.pushConsoleInfo("Done.")

        feedback.pushConsoleInfo("Creating TOA image ...")
        cmdargs = Namespace(
            infile=refimg, mtl=mtl, anglesfile=anglesfile, output=outfile
        )
        with np.errstate(invalid="ignore"):
            mainRoutine(cmdargs)
        feedback.pushConsoleInfo("Done.")

    finally:
        try:
            shutil.rmtree(tempdir)
        except OSError:
            pass

    dataobjects.load(outfile, os.path.basename(outfile))
