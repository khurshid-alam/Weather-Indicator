#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# main.py
# Copyright (C) Sebastian MacDonald 2010 <sebas310@gmail.com>
# 
# weather-indicator is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# weather-indicator is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.


import pygtk
pygtk.require('2.0')
import gtk
import gobject
import appindicator
import gconf
import os
import urllib2
import time
from threading import Timer
import thread
import locale


class weather_indicator:
    def __init__(self):
        self.winder = appindicator.Indicator ("weather-indicator", "stock_weather-cloudy", appindicator.CATEGORY_APPLICATION_STATUS)
        self.winder.set_status (appindicator.STATUS_ACTIVE)
        self.winder.set_attention_icon("weather-severe-alert")
        
        self.gconfClient = gconf.client_get_default()
        
        first_run = self.gconfClient.get_bool("/apps/weather-indicator/first_run")
        
        if first_run in (False, None):
            self.firsty()
        
        self.place = self.gconfClient.get_string("/apps/weather-indicator/place")
        self.places = self.place.split('|')
        
        self.menu = gtk.Menu()

        '''self.city_show = gtk.MenuItem()
        self.city_table = gtk.Table(1, 2, True)
        self.city_show.add(self.city_table)
        city_adder = gtk.Label("City")
        self.city_table.attach(city_adder, 0, 1, 0, 1)
        city_adder.show()
        self.city_show.show_all()
        self.menu.append(self.city_show)'''
        
        self.city_show = gtk.MenuItem()
        self.city_show.show()
        self.menu.append(self.city_show)
        
        self.cond_show = gtk.MenuItem()
        self.cond_show.show()
        self.menu.append(self.cond_show)
                
        self.temp_show = gtk.MenuItem()
        self.temp_show.show()
        self.menu.append(self.temp_show)
        
        self.humid_show = gtk.MenuItem()
        self.humid_show.show()
        self.menu.append(self.humid_show)
        
        self.wind_show = gtk.MenuItem()
        self.wind_show.show()
        self.menu.append(self.wind_show)
        
        breaker = gtk.SeparatorMenuItem()
        breaker.show()
        self.menu.append(breaker)
        
        woo = 1
        
        for place in self.places:
            loco = gtk.RadioMenuItem(None, place)
            loco.show()
            self.menu.append(loco)
        
        self.menu.append(breaker)
        
        replace = gtk.MenuItem("Change City")
        replace.connect("activate", self.replacer)
        replace.show()
        self.menu.append(replace)

        add = gtk.MenuItem("Add City")
        add.connect("activate", self.adder)
        add.show()
        self.menu.append(add)

        self.menu.append(breaker)
                
        prefs_show = gtk.MenuItem("Preferences")
        prefs_show.connect("activate", self.prefs)
        prefs_show.show()
        self.menu.append(prefs_show)

        about_ico = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        about_ico.connect("activate", self.about)
        about_ico.show()
        self.menu.append(about_ico)
        
        quitter = gtk.ImageMenuItem(gtk.STOCK_QUIT)
        quitter.connect("activate", self.quit)
        quitter.show()
        self.menu.append(quitter)
        
        self.update_weather()
        
        self.menu.show()        
        
        self.winder.set_menu(self.menu)

    def quit(self, widget, data=None):
        gtk.main_quit()
    
    def update_weather(self, widget=None):
        current = self.get_weather(self.place)
        
        self.condition = current
        
        print current
        
        current = current.lower()
        
        if current in ('chance of storm', 'storm', 'thunderstorm', 'chance of tstorm'):
            self.storms()
        elif current in ('sleet',  'snow',  'icy',  'flurries',  'chance of snow'):
            self.snow()
        elif current in ('dust',  'fog',  'smoke',  'haze',  'mist'):
            self.fog()
        elif current in ('chance of rain',  'rain',  'chance of rain'):
            self.showers()
        elif current in ('sunny', 'clear'):
            self.clear()
        elif current in ('mostly cloudy', 'cloudy'):
            self.cloudy()
        elif current in ('mostly sunny',  'partly cloudy'):
            self.few_clouds()
        else:
            self.snow()
        
        #self.city_table.attach(gtk.Label("City"), 0, 1, 0, 1)
        self.city_show.set_label(self.city)
        self.cond_show.set_label(self.condition)
        self.temp_show.set_label(self.temp + ' °F' )
        self.humid_show.set_label(self.humid)
        self.wind_show.set_label(self.wind)
        
        gobject.timeout_add(300000, self.update_weather)
                            
    def showers(self):
        self.winder.set_icon("stock_weather-showers")
        
    def storms(self):
        self.winder.set_icon("stock_weather-storm")
        
    def cloudy(self):
        self.winder.set_icon("stock_weather-cloudy")
        
    def few_clouds(self):
        self.winder.set_icon("weather-few-clouds")
    
    def fog(self):
        self.winder.set_icon("stock_weather-fog")    
        
    def clear(self):
        self.winder.set_icon("stock_weather-sunny")
        
    def snow(self):
    	self.winder.set_icon("stock_weather-snow")
        
    def severe(self):
        self.winder.set_icon("weather-severe-alert")
    
    def err(self):
        self.winder.set_icon("weather-severe-alert")
    
    def about(self, widget, data=None):
        dialog = gtk.AboutDialog()
        dialog.set_name('Weather-Indicator Applet')
        dialog.set_version('0.0.2rev2')
        dialog.set_authors(['Sebastian MacDonald <sebastian.macdonald@gmail.com>', 'Cullen Maglothin <cmaglothin@gmail.com>'])
        dialog.set_comments('A simple weather indicator applet')
        dialog.set_license('Distributed under the GPL license.\nhttp://www.gnu.org/licenses/')
        dialog.run()
        dialog.destroy()

	def hide_dialog(self, widget, data):
		widget.hide()
    
    def firsty(self):
        self.getText()
    
    def replacer(self, widget):
        self.getText()
        
    def adder(self, widget):
        self.getText(replace=False)
            
    def responseToDialog(self, entry, dialog, response):
	    dialog.response(response)
	    
    def getText(self, replace=True):
	    dialog = gtk.MessageDialog(
		    None,
		    gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
		    gtk.MESSAGE_QUESTION,
		    gtk.BUTTONS_OK,
		    None)
	    dialog.set_markup('Please enter your address:')
	    entry = gtk.Entry()
	    entry.connect("activate", self.responseToDialog, dialog, gtk.RESPONSE_OK)
	    hbox = gtk.HBox()
	    hbox.pack_start(gtk.Label("Address:"), False, 5, 5)
	    hbox.pack_end(entry)
	    dialog.vbox.pack_end(hbox, True, True, 0)
	    dialog.show_all()
	    dialog.run()
	    if replace == False:
	        self.place = self.place + '|' + entry.get_text()
	        self.gconfClient.set_string("/apps/weather-indicator/place", self.place)
	    else:
	        self.gconfClient.set_string("/apps/weather-indicator/place", entry.get_text())
	    self.gconfClient.set_bool("/apps/weather-indicator/first_run", True)
	    dialog.destroy()
	    
	    self.update_weather()
        
    def get_weather(self, city):

        #create google weather api url
        url = "http://www.google.com/ig/api?weather=" + urllib2.quote(city)

        try:
            # open google weather api url
            f = urllib2.urlopen(url)
        except:
            # if there was an error opening the url, return
            return "Error opening url"

        # read contents to a string
        s = f.read()

        # extract weather condition data from xml string
        weather = s.split("<current_conditions><condition data=\"")[-1].split("\"")[0]
        self.temp = s.split("<temp_f data=\"")[-1].split("\"")[0]
        self.city = s.split("<city data=\"")[-1].split("\"")[0]
        self.humid = s.split("<humidity data=\"Humidity: ")[-1].split("\"")[0]
        self.wind = s.split("<wind_condition data=\"Wind: ")[-1].split("\"")[0]

        # if there was an error getting the condition, the city is invalid
        if weather == "<?xml version=":
            self.temp = "Invalid city"
            self.city = "Invalid city"
            self.humid = "Invalid city"
            self.wind = "Invalid city"
            return "Invalid city"

        #return the weather condition
        return weather
    
    def prefs(self, widget):
        window = gtk.Window()
        window.set_size_request(500, 300)
        window.show_all()
    
def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    indicator = weather_indicator()
    main()


