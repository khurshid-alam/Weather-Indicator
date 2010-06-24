# -*- coding: utf-8 -*-
### BEGIN LICENSE
# Copyright (C) 2010 Sebastian MacDonald Sebas310@gmail.com
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

import gtk

from weather_indicator.helpers import get_builder

import gettext
from gettext import gettext as _
gettext.textdomain('weather-indicator')

class AboutWeatherIndicatorDialog(gtk.AboutDialog):
    __gtype_name__ = "AboutWeatherIndicatorDialog"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated AboutWeatherIndicatorDialog object.
        """
        builder = get_builder('AboutWeatherIndicatorDialog')
        new_object = builder.get_object("about_weather_indicator_dialog")
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called while initializing this instance in __new__

        finish_initalizing should be called after parsing the ui definition
        and creating a AboutWeatherIndicatorDialog object with it in order to
        finish initializing the start of the new AboutWeatherIndicatorDialog
        instance.
        
        Put your initialization code in here and leave __init__ undefined.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.builder.connect_signals(self)

        # Code for other initialization actions should be added here.


if __name__ == "__main__":
    dialog = AboutWeatherIndicatorDialog()
    dialog.show()
    gtk.main()
