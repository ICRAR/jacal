import os
import io
import math

from astropy.io import fits
from shutil import copyfile


def image_size_and_num_channels(fits_file):
    header = fits.getheader(fits_file, 0)
    if header['NAXIS'] > 3:
        raise Exception('Invalid number of axis')
    if header['CTYPE3'] != 'FREQ':
        raise Exception('3rd axis is not FREQ')

    image_size = int(header['NAXIS1'] * header['NAXIS2'] * math.fabs(header['BITPIX'])/8)
    return image_size, int(header['NAXIS3'])


def header_size_obj(fits_input_obj):
    num_bytes = 0
    row_size = 80

    while True:
        row = fits_input_obj.read(row_size).decode('ascii')
        num_bytes += row_size
        if 'END' in row.upper():
            break

    while fits_input_obj.tell() % 2880 != 0:
        fits_input_obj.read(row_size)
        num_bytes += row_size

    return num_bytes


def modify_header(fits_file, key, value):
    if isinstance(value, str):
        val = "'{0}'".format(str(value))
        entry = "{0}  = {1}".format(key, val)
    else:
        val = value
        white_space = [' ']*(21 - len(str(val)))
        entry = "{0}  ={1}{2}".format(key, ''.join(white_space), value)

    row_bytes = bytes(entry.encode('ascii')) + bytes([0x20]*(80-len(entry)))
    read_bytes = 0

    with open(fits_file, 'rb+') as fits_input_obj:
        while True:
            row = fits_input_obj.read(80).decode('ascii')

            if 'END' in row.upper():
                break

            if row.startswith(key):
                fits_input_obj.seek(read_bytes)
                fits_input_obj.write(row_bytes)
                break

            read_bytes += 80


def header_size(fits_file):
    with open(fits_file, 'rb') as fits_input_obj:
        return header_size_obj(fits_input_obj)


def concat_images(fits_cube_output, fits_image_input):
    input_iter = iter(fits_image_input)

    if not os.path.exists(fits_cube_output):
        first_input = next(input_iter)
        copyfile(first_input, fits_cube_output)

    hdr_size = header_size(fits_cube_output)
    image_size, num_channels = image_size_and_num_channels(fits_cube_output)

    total_size = hdr_size + (image_size * num_channels)
    total_channels = num_channels

    with open(fits_cube_output, 'rb+') as f:
        f.seek(total_size)

        # loop through input and append images to original cube
        for input_fits in input_iter:
            in_image_size, in_num_channels = image_size_and_num_channels(input_fits)
            total_channels += in_num_channels

            with open(input_fits, 'rb') as inf:
                in_hdr_size = header_size_obj(inf)

                total_to_read = in_image_size * in_num_channels
                total_size += total_to_read

                while total_to_read > 0:
                    buff = inf.read(io.DEFAULT_BUFFER_SIZE)
                    if not buff:
                        raise Exception("Error reading fits")
                    total_to_read -= len(buff)
                    f.write(buff)

        # pad with zeros if cube is not in 2880 increments
        remain = 2880 - (total_size % 2880)
        if remain > 0:
            f.write(bytes([0]*remain))

    # update the total number of freq channels in final image cube
    modify_header(fits_cube_output, 'NAXIS3', total_channels)
