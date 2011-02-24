"""
    easel.converters
    ~~~~~~~~~~~~~~~~

    Import and export palettes from and to various file formats.

    :copyright: Copyright 2011 David Gidwani.
    :license: BSD style, see LICENSE
"""
__import__("pkg_resources").declare_namespace(__name__)

import abc
import pkgutil

from commons.core.graphics.color import NumberedPalette


__all__ = ["ConverterError", "IConverter"]


class ConverterError(Exception):
    pass


class IConverter(object):
    """Modular converter interface."""

    __metaclass__ = abc.ABCMeta
    METADATA = {
        "author": "Anonymous",
        "license": "New BSD",
        "description": "",
        "version": "0.0.1",
        "file_filters": [
            ("", {
                "patterns": [],
                "mime_types": []
            })
        ],
        "requires_template": True
    }

    def __init__(self, palette_obj=NumberedPalette(16)):
        self._palette = palette_obj
        assert (len(self.METADATA["file_filters"]) and
                len(self.METADATA["file_filters"][0]) == 2 and
                any(self.METADATA["file_filters"][0][1].values())), \
                "Converter metadata must contain valid file filter(s)"

    def update_palette(self, palette):
        self._palette.colors = palette.colors

    @abc.abstractmethod
    def read(self, filename):
        """Populate a palette from a given file.

        :rtype: :class:`commons.core.graphics.color.NumberedPalette`.
        :return: The internal palette (an instance of the class passed to the
                 *palette_class* parameter in the constructor).
        """
        self._data = open(filename, "r").read()

    @abc.abstractmethod
    def write(self, template_filename=None, filename=None):
        """Export a palette to a given file.

        :param template_filename: Absolute path to a template file.
        :param filename: Absolute path to destination file.

        :rtype: `str` or `None`.
        :return: If *filename* is not specified, returns a string of the
                 exported data.
        """
        return NotImplemented

    def __repr__(self):
        return "<{0}({1})>".format(self.__class__.__name__,
            self.METADATA["file_filters"][0][1].values()[0])
