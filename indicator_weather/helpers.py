#!/usr/bin/python
# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Sebastian MacDonald Sebas310@gmail.com
# Copyright (C) 2010 Mehdi Rejraji mehd36@gmail.com
# Copyright (C) 2013 Joshua Tasker jtasker@gmail.com
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
    'ProxyMonitor',
    'TimeFormatter',
    'NumberFormatter',
    ]
try:
    from gi.repository import Gio
    # this has to be called only once, otherwise we get segfaults
    DCONF_SCHEMAS = Gio.Settings.list_schemas()
except ImportError:
    # shouldn't we just fail entirely here?
    DCONF_SCHEMAS = []

from gi.repository import GConf
from gi.repository import Gtk
import traceback
import os
import urllib2
import locale
import re
from indicator_weather.indicator_weatherconfig import get_data_file

import gettext
_ = gettext.translation('indicator-weather').ugettext

def get_builder(builder_file_name):
    """Return a fully-instantiated Gtk.Builder instance from specified ui
    file

    :param builder_file_name: The name of the builder file, without extension.
        Assumed to be in the 'ui' directory under the data path.
    """
    # Look for the ui file that describes the user interface.
    ui_filename = get_data_file('ui', '%s.ui' % (builder_file_name))
    if not os.path.exists(ui_filename):
        ui_filename = None

    builder = Gtk.Builder()
    builder.set_translation_domain('indicator-weather')
    builder.add_from_file(ui_filename)
    return builder


class ProxyMonitor:
    """ Class to monitor proxy settings """

    @staticmethod
    def monitor_proxy(log):
        ProxyMonitor.log = log
        try:
            # GConf is deprecated; leaving it here for legacy systems
            if "org.gnome.system.proxy" in DCONF_SCHEMAS:
                # check for proxy mode='none'
                proxy_settings = Gio.Settings.new("org.gnome.system.proxy")
                proxy_mode = proxy_settings.get_string("mode")
                log.debug("ProxyMonitor: proxy mode is '%s'" % proxy_mode)
                if proxy_mode == "manual":
                    # load dconf settings
                    proxy_settings = Gio.Settings.new("org.gnome.system.proxy.http")
                    ProxyMonitor.dconf_proxy_changed(proxy_settings)
                    proxy_settings.connect("changed", ProxyMonitor.dconf_proxy_changed)
            else:
                # load gconf settings
                client = GConf.Client.get_default()
                client.add_dir("/system/http_proxy", GConf.ClientPreloadType.PRELOAD_ONELEVEL)
                ProxyMonitor.gconf_proxy_changed(client)
                client.notify_add("/system/http_proxy", ProxyMonitor.gconf_proxy_changed, None)

        except Exception, e:
            log.error("ProxyMonitor: %s" % e)
            log.debug(traceback.format_exc(e))

    @staticmethod
    def dconf_proxy_changed(settings, changed_key=None):
        """
        Loads dconf http proxy settings
        """
        try:
            ProxyMonitor.log.debug("ProxyMonitor: loading dconf settings")
            proxy_info = {}
            # Was taken from http://forum.compiz.org/viewtopic.php?t=9480 
            # Now we ignore the 'enabled' key, as per Gnome bug 648237:
            #     https://bugzilla.gnome.org/show_bug.cgi?id=648237
            #if settings.get_boolean("enabled"):
            proxy_info['host'] = settings.get_string("host")
            proxy_info['port'] = settings.get_int("port")
            if settings.get_boolean("use-authentication"):
                proxy_info['user'] = settings.get_string("authentication-user")
                proxy_info['pass'] = settings.get_string("authentication-password")

            ProxyMonitor.install_proxy_handler(proxy_info)

        except Exception, e:
            ProxyMonitor.log.error("ProxyMonitor: %s" % e)
            ProxyMonitor.log.debug(traceback.format_exc(e))

    @staticmethod
    def gconf_proxy_changed(client, cnxn_id=None, entry=None, data=None):
        """
        Loads gconf http proxy settings
        """
        try:
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

        except Exception, e:
            ProxyMonitor.log.error("ProxyMonitor: %s" % e)
            ProxyMonitor.log.debug(traceback.format_exc(e))

    @staticmethod
    def install_proxy_handler(proxy_info):
        """
        Installs http proxy support in urllib2
        """
        # validate data
        if 'host' in proxy_info:
            if proxy_info['host'] is not None:
                proxy_info['host'] = proxy_info['host'].strip()
            if not proxy_info['host']:
                ProxyMonitor.log.error("ProxyMonitor: empty proxy host!")
                proxy_info.pop('host')
                proxy_info.pop('port')
            elif not proxy_info['port']:
                ProxyMonitor.log.error("ProxyMonitor: invalid proxy port!")
                proxy_info.pop('host')
                proxy_info.pop('port')

        if 'host' in proxy_info and 'user' in proxy_info:
            if proxy_info['user'] is not None:
                proxy_info['user'] = proxy_info['user'].strip()
            if proxy_info['pass'] is not None:
                proxy_info['pass'] = proxy_info['pass'].strip()
            else:
                proxy_info['pass'] = ""
            if not proxy_info['user']:
                ProxyMonitor.log.error("ProxyMonitor: empty proxy user name!")
                proxy_info.pop('user')
                proxy_info.pop('pass')
                proxy_info.pop('host')

        # create proxy handler
        if 'host' not in proxy_info:
            ProxyMonitor.log.debug("ProxyMonitor: using direct connection")
            proxy_support = urllib2.ProxyHandler({})
        else:
            if 'user' not in proxy_info:
                ProxyMonitor.log.debug("ProxyMonitor: using simple proxy: " + \
                    "%(host)s:%(port)d" % proxy_info)
                proxy_url = "http://%(host)s:%(port)d" % proxy_info
            else:
                ProxyMonitor.log.debug("ProxyMonitor: using proxy with auth: " + \
                    "%(user)s@%(host)s:%(port)d" % proxy_info)
                proxy_url = "http://%(user)s:%(pass)s@%(host)s:%(port)d" % proxy_info
            proxy_support = urllib2.ProxyHandler({'http': proxy_url, 
    					      'https': proxy_url})

        # install new urllib2 opener
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
        try:
            for schema in TimeFormatter.SCHEMAS:
                if schema in DCONF_SCHEMAS:
                    log.debug("TimeFormatter: loading indicator-datetime settings: %s" % schema)
                    TimeFormatter.settings = Gio.Settings.new(schema)
                    TimeFormatter.calc_format(TimeFormatter.settings)
                    TimeFormatter.settings.connect("changed", TimeFormatter.calc_format)
                    break
            # this else belongs to for loop
            else:
                log.debug("TimeFormatter: indicator-datetime settings not found")

        except Exception, e:
            log.error("TimeFormatter: %s" % e)
            log.debug(traceback.format_exc(e))

    @staticmethod
    def format_time(t):
        """ do the format """
        if not t:
            return u"Unknown"
        return t.strftime(TimeFormatter.format.encode('utf-8')).decode('utf-8')

    @staticmethod
    def calc_format(timeformat_settings, changed_key=None):
        """ settings init or changed """
        TimeFormatter.log.debug("TimeFormatter: time format changed")
        time_format = timeformat_settings.get_enum("time-format")

        if time_format == TimeFormatter.SETTINGS_TIME_24_HOUR:
            TimeFormatter.format = "%H:%M"

        elif time_format == TimeFormatter.SETTINGS_TIME_12_HOUR:
            TimeFormatter.format = "%I:%M %p"

        elif time_format == TimeFormatter.SETTINGS_TIME_CUSTOM or time_format == TimeFormatter.SETTINGS_TIME_LOCALE:
            # ignore this as it might contain date params
            #TimeFormatter.format = gsettings.get_string("custom-time-format")
            TimeFormatter.format = "%X"

class NumberFormatter:
    """
    Formats a number with respect to the locale settings
    """

    # regex to remove trailing zeros
    re_trailing_zeros = None
    # regex to replace -0
    re_minus_zero = re.compile("^-0$")

    @staticmethod
    def format_float(value, precision = 1):
        """
        Formats a float with current locale's conventions (decimal point &
        grouping), with specified precision.
        It strips trailing zeros after the decimal point and replaces -0 with 0.
        """
        p = int(precision)
        v = float(value)
        s = locale.format("%.*f", (p, v), True)
        if p > 0:
            # compile regex if needed
            if NumberFormatter.re_trailing_zeros is None:
                try: dp = locale.localeconv().get('decimal_point', '.')
                except: dp = '.'
                NumberFormatter.re_trailing_zeros = re.compile(dp + "?0+$")

            s = NumberFormatter.re_trailing_zeros.sub('', s)
        return NumberFormatter.re_minus_zero.sub('0', s)
