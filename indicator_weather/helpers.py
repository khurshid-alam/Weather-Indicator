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
    'make_window',
    ]

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

def monitor_upower(sleep_handler, resume_handler):
    """
    Attemts to connect to UPower interface
    """
    # http://upower.freedesktop.org/docs/UPower.html
    global log
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

def proxy_changed(client):
    """
    Handles http proxy support in urllib2
    """
    global log
    log.debug("Proxy Handler: loading settings")

    # Taken from http://forum.compiz.org/viewtopic.php?t=9480
    # get info from GConf about possible proxies, auth, etc
    use_proxy = client.get_boolean("enabled")
    if not use_proxy:
        # no proxy, direct connection
        log.debug("Proxy Handler: using direct connection")
        proxy_info = {}
        proxy_support = urllib2.ProxyHandler(proxy_info)
        
    else:
        proxy_host = client.get_string("host")
        proxy_port = client.get_int("port")
        if proxy_host == None or proxy_port == 0:
            log.error("Proxy Handler: invalid proxy_host and proxy_port in gconf")
            return

        use_auth = client.get_bool("use_authentication")
        if not use_auth:
            # simple proxy without auth
            log.debug("Proxy Handler: using simple proxy")
            proxy_info = {
                'host': proxy_host,
                'port': proxy_port
            }
            proxy_support = urllib2.ProxyHandler({
                'http': "http://%(host)s:%(port)d" % proxy_info})
        else:
            # proxy with authentication
            log.debug("Proxy Handler: using proxy with auth")
            auth_password = client.get_string("authentication_password")
            auth_user = client.get_string("authentication_user")
            if auth_user == None or auth_password == None:
                log.error("Proxy Handler: invalid authentication_user and authentication_password in gconf")
                return

            # code from Andre Bocchini <lists@andrebocchini.com>
            # at http://bytes.com/forum/thread22918.html
            proxy_info = {
                'user': auth_user,
                'pass': auth_password,
                'host': proxy_host,
                'port': proxy_port
            }
            proxy_support = urllib2.ProxyHandler({
                'http': "http://%(user)s:%(pass)s@%(host)s:%(port)d" % proxy_info})

    log.debug("Proxy info: %s" % proxy_info)
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

    @staticmethod
    def format_time(t):
        """ do the format """
        return t.strftime(TimeFormatter.format)

    @staticmethod
    def calc_format(timeformat_settings, changed_key=None):
        """ settings init or changed """
        global log
        log.debug("Time Formatter: time format changed")
        time_format = timeformat_settings.get_enum("time-format")

        if time_format == TimeFormatter.SETTINGS_TIME_24_HOUR:
            TimeFormatter.format = "%H:%M"

        elif time_format == TimeFormatter.SETTINGS_TIME_12_HOUR:
            TimeFormatter.format = "%I:%M %p"

        elif time_format == TimeFormatter.SETTINGS_TIME_CUSTOM or time_format == TimeFormatter.SETTINGS_TIME_LOCALE:
            # ignore this as it might contain date params
            #TimeFormatter.format = gsettings.get_string("custom-time-format")
            TimeFormatter.format = "%X"
