import logging
import numpy

class VisibilityCube:
    def __init__(self, number_of_rows, number_of_channels, number_of_polarisations):
        logging.debug("Initializing...")

        self._number_of_rows = number_of_rows
        self._number_of_channels = number_of_channels
        self._number_of_polarisations = number_of_polarisations

        self._cube = numpy.zeros((number_of_rows, number_of_channels, number_of_polarisations), dtype=complex)







    def serialize(chunk):
        return None

    @staticmethod
    def deserialize(serialized):
        return None

    def __str__(self):
        return None

