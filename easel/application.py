"""
    easel.application
    ~~~~~~~~~~~~~~~~~

    A modular, multi-application system color scheme manager.

    :copyright: Copyright 2011 David Gidwani.
    :license: BSD style, see LICENSE
"""
import sys
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

try:
    import gtk
    import gobject
except:
    sys.exit(1)

import os
import pkgutil

from commons.core.structures.dict import AttrDict
from commons.core.graphics.color import HTML4_COLORS, Color, NumberedPalette
from commons.io.fs import path
from pkg_resources import resource_filename

import easel.converters


def gtk_message(parent=None, flags=0, type_=gtk.MESSAGE_INFO,
                buttons=gtk.BUTTONS_OK, message_format=None):
    dialog = gtk.MessageDialog(parent, flags, type_, buttons, message_format)
    result = dialog.run()
    dialog.destroy()
    return result


def gtk_question(message):
    result = gtk_message(type_=gtk.MESSAGE_QUESTION,
        buttons=gtk.BUTTONS_YES_NO, message_format=message)
    return result == gtk.RESPONSE_YES


class Application(object):

    def __init__(self, ui_file, handlers=[]):
        self.shared_data = AttrDict()

        self.builder = gtk.Builder()
        self.builder.add_from_file(resource_filename(__name__, ui_file))
        self.handlers = []
        map(self.add_handler, handlers)
        self.handlers and self.connect_signals()

    def add_handler(self, cls):
        self.handlers.append(cls(self.builder, self.shared_data))

    def connect_signals(self):
        self.builder.connect_signals(self)

    def __getattr__(self, name):
        try:
            return super(Application, self).__getattribute__(name)
        except AttributeError, err:
            for obj in self.handlers:
                if hasattr(obj, name):
                    return getattr(obj, name)
            else:
                raise err


class MainWindow(object):

    config_dir = path(os.environ["XDG_CONFIG_HOME"], "easel")
    config_dir.create(silent=True)

    def __init__(self, builder, shared_data):
        self.shared_data = shared_data
        self.shared_data.config_dir = self.config_dir

        self.builder = builder
        self.window = builder.get_object("main_window")

        self.shared_data.converters = []
        self.converters = self.shared_data.converters

        #: (filename, converter)
        self.shared_data.current_file = ()
        self.current_file = self.shared_data.current_file

        self.unsaved = False

        self.load_converters()
        self.load_file(
            (path("~/.Xdefaults") or path("~/.Xresources")).absolute,
            converter_name="xresource"
        )

    def load_converters(self):
        map(lambda (loader, name, is_pkg):
                __import__("easel.converters." + name),
            pkgutil.walk_packages(easel.converters.__path__))
        map(lambda cls: self.converters.append(cls()),
            easel.converters.IConverter.__subclasses__())

        liststore = self.builder.get_object("converter_liststore")

        for converter in self.converters:
            name = converter.__module__.lstrip("easel.converters.")
            liststore.append([name.capitalize()])

    def load_file(self, filename, converter_filter=None, converter_name=None):
        if converter_name:
            converter = self.get_converter_by_name(converter_name)
        elif converter_filter:
            converter = self.get_converter_by_filter(
                converter_filter.get_name())
        else:
            converter = None

        if not converter:
            return gtk_message(parent=self.window, type_=gtk.MESSAGE_ERROR,
                message_format="No converter found")
        try:
            palette = converter.read(filename)
            assert palette, "Unable to parse file '{0}'".format(filename)
            self.set_palette(palette)
            self.current_file = (filename, converter)
            self._set_unsaved(False)
        except Exception, err:
            return gtk_message(parent=self.window, type_=gtk.MESSAGE_ERROR,
                message_format=str(err))

    def get_converter_by_name(self, name):
        for converter in self.converters:
            if converter.__module__ == "easel.converters." + name:
                return converter

    def get_converter_by_filter(self, filter_name):
        for converter in self.converters:
            for file_filter in converter.METADATA["file_filters"]:
                if file_filter[0] == filter_name:
                    return converter

    def get_palette(self):
        palette = NumberedPalette(16)
        for index in range(16):
            button = self.builder.get_object("colorbutton" + str(index + 1))
            color = button.get_color()
            palette.set_color(Color(*map(
                lambda c: round(c/256),
                (color.red, color.green, color.blue))), index)
        return palette

    def file_select(self, action=gtk.FILE_CHOOSER_ACTION_OPEN,
        initial_path=config_dir, suggested_file=None, associated_entry=None):
        if action == gtk.FILE_CHOOSER_ACTION_OPEN:
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_OPEN, gtk.RESPONSE_OK)
            title = "Open"
        elif action == gtk.FILE_CHOOSER_ACTION_SAVE:
            buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                gtk.STOCK_SAVE, gtk.RESPONSE_OK)
            title = "Save as"
        else:
            raise ValueError("Invalid action")
        chooser = gtk.FileChooserDialog(title=title, action=action,
            buttons=buttons)
        if associated_entry:
            chooser.selection_entry = associated_entry

        for converter in self.converters:
            for name, targets in converter.METADATA["file_filters"]:
                file_filter = gtk.FileFilter()
                file_filter.set_name(name)
                if "patterns" in targets:
                    map(file_filter.add_pattern, targets["patterns"])
                if "mime_types" in targets:
                    map(file_filter.add_mimetype, targets["mime_types"])
                chooser.add_filter(file_filter)

        if suggested_file:
            chooser.set_filename(suggested_file)
        chooser.set_current_folder(initial_path.absolute)

        result = file_filter = None
        if chooser.run() == gtk.RESPONSE_OK:
            result = chooser.get_filename()
            file_filter = chooser.get_filter()
        chooser.destroy()
        return (result, file_filter)

    def save(self):
        filename, converter = self.current_file
        assert not converter.METADATA["requires_template"]
        converter.write(filename=filename)
        self._set_unsaved(False)

    def show(self):
        self.window.show()

    def set_palette(self, palette):
        for index, color in enumerate(palette):
            self.builder.get_object("colorbutton" + str(index + 1)).set_color(
                gtk.gdk.Color(*map(lambda c: (c + 1) * 256 - 1, color.rgb)))

    def on_colorbutton_set(self, widget):
        self._set_unsaved(True)

    def on_file_new_activate(self, widget):
        self.set_palette(NumberedPalette(16, colors=map(
            lambda color: Color(*HTML4_COLORS[color]),
            ("black", "maroon", "green", "olive", "navy", "purple", "teal",
             "silver", "gray", "red", "lime", "yellow", "blue", "magenta",
             "cyan", "white"))))
        self.current_file = ()

    def on_file_open_activate(self, widget):
        filename, file_filter = self.file_select(gtk.FILE_CHOOSER_ACTION_OPEN)
        filename and self.load_file(filename, file_filter)

    def on_file_save_activate(self, widget):
        self.save()

    def on_file_export_activate(self, widget):
        dialog = self.builder.get_object("export_dialog")
        result = dialog.run()
        dialog.hide()

        if result == gtk.RESPONSE_OK:
            template_chooser = self.builder.get_object("template_filechooser")
            output_chooser = self.builder.get_object("output_filechooser")

            template_file = template_chooser.get_filename()
            output_file = output_chooser.get_filename()

            filter_name = output_chooser.get_filter().get_name()
            converter = self.get_converter_by_filter(filter_name)
            assert converter

            if not template_file and converter.METADATA["requires_template"]:
                return gtk_message(parent=self.window, type_=gtk.MESSAGE_ERROR,
                    message_format="You must select a template file.")
            if output_file is None:
                return gtk_message(parent=self.window, type_=gtk.MESSAGE_ERROR,
                    message_format="You must specify a filename to export to.")

            converter.update_palette(self.get_palette())
            converter.write(template_file, output_file)

    def on_help_about_activate(self, widget):
        self.builder.get_object("about_dialog").run()

    def on_about_dialog_response(self, widget, response_id):
        if response_id in (gtk.RESPONSE_CANCEL, gtk.RESPONSE_CLOSE,
            gtk.RESPONSE_DELETE_EVENT):
            widget.hide()

    def gtk_main_quit(self, widget):
        self.save_and_quit()

    def on_main_window_delete_event(self, widget, event):
        return self.save_and_quit()

    def save_and_quit(self):
        if (self.unsaved and gtk_question("You have unsaved changes, " \
            "are you sure you want to quit?") or not self.unsaved):
            gtk.main_quit()
            return gtk.FALSE
        return gtk.TRUE

    def _set_unsaved(self, value):
        if not hasattr(self, "unsaved"): return
        if not self.current_file[1].METADATA["requires_template"]:
            self.unsaved = value
            self.builder.get_object("file_save").set_sensitive(value)


class ExportDialog(object):

    def __init__(self, builder, shared_data):
        self.shared_data = shared_data
        self.converters = shared_data.converters
        self.builder = builder
        self.file_filters = []
        self.window = builder.get_object("export_dialog")

        self.converter_combo = builder.get_object("converter_combobox")
        cell = gtk.CellRendererText()
        self.converter_combo.pack_start(cell, True)
        self.converter_combo.add_attribute(cell, "text", 0)
        self.converter_combo.set_active(0)

        config_dir = self.shared_data.config_dir

        template_chooser = builder.get_object("template_filechooser")
        template_chooser.set_current_folder(config_dir.absolute)

        self.output_chooser = builder.get_object("output_filechooser")
        self.set_file_filter(0)

    def set_file_filter(self, index):
        for name, targets in self.converters[index].METADATA["file_filters"]:
            file_filter = gtk.FileFilter()
            file_filter.set_name(name)
            if "patterns" in targets:
                map(file_filter.add_pattern, targets["patterns"])
            if "mime_types" in targets:
                map(file_filter.add_mimetype, targets["mime_types"])
            self.output_chooser.add_filter(file_filter)

    def on_converter_combobox_changed(self, widget):
        self.set_file_filter(self.converter_combo.get_active())

    def on_export_dialog_close(self, widget):
        pass


def main():
    app = Application("easel.glade", [MainWindow, ExportDialog])
    app.handlers[0].show()
    gtk.main()
