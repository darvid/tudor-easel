"""
    easel.converters.xresource
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Convert a palette to and from an XResources file.

    :copyright: Copyright 2011 David Gidwani.
    :license: BSD style, see LICENSE
"""
from easel.converters import IConverter, ConverterError

from commons.core.stringutils import render_template
from commons.core.graphics.color import Color
from commons.core.structures.dict import find_key, find_key_with_parents
from commons.os.xlib.xresources import SimpleResourceCollection


class XResourceConverter(IConverter):

    def __init__(self, *args, **kwargs):
        super(XResourceConverter, self).__init__(*args, **kwargs)
        self.rc = None

    def read(self, filename):
        self.rc = SimpleResourceCollection(filename)
        colors = map(lambda i: find_key("color" + str(i), self.rc.db),
            range(16))
        if not any(colors):
            raise ConverterError("xrdb does not contain any color info")
        for index, color in enumerate(colors):
            self._palette.set_color(Color.from_string(color), index)
        return self._palette

    def write(self, template_filename=None, filename=None):
        if not self.rc: return
        for index, color in enumerate(self._palette):
            parents = find_key_with_parents("color" + str(index), self.rc.db)
            setattr(reduce(lambda a, b: a[b],
                [self.rc.db[parents[0]]] + parents[1:-1]), parents[-1],
                str(self._palette[index]))
        modified, filenames = self.rc.modified
        if template_filename:
            return render_template(template_filename, filename,
                numbered_data=self._palette.colors)
        else:
            if filename:
                if (filename.lower().endswith("xdefaults") or
                    filename.lower().endswith("xresources") and
                    filename != filenames[0][0]):
                    filename = None
                return self.rc.save(filenames[0][0], filename)
            map(self.rc.save, filenames)

XResourceConverter.METADATA.update({
    "author": "builtin",
    "description": __doc__.split("\n")[4].strip(),
    "file_filters": [
        ("XResources/XDefaults", {
            "patterns": ["*"]
        })
    ],
    "requires_template": False
})
