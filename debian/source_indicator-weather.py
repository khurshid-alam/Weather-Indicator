from apport.hookutils import *
import os.path

def add_info(report, ui=None):
    if not apport.packaging.is_distro_package(report['Package'].split()[0]):
        report['ThirdParty'] = 'True'
        report['CrashDB'] = 'indicator_weather'
    report['settings'] = command_output(['gconftool-2', '-R', '/apps/indicator-weather'])

    #FIXME: attach log here
    #if os.path.exists('/var/log/foo.log'):
    #    report['FooLog'] = open('/var/log/foo.log').read()
