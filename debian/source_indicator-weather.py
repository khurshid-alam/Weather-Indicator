from apport.hookutils import *
import os.path

def add_info(report, ui=None):
    if not apport.packaging.is_distro_package(report['Package'].split()[0]):
        report['ThirdParty'] = 'True'
        report['CrashDB'] = 'indicator_weather'
    report['settings'] = command_output(['gconftool-2', '-R', '/apps/indicator-weather'])
    log_filename = os.path.join(os.path.expanduser("~/.cache"), "indicator-weather.log")
    if os.path.exists(log_filename):
        report['IndicatorLog'] = open(log_filename).read()
