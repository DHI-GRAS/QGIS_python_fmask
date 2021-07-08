from qgis.processing import alg
from processing.core.ProcessingConfig import ProcessingConfig
from argparse import Namespace
import sys
import os.path
import tempfile
import shutil

import numpy as np
from processing.tools import dataobjects

from qgis_fmask.stacks.landsat_stack import create_landsat_stacks
from qgis_fmask.interfaces.fmask_usgsLandsatStacked import mainRoutine
from qgis_fmask.interfaces.fmask_usgsLandsatMakeAnglesImage import (
    mainRoutine as mainRoutine_angles,
)
from qgis_fmask.interfaces.fmask_usgsLandsatSaturationMask import (
    mainRoutine as mainRoutine_saturation,
)
from qgis_fmask.interfaces.fmask_usgsLandsatTOA import mainRoutine as mainRoutine_toa
from qgis_fmask.interfaces.redirect_stdout import redirect_stdout_to_feedback
from qgis_fmask.interfaces.landsatmeta import find_mtl_in_product_dir

# ##OutputFile|output|Output cloud mask|tif #TODO extention should be tif. - implemented without.
# TODO yields different output than the old one.


@alg(
    name="fmasklandsat",
    label=alg.tr("FMask Landsat"),
    group="fmask",
    group_label=alg.tr("FMask"),
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
@alg.input(
    type=alg.FILE_DEST,
    name="saturationfile",
    label="Saturation mask file. If kot existing, it will be created in this location.",
)
@alg.input(
    type=alg.FILE_DEST,
    name="toafile",
    label="TOA file. If not existing, it will be created in this location.",
)
@alg.input(type=alg.FILE_DEST, name="output", label="Output cloud mask")
@alg.input(
    type=int,
    name="mincloudsize",
    label="Mininum cloud size (in pixels) to retain, before any buffering",
    minValue=0,
    maxValue=sys.float_info.max,
    default=0,
)
@alg.input(
    type=int,
    name="cloudbufferdistance",
    label="Distance (in metres) to buffer final cloud objects",
    minValue=0,
    default=150,
)
@alg.input(
    type=int,
    name="shadowbufferdistance",
    label="Distance (in metres) to buffer final cloud shadow objects",
    minValue=0,
    default=300,
)
@alg.input(
    type=int,
    name="cloudprobthreshold",
    label="Cloud probability threshold (percentage) (Eqn 17)",
    minValue=0,
    maxValue=100,
    default=20,
)
@alg.input(
    type=float,
    name="nirsnowthreshold",
    label="Threshold for NIR reflectance for snow detection (Eqn 20). Increase this to reduce snow commission errors",
    minValue=0,
    maxValue=1,
    default=0.11,
    advanced=True,
)
@alg.input(
    type=float,
    name="greensnowthreshold",
    label="Threshold for Green reflectance for snow detection (Eqn 20). Increase this to reduce snow commission errors",
    minValue=0,
    maxValue=1,
    default=0.1,
    advanced=True,
)
@redirect_stdout_to_feedback
def fmasklandsat(instance, parameters, context, feedback, inputs):
    """fmasklandsat"""

    productdir = instance.parameterAsString(parameters, "productdir", context)
    landsatkeynr = instance.parameterAsInt(parameters, "landsatkeynr", context)
    anglesfile = instance.parameterAsString(parameters, "anglesfile", context)
    saturationfile = instance.parameterAsString(parameters, "saturationfile", context)
    toafile = instance.parameterAsString(parameters, "toafile", context)
    output = instance.parameterAsString(parameters, "output", context)
    mincloudsize = instance.parameterAsInt(parameters, "mincloudsize", context)
    cloudbufferdistance = instance.parameterAsInt(
        parameters, "cloudbufferdistance", context
    )
    shadowbufferdistance = instance.parameterAsInt(
        parameters, "shadowbufferdistance", context
    )
    cloudprobthreshold = instance.parameterAsInt(
        parameters, "cloudprobthreshold", context
    )
    nirsnowthreshold = instance.parameterAsDouble(
        parameters, "nirsnowthreshold", context
    )
    greensnowthreshold = instance.parameterAsDouble(
        parameters, "greensnowthreshold", context
    )

    landsatkey = ["4&5", "7", "8"][landsatkeynr]
    tempdir = tempfile.mkdtemp()

    try:
        mtl = find_mtl_in_product_dir(productdir)

        # create band stacks
        feedback.pushConsoleInfo("Creating band stacks ...")
        outfile_template = os.path.join(tempdir, "temp_{imagename}.vrt")
        vrtfiles = create_landsat_stacks(
            productdir, outfile_template=outfile_template, landsatkey=landsatkey
        )
        feedback.pushConsoleInfo("Done.")

        # create angles file
        anglesfile = anglesfile or os.path.join(tempdir, "angles.img")
        if not os.path.isfile(anglesfile):
            feedback.pushConsoleInfo("Creating angles file ...")
            with np.errstate(invalid="ignore"):
                mainRoutine_angles(
                    Namespace(mtl=mtl, templateimg=vrtfiles["ref"], outfile=anglesfile)
                )
            feedback.pushConsoleInfo("Done.")

        # create saturation file
        saturationfile = saturationfile or os.path.join(tempdir, "saturation.img")
        if not os.path.isfile(saturationfile):
            feedback.pushConsoleInfo("Creating saturation mask file ...")
            mainRoutine_saturation(
                Namespace(infile=vrtfiles["ref"], mtl=mtl, output=saturationfile)
            )
            feedback.pushConsoleInfo("Done.")

        # create TOA file
        toafile = toafile or os.path.join(tempdir, "toa.img")
        if not os.path.isfile(toafile):
            feedback.pushConsoleInfo("Creating TOA file ...")
            mainRoutine_toa(
                Namespace(
                    infile=vrtfiles["ref"],
                    mtl=mtl,
                    anglesfile=anglesfile,
                    output=toafile,
                )
            )
            feedback.pushConsoleInfo("Done.")

        cmdargs = Namespace(
            toa=toafile,
            thermal=vrtfiles["thermal"],
            anglesfile=anglesfile,
            saturation=saturationfile,
            mtl=mtl,
            verbose=True,
            keepintermediates=False,
            tempdir=tempdir,
            output=output,
            mincloudsize=mincloudsize,
            cloudbufferdistance=cloudbufferdistance,
            shadowbufferdistance=shadowbufferdistance,
            cloudprobthreshold=cloudprobthreshold,
            nirsnowthreshold=nirsnowthreshold,
            greensnowthreshold=greensnowthreshold,
        )

        feedback.pushConsoleInfo("Running FMask (this may take a while) ...")
        mainRoutine(cmdargs)
        feedback.pushConsoleInfo("Done.")
    finally:
        try:
            shutil.rmtree(tempdir)
        except OSError:
            pass

    dataobjects.load(output, os.path.basename(output))
