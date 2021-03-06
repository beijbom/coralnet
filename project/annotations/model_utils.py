# Utility methods used by models.py.
#
# These methods should not import anything from models.py.  Otherwise,
# there will be circular import dependencies.  Utility functions
# that use models.py should go in the general utility functions
# file, utils.py.
from __future__ import division
from decimal import Decimal
import math


class AnnotationAreaUtils():

    # Percentages are decimals.
    # Pixels are integers.
    # Database (db) format:
    #     percentages - "5.7;94.5;10;90"
    #     pixels - "125,1880,80,1600"

    IMPORTED_STR = 'imported'
    IMPORTED_DISPLAY = "(Imported points; not specified)"
    TYPE_PERCENTAGES = 'percentages'
    TYPE_PIXELS = 'pixels'
    TYPE_IMPORTED = 'imported'

    @staticmethod
    def percentages_to_db_format(min_x, max_x, min_y, max_y):
        return ';'.join([
            str(min_x), str(max_x), str(min_y), str(max_y)
        ])

    @staticmethod
    def pixels_to_db_format(min_x, max_x, min_y, max_y):
        return ','.join([
            str(min_x), str(max_x), str(min_y), str(max_y)
        ])

    @staticmethod
    def db_format_to_numbers(s):
        d = dict()
        if s == AnnotationAreaUtils.IMPORTED_STR:
            d['type'] = AnnotationAreaUtils.TYPE_IMPORTED
        elif s.find(';') != -1:
            # percentages
            d['min_x'], d['max_x'], d['min_y'], d['max_y'] = [Decimal(dec_str) for dec_str in s.split(';')]
            d['type'] = AnnotationAreaUtils.TYPE_PERCENTAGES
        elif s.find(',') != -1:
            # pixels
            d['min_x'], d['max_x'], d['min_y'], d['max_y'] = [int(int_str) for int_str in s.split(',')]
            d['type'] = AnnotationAreaUtils.TYPE_PIXELS
        else:
            raise ValueError("Annotation area isn't in a valid DB format.")
        return d

    @staticmethod
    def db_format_to_percentages(s):
        d = AnnotationAreaUtils.db_format_to_numbers(s)
        if d['type'] == AnnotationAreaUtils.TYPE_PERCENTAGES:
            return d
        else:
            raise ValueError("Annotation area type is '{0}' expected {1}.".format(
                d['type'], AnnotationAreaUtils.TYPE_PERCENTAGES))

    @staticmethod
    def db_format_to_display(s):
        d = AnnotationAreaUtils.db_format_to_numbers(s)

        if d['type'] == AnnotationAreaUtils.TYPE_IMPORTED:
            return AnnotationAreaUtils.IMPORTED_DISPLAY
        elif d['type'] == AnnotationAreaUtils.TYPE_PERCENTAGES:
            return "X: {0} - {1}% / Y: {2} - {3}%".format(
                d['min_x'], d['max_x'], d['min_y'], d['max_y']
            )
        elif d['type'] == AnnotationAreaUtils.TYPE_PIXELS:
            return "X: {0} - {1} pixels / Y: {2} - {3} pixels".format(
                d['min_x'], d['max_x'], d['min_y'], d['max_y']
            )

    @staticmethod
    def percentages_to_pixels(min_x, max_x, min_y, max_y, width, height):
        d = dict()

        # The min/max x/y percentage arguments are Decimals.

        # Convert to Decimal pixel values ranging from 0 to the width/height.
        # (Decimal / int) * int -> Decimal * int -> Decimal.
        d['min_x'] = (min_x / 100) * width
        d['max_x'] = (max_x / 100) * width
        d['min_y'] = (min_y / 100) * height
        d['max_y'] = (max_y / 100) * height

        for key in d.keys():
            # Convert the Decimal pixel values to integers.

            # At this point our values range from 0.0 to width/height.
            # Round up, then subtract 1.
            d[key] = int(math.ceil(d[key]) - 1)

            # Clamp the -1 edge-value to 0.
            # We thus map 0.000-1.000 to 0, 1.001-2.000 to 1,
            # 2.001-3.000 to 2, etc.
            d[key] = max(d[key], 0)

        return d
