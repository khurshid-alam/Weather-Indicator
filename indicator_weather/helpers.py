# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Sebastian MacDonald Sebas310@gmail.com
# Copyright (C) 2010 Mehdi Rejraji mehd36@gmail.com
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

"""Helpers for an Ubuntu application."""

__all__ = [
    'get_builder',
    'monitor_upower',
    'ProxyMonitor',
    'TimeFormatter',
    ]

from gi.repository import Gio
# this has to be called only once, otherwise we get segfaults
DCONF_SCHEMAS = Gio.Settings.list_schemas()

import os
import gtk
import urllib2
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from indicator_weather.indicator_weatherconfig import get_data_file

import gettext
from gettext import gettext as _
gettext.textdomain('indicator-weather')

def get_builder(builder_file_name):
    """Return a fully-instantiated gtk.Builder instance from specified ui 
    file
    
    :param builder_file_name: The name of the builder file, without extension.
        Assumed to be in the 'ui' directory under the data path.
    """
    # Look for the ui file that describes the user interface.
    ui_filename = get_data_file('ui', '%s.ui' % (builder_file_name))
    if not os.path.exists(ui_filename):
        ui_filename = None

    builder = gtk.Builder()
    builder.set_translation_domain('indicator-weather')
    builder.add_from_file(ui_filename)
    return builder

def monitor_upower(sleep_handler, resume_handler, log):
    """
    Attemts to connect to UPower interface
    """
    # http://upower.freedesktop.org/docs/UPower.html
    try:
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        if not bus.name_has_owner("org.freedesktop.UPower"):
            log.info("UPower service is missing, cannot monitor power events")
            return

        proxy = dbus.SystemBus().get_object("org.freedesktop.UPower",
                                            "/org/freedesktop/UPower")
        iface = dbus.Interface(proxy, "org.freedesktop.UPower")
        iface.connect_to_signal("Sleeping", sleep_handler)
        iface.connect_to_signal("Resuming", resume_handler)
        log.info("Monitoring UPower interface")

    except Exception, e:
        log.error("UPower error: %s" % e)

class ProxyMonitor:
    """ Class to monitor proxy settings """
        
    @staticmethod
    def monitor_proxy(log):
        ProxyMonitor.log = log
        # try dconf
        if "org.gnome.system.proxy.http" in DCONF_SCHEMAS:
            proxy_settings = Gio.Settings.new("org.gnome.system.proxy.http")
            ProxyMonitor.dconf_proxy_changed(proxy_settings)
            proxy_settings.connect("changed", ProxyMonitor.dconf_proxy_changed)
        else:
            # try gconf
            import gconf
            client = gconf.client_get_default()
            client.add_dir("/system/http_proxy", gconf.CLIENT_PRELOAD_ONELEVEL)
            ProxyMonitor.gconf_proxy_changed(client)
            client.notify_add("/system/http_proxy", ProxyMonitor.gconf_proxy_changed)

    @staticmethod
    def dconf_proxy_changed(settings):
        """
        Loads dconf hhtp proxy settings
        """
        ProxyMonitor.log.debug("ProxyMonitor: loading dconf settings")
        proxy_info = {}
        # Taken from http://forum.compiz.org/viewtopic.php?t=9480
        if settings.get_boolean("enabled"):
            proxy_info['host'] = settings.get_string("host")
            proxy_info['port'] = settings.get_int("port")
            if settings.get_boolean("use-authentication"):
                proxy_info['user'] = settings.get_string("authentication-user")
                proxy_info['pass'] = settings.get_string("authentication-password")

        ProxyMonitor.install_proxy_handler(proxy_info)

    @staticmethod
    def gconf_proxy_changed(client, cnxn_id=None, entry=None, data=None):
        """
        Loads gconf hhtp proxy settings
        """
        ProxyMonitor.log.debug("ProxyMonitor: loading gconf settings")
        proxy_info = {}
        # Taken from http://forum.compiz.org/viewtopic.php?t=9480
        if client.get_bool("/system/http_proxy/use_http_proxy"):
            proxy_info['host'] = client.get_string("/system/http_proxy/host")
            proxy_info['port'] = client.get_int("/system/http_proxy/port")
            if client.get_bool("/system/http_proxy/use_authentication"):
                proxy_info['user'] = client.get_string("/system/http_proxy/authentication_user")
                proxy_info['pass'] = client.get_string("/system/http_proxy/authentication_password")

        ProxyMonitor.install_proxy_handler(proxy_info)

    @staticmethod
    def install_proxy_handler(proxy_info):
        """
        Installs http proxy support in urllib2
        """
        if 'host' not in proxy_info:
            ProxyMonitor.log.debug("ProxyMonitor: using direct connection")
            proxy_support = urllib2.ProxyHandler({})
            
        elif 'user' not in proxy_info:
            ProxyMonitor.log.debug("ProxyMonitor: using simple proxy")
            if proxy_info['host'] is None:
                ProxyMonitor.log.error("ProxyMonitor: invalid proxy host")
                return
            if proxy_info['port'] == 0:
                ProxyMonitor.log.error("ProxyMonitor: invalid proxy port")
                return
            proxy_support = urllib2.ProxyHandler({
                'http': "http://%(host)s:%(port)d" % proxy_info})

        else:
            ProxyMonitor.log.debug("ProxyMonitor: using proxy with auth")
            if proxy_info['user'] is None:
                ProxyMonitor.log.error("ProxyMonitor: invalid proxy user")
                return
            if proxy_info['pass'] is None:
                ProxyMonitor.log.error("ProxyMonitor: invalid proxy pass")
                return
            proxy_support = urllib2.ProxyHandler({
                'http': "http://%(user)s:%(pass)s@%(host)s:%(port)d" % proxy_info})
        
        #disable this logging as it might log the password
        #ProxyMonitor.log.debug("Proxy info: %s" % proxy_info)
        opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)

class TimeFormatter:
    """
    Formats a time object with respect to the settings of indicator-datetime
    """

    # default format from locale
    format = "%X"

    SETTINGS_TIME_LOCALE = 0
    SETTINGS_TIME_12_HOUR = 1
    SETTINGS_TIME_24_HOUR = 2
    SETTINGS_TIME_CUSTOM = 3

    SCHEMAS = (
        "com.canonical.indicator.datetime", #natty
        "org.ayatana.indicator.datetime",   #maverick
    )

    @staticmethod
    def monitor_indicator_datetime(log):
        TimeFormatter.log = log
        for schema in TimeFormatter.SCHEMAS:
            if schema in DCONF_SCHEMAS:
                log.debug("TimeFormatter: loading indicator-datetime settings: %s" % schema)
                TimeFormatter.settings = Gio.Settings.new(schema)
                TimeFormatter.calc_format(TimeFormatter.settings)
                TimeFormatter.settings.connect("changed", TimeFormatter.calc_format)
                break
        else:
            log.debug("TimeFormatter: indicator-datetime settings not found")

    @staticmethod
    def format_time(t):
        """ do the format """
        return t.strftime(TimeFormatter.format)

    @staticmethod
    def calc_format(timeformat_settings, changed_key=None):
        """ settings init or changed """
        TimeFormatter.log.debug("Time Formatter: time format changed")
        time_format = timeformat_settings.get_enum("time-format")

        if time_format == TimeFormatter.SETTINGS_TIME_24_HOUR:
            TimeFormatter.format = "%H:%M"

        elif time_format == TimeFormatter.SETTINGS_TIME_12_HOUR:
            TimeFormatter.format = "%I:%M %p"

        elif time_format == TimeFormatter.SETTINGS_TIME_CUSTOM or time_format == TimeFormatter.SETTINGS_TIME_LOCALE:
            # ignore this as it might contain date params
            #TimeFormatter.format = gsettings.get_string("custom-time-format")
            TimeFormatter.format = "%X"
