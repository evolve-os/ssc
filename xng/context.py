#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  This file is part of solus-sc
#
#  Copyright © 2013-2018 Ikey Doherty <ikey@solus-project.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 2 of the License, or
#  (at your option) any later version.
#

from .appsystem import AppSystem
from .executor import Executor
from .util.fetcher import ScMediaFetcher
from gi.repository import GObject, GLib
import threading


class ScContext(GObject.Object):
    """ ScContext manages the global plugins and shared components """

    plugins = None
    appsystem = None
    has_loaded = False
    fetcher = None
    executor = None
    driver_manager = None
    window = None

    __gtype_name__ = "ScContext"

    __gsignals__ = {
        'loaded': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, ()),
    }

    def __init__(self, window=None):
        GObject.Object.__init__(self)
        self.has_loaded = False
        self.window = window
        self.executor = Executor()

    def begin_load(self):
        """ Request a load for the system, i.e. after all components are
            now available for the UI """
        if self.has_loaded:
            return
        self.has_loaded = True
        self.init_ldm()
        self.init_plugins()
        self.fetcher = ScMediaFetcher()

        # Lazy load now
        thr = threading.Thread(target=self.build_data)
        thr.daemon = True
        thr.start()

    def init_ldm(self):
        """ Initialise Linux Driver Management if available. """
        try:
            from xng.plugins.drivers import DriverManager
            self.driver_manager = DriverManager()
        except Exception as e:
            print("LDM support unavailable on this system: {}".format(e))
            return
        self.driver_manager.reload()

    def init_snap_plugin(self):
        """ Eventually will load snapd plugin, currently disabled """
        snap = None
        try:
            from xng.plugins.snapd import SnapdPlugin
            snap = SnapdPlugin()
        except Exception as e:
            print("snapd support unavailable on this system: {}".format(e))
            snap = None

        if snap is not None:
            self.plugins.append(snap)

    def init_native_plugin(self):
        """ Init the native plugin """
        osPlugin = None

        try:
            from xng.plugins.native import get_native_plugin
            osPlugin = get_native_plugin()
        except Exception as e:
            print("Native plugin support unavailable for this system: {}".
                  format(e))
        if osPlugin is not None:
            self.plugins.insert(0, osPlugin)
        else:
            print("WARNING: Unsupported OS, native packaging unavailable!")

    def init_plugins(self):
        """ Take care of setting up our plugins
            This takes special care to wrap the initial import in case we
            have a module level import that would fail, i.e. import of
            the snapd-glib binding
        """
        self.plugins = []

        # self.init_snap_plugin()
        self.init_native_plugin()

    def emit_loaded(self):
        """ Emitted on the main thread to let the application know we're now
            ready and have available AppSystem data, etc. """
        print("defer loaded")
        self.emit('loaded')
        return False

    def build_data(self, args=None):
        """ Perform expensive operations """
        self.appsystem = AppSystem()
        GLib.idle_add(self.emit_loaded)

    def begin_install(self, item):
        """ Begin the work necessary to install a package """
        packages = item.get_plugin().plan_install_item(item)
        names = [x.get_id() for x in packages]

        # TODO: Make sure this part is a dependency dialog
        print("begin_install: {}".format(", ".join(names)))

        # Schedule now
        self.executor.install_package(item)

    def begin_remove(self, item):
        """ Begin the work necessary to remove a package """
        packages = item.get_plugin().plan_remove_item(item)
        print("begin_remove: {}".format(packages))

    def set_window_busy(self, busy):
        if not self.window:
            return
        self.window.set_busy(busy)

    def window_done(self):
        """ Let the window know all loading has completed """
        if not self.window:
            return False
        return self.window.done()

    def refresh_sources(self):
        """ Attempt to refresh all sources """
        for plugin in self.plugins:
            for source in plugin.sources():
                self.executor.refresh_source(plugin, source)
