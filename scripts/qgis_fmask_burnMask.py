# TODO yields Error1: PROJ...
from qgis.processing import alg
from processing.core.ProcessingConfig import ProcessingConfig
from db_manager.db_plugins import data_model
from processing.tools import system
from qgis import processing


@alg(
    name="burncloudmask",
    label=alg.tr("Burn cloud mask"),
    group="fmask",
    group_label=alg.tr("FMask"),
)
@alg.input(
    type=alg.RASTER_LAYER,
    name="dataFile",
    label="An image file to burn the cloud mask into",
    optional=False,
)
@alg.input(
    type=alg.RASTER_LAYER,
    name="maskFile",
    label="Could mask from FMask",
    optional=False,
)
@alg.input(
    type=bool,
    name="maskNull",
    label="Mask FMask null pixels",
    default=True,
    advanced=True,
)
@alg.input(
    type=bool,
    name="maskCloud",
    label="Mask FMask cloud pixels",
    default=True,
    advanced=True,
)
@alg.input(
    type=bool,
    name="maskShadow",
    label="Mask FMask shadow pixels",
    default=True,
    advanced=True,
)
@alg.input(
    type=bool,
    name="maskSnow",
    label="Mask FMask snow pixels",
    default=True,
    advanced=True,
)
@alg.input(
    type=bool,
    name="maskWater",
    label="Mask FMask water pixels",
    default=False,
    advanced=True,
)
@alg.input(
    type=bool,
    name="maskLand",
    label="Mask FMask land pixels",
    default=False,
    advanced=True,
)
@alg.input(type=alg.FILE_DEST, name="outputFile", label="Maked output image")
def burncloudmask(instance, parameters, context, feedback, inputs):
    """burncloudmask"""

    dataRaster = instance.parameterAsRasterLayer(parameters, "dataFile", context)
    # Run GDAL warp to make sure that the mask file exactly aligns with the image file

    feedback.setProgressText("Aligning mask raster to image raster...")
    # feedback.setProgressText(str(dir(dataRaster)))

    feedback.setProgressText(str(dir(parameters["dataFile"])))
    extent = dataRaster.extent().asWktPolygon()
    proj = dataRaster.crs().toWkt()
    resolution = dataRaster.rasterUnitsPerPixelX()
    bandCount = dataRaster.bandCount()
    warpMask = system.getTempFilename("tif")
    params = {
        "INPUT": parameters["maskFile"],
        "DEST_SRS": proj,
        "TR": resolution,
        "USE_RASTER_EXTENT": True,
        "RASTER_EXTENT": extent,
        "EXTENT_CRS": proj,
        "METHOD": 0,
        "RTYPE": 0,
        "OUTPUT": warpMask,
    }
    processing.run("gdal:warpreproject", params, feedback=feedback, context=context)

    feedback.setProgressText("Applying mask to image...")
    # First reclassify fmask output into two classes
    flags = [
        parameters["maskNull"],
        parameters["maskLand"],
        parameters["maskCloud"],
        parameters["maskShadow"],
        parameters["maskSnow"],
        parameters["maskWater"],
    ]
    maskClass = [str(i) for i in range(len(flags)) if flags[i]]
    leaveClass = [str(i) for i in range(len(flags)) if not flags[i]]
    reclassString = " ".join(maskClass) + " = 0\n" + " ".join(leaveClass) + " = 1"
    reclassMask = system.getTempFilename("tif")
    params = {
        "input": warpMask,
        "txtrules": reclassString,
        "output": reclassMask,
        "GRASS_REGION_PARAMETER": extent,
        "GRASS_REGION_CELLSIZE_PARAMETER": resolution,
    }
    processing.run("grass7:r.reclass", params, feedback=feedback, context=context)

    # Then use OTB band maths on all bands
    params = {
        "il": [
            instance.parameterAsString(parameters, "dataFile", context),
            reclassMask,
        ],
        "exp": "im1*im2b1",
        "out": instance.parameterAsString(parameters, "outputFile", context),
    }
    processing.run("otb:BandMathX", params, feedback=feedback, context=context)
