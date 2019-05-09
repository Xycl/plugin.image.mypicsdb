#!/usr/bin/python
# -*- coding: utf8 -*-

""" 
Common functions.
Copyright (C) 2012 Xycl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""


import sys, os, urllib
import xbmc, xbmcaddon

# change for ruuk's plugin screensaver
try:
    __addonname__    = sys.modules[ "__main__" ].__addonname__
except:
    __addonname__ = 'plugin.image.mypicsdb'

    
__settings__ = xbmcaddon.Addon(id=__addonname__)
__language__ = __settings__.getLocalizedString
__homepath__ = __settings__.getAddonInfo('path').decode('utf-8')
__sys_file_encoding__ = sys.getfilesystemencoding()
__addonname__   = __settings__.getAddonInfo('name')
__icon__        = __settings__.getAddonInfo('icon')


def getaddon_path():
    return __homepath__


def getaddon_name():
    return __settings__.getAddonInfo('name')

    
def getaddon_info(parm):
    # author, changelog, description, disclaimer, fanart. icon, id, name, path, profile, stars, summary, type, version
    return __settings__.getAddonInfo(parm)


def getstring(num):
    return __language__(num)


# taken from: http://wiki.xbmc.org/index.php?title=Xbmcaddon_module
def openaddon_settings():
    __settings__.openSettings()


def getxbmc_version():    
    xbmc.getInfoLabel('System.BuildVersion')


def getaddon_setting(name):
    return __settings__.getSetting(name)


def setaddon_setting(name, value):
    __settings__.setSetting(id=name, value=value)


# helpers
def show_notification(title, message, timeout=5000, image=""):
    if image == "":
        command = 'Notification(%s,%s,%s,%s)' % (smart_utf8(title), smart_utf8(message), timeout, __icon__)
    else:
        command = 'Notification(%s,%s,%s,%s)' % (smart_utf8(title), smart_utf8(message), timeout, smart_utf8(image))
    xbmc.executebuiltin(command)


def run_plugin(plugin, params=""):
    if params != "":
        quoted_params = [ name+"="+quote_param(value)+"&" for (name, value) in params][:-1]
        xbmc.executebuiltin('XBMC.RunPlugin(%s?%s)'%(smart_utf8(plugin), smart_utf8(quoted_params)))
    else:
        xbmc.executebuiltin('XBMC.RunPlugin(%s)'%smart_utf8(plugin))


def run_script(script):
    xbmc.executebuiltin('XBMC.RunScript(%s)'%smart_utf8(script))


def get_params():
    """ extract params from argv[2] to make a dict (key=value) """
    param_dict = {}
    try:
        if sys.argv[2]:
            param_pairs=sys.argv[2][1:].split( "&" )
            for params_pair in param_pairs:
                param_splits = params_pair.split('=')
                if (len(param_splits))==2:
                    param_dict[urllib.unquote_plus(param_splits[0])] = urllib.unquote_plus(param_splits[1])
    except:
        pass
    return param_dict

        
def smart_unicode(s):
    """credit : sfaxman"""
    if not s:
        return ''
    try:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'UTF-8')
        elif not isinstance(s, unicode):
            s = unicode(s, 'UTF-8')
    except:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'ISO-8859-1')
        elif not isinstance(s, unicode):
            s = unicode(s, 'ISO-8859-1')
    return s


def smart_utf8(s):
    return smart_unicode(s).encode('utf-8')


def get_crc32( parm ):
    parm = parm.lower()        
    byte = bytearray(parm.encode())
    crc = 0xffffffff;
    for b in byte:
        crc = crc ^ (b << 24)          
        for _ in range(8):
            if (crc & 0x80000000 ):                 
                crc = (crc << 1) ^ 0x04C11DB7                
            else:
                crc = crc << 1;                        
        crc = crc & 0xFFFFFFFF

    return '%08x' % crc    


def quote_param(parm):
    parm = smart_utf8( parm.replace("\\", "\\\\\\\\").replace ("'", "\\'").replace ('"', '\\"') )
    parm = urllib.quote_plus(parm)

    return parm


def unquote_param(parm):
    parm = urllib.unquote_plus(parm)
    parm = smart_unicode( parm.replace ('\\"', '"').replace ("\\'", "'").replace("\\\\\\\\", "\\") )

    return parm


def log(module, msg, level=xbmc.LOGDEBUG):
    if type(module).__name__=='unicode':
        module = module.encode('utf-8')

    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')
        
    if getaddon_setting("debugging") == "true" and xbmc.LOGERROR != level:
        level = xbmc.LOGNOTICE

    filename = smart_utf8(os.path.basename(sys._getframe(1).f_code.co_filename))
    lineno  = str(sys._getframe(1).f_lineno)

    if len(module.strip()) == 0:
        try:
            module = "function " + sys._getframe(1).f_code.co_name
        except:
            module = " "
            pass
    else:
        module = 'object ' + module
    xbmc.log(str("[%s] line %5d in %s %s >> %s"%(__addonname__, int(lineno), filename, module, msg.__str__())), level)    


# version is a string like 'x.y.z'
# if first version is greater then -1 is returned. if equal then 0 is returned else +1
def check_version(first, second):
    a = first.split('.')
    b = second.split('.')
    
    for i in range(len(a)):
        # if we're here and there is no element left in b then a is greater than b
        if len(b)<i:
            return -1
        
        if int(a[i]) != int(b[i]):
            return int(b[i]) - int(a[i])
    # if we're here and a was equal to b, but b is longer than a then b must be greater  
    if len(b)>len(a):
        return 1
            
    return 0
