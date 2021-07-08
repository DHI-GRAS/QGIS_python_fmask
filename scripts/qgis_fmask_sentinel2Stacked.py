from qgis.processing import alg
from argparse import Namespace
import sys
import os.path
import tempfile
import shutil
from processing.tools import dataobjects

from qgis_fmask.stacks.sentinel_stack import create_sentinel_stack
from qgis_fmask.interfaces.fmask_sentinel2Stacked import mainRoutine
from qgis_fmask.interfaces.fmask_sentinel2makeAnglesImage import (
    mainRoutine as mainRoutine_angles,
)
from qgis_fmask.interfaces.redirect_stdout import redirect_stdout_to_feedback
from qgis_fmask.interfaces.s2meta import find_xml_in_granule_dir


@alg(
    name="fmasksentinel2",
    label=alg.tr("FMask Sentinel 2"),
    group="fmask",
    group_label=alg.tr("FMask"),
)
@alg.input(
    type=alg.FILE,
    name="granuledir",
    label="Path to .SAFE or tile/granule directory",
    behavior=1,
    optional=False,
)
@alg.input(
    type=alg.FILE,
    name="anglesfile",
    label="Input angles file containing satellite and sun azimuth and zenith",
    behavior=0,
    optional=True,
    fileFilter="tif",
)
@alg.input(
    type=alg.FILE_DEST, name="output", label="Output cloud mask", fileFilter="tif"
)
@alg.input(type=bool, name="verbose", label="verbose output", default=True)
@alg.input(
    type=int,
    name="mincloudsize",
    label="Mininum cloud size (in pixels) to retain, before any buffering",
    minValue=0,
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
def fmasksentinel2(instance, parameters, context, feedback, inputs):
    """fmasksentinel2"""
    granuledir = instance.parameterAsString(parameters, "granuledir", context)
    anglesfile = instance.parameterAsString(parameters, "anglesfile", context)
    output = instance.parameterAsString(parameters, "output", context)
    verbose = instance.parameterAsBool(parameters, "verbose", context)
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

    tempdir = tempfile.mkdtemp()
    try:
        feedback.pushConsoleInfo("Creating Sentinel 2 band stack VRT file ...")
        tempvrt = os.path.join(tempdir, "temp.vrt")
        create_sentinel_stack(granuledir, outfile=tempvrt)
        feedback.pushConsoleInfo("Done.")

        if not anglesfile:
            feedback.pushConsoleInfo("Creating angles file ...")
            anglesfile = os.path.join(tempdir, "angles.img")
            cmdargs_angles = Namespace(
                infile=find_xml_in_granule_dir(granuledir), outfile=anglesfile
            )
            import numpy as np

            with np.errstate(invalid="ignore"):
                mainRoutine_angles(cmdargs_angles)
            feedback.pushConsoleInfo("Done.")

        cmdargs = Namespace(
            toa=tempvrt,
            anglesfile=anglesfile,
            output=output,
            verbose=verbose,
            tempdir=tempdir,
            keepintermediates=False,
            mincloudsize=mincloudsize,
            cloudbufferdistance=cloudbufferdistance,
            shadowbufferdistance=shadowbufferdistance,
            cloudprobthreshold=cloudprobthreshold,
            nirsnowthreshold=nirsnowthreshold,
            greensnowthreshold=greensnowthreshold,
        )

        feedback.pushConsoleInfo("Running FMask (this may take a while) ...")
        mainRoutine(cmdargs)
    finally:
        try:
            shutil.rmtree(tempdir)
        except OSError:
            pass

    feedback.pushConsoleInfo("Done.")
    dataobjects.load(output, os.path.basename(output))
