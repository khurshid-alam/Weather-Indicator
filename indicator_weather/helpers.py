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
import gconf

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

def on_http_proxy_changed_handler(client, cnxn_id=None, entry=None, data=None):
    """
    Handles http proxy support in urllib2
    """
    log = data
    log.debug("Proxy Handler: loading settings")

    # Taken from http://forum.compiz.org/viewtopic.php?t=9480
    # get info from GConf about possible proxies, auth, etc
    use_proxy = client.get_bool("/system/http_proxy/use_http_proxy")
    if not use_proxy:
        # no proxy, direct connection
        log.debug("Proxy Handler: using direct connection")
        proxy_info = {}
        proxy_support = urllib2.ProxyHandler(proxy_info)
        
    else:
        proxy_host = client.get_string("/system/http_proxy/host")
        proxy_port = client.get_int("/system/http_proxy/port")
        if proxy_host == None or proxy_port == 0:
            log.error("Proxy Handler: invalid proxy_host and proxy_port in gconf")
            return

        use_auth = client.get_bool("/system/http_proxy/use_authentication")
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
            auth_password = client.get_string("/system/http_proxy/authentication_password")
            auth_user = client.get_string("/system/http_proxy/authentication_user")
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

    #log.debug("Proxy info: %s" % proxy_info)
    opener = urllib2.build_opener(proxy_support, urllib2.HTTPHandler)
    urllib2.install_opener(opener)

def monitor_http_proxy(log):
    # get gconf client
    client = gconf.client_get_default()
    # add dir to watch
    client.add_dir("/system/http_proxy", gconf.CLIENT_PRELOAD_ONELEVEL)
    # init
    on_http_proxy_changed_handler(client, data=log)
    # set hook for changes
    client.notify_add("/system/http_proxy", on_http_proxy_changed_handler, log)
