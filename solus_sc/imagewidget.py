#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  This file is part of solus-sc
#
#  Copyright © 2017 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#

# from gi.repository import AppStreamGlib as As
from gi.repository import Gtk


class ScImageWidget(Gtk.Frame):
    """ The ScImageWidget is used as the *main* screenshot that is currently
        shown for a given application. It is not the image *selector*
    """

    page_not_found = None
    page_image = None
    page_loading = None
    stack = None

    # The currently set URI
    uri = None

    def __init__(self):
        Gtk.Frame.__init__(self)

        self.stack = Gtk.Stack.new()
        self.stack.set_homogeneous(False)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_interpolate_size(True)
        self.add(self.stack)
        self.set_border_width(0)
        self.set_property("margin", 0)
        self.set_shadow_type(Gtk.ShadowType.NONE)

        self.create_page_not_found()
        self.create_page_image()
        self.create_page_loading()

        self.show_all()

        self.stack.set_visible_child_name("page-not-found")

    def create_page_not_found(self):
        """ Construct the "no screenshot available" page """
        self.page_not_found = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        self.stack.add_named(self.page_not_found, "page-not-found")

        self.page_not_found.set_valign(Gtk.Align.CENTER)
        self.page_not_found.set_halign(Gtk.Align.CENTER)

        img = Gtk.Image.new_from_icon_name(
            "image-missing-symbolic", Gtk.IconSize.DIALOG)
        self.page_not_found.pack_start(img, False, False, 0)
        img.get_style_context().add_class("dim-label")
        img.set_margin_end(15)

        lab = Gtk.Label.new("<span size='x-large'>{}</span>".format(
            _("No screenshots available")))
        lab.set_use_markup(True)
        lab.get_style_context().add_class("dim-label")
        self.page_not_found.pack_start(lab, False, False, 0)

    def create_page_image(self):
        """ The main image preview. """
        self.page_image = Gtk.Image.new()
        self.stack.add_named(self.page_image, "page-image")

    def create_page_loading(self):
        """ Loading spinner to irritate and annoy """
        self.page_loading = Gtk.Spinner.new()
        self.page_loading.set_halign(Gtk.Align.CENTER)
        self.page_loading.set_valign(Gtk.Align.CENTER)
        self.page_loading.set_size_request(-1, 64)
        self.stack.add_named(self.page_loading, "page-loading")

    def show_image(self, uri, pbuf):
        """ Show the loaded image and switch to it on the view """
        self.uri = uri
        self.page_loading.stop()
        self.page_image.set_from_pixbuf(pbuf)
        self.stack.set_visible_child_name("page-image")

    def show_failed(self, uri, err):
        """ Show that the image loading failed """
        self.uri = uri
        self.page_loading.stop()
        # TODO: Do something with the error
        self.stack.set_visible_child_name("page-not-found")

    def show_not_found(self):
        """ Show that the image wasn't found """
        self.uri = None
        self.page_loading.stop()
        self.stack.set_visible_child_name("page-not-found")

    def show_loading(self):
        self.uri = None
        self.page_loading.start()
        self.stack.set_visible_child_name("page-loading")
