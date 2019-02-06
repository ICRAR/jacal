from astropy.io import fits


def open_fits(fits_image_input):
    for i in fits_image_input:
        yield fits.open(i)


def create_multi_fits_extension_cube(fits_image_input, fits_cube_output):
    image_list = fits.HDUList()

    for hdu_list in open_fits(fits_image_input):
        image = fits.ImageHDU(data=hdu_list[0].data, header=hdu_list[0].header)
        image_list.append(image)

    image_list.writeto(fits_cube_output, overwrite=True)

