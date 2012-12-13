# -*- coding: utf8 -*-

""" 
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

import os, urllib
import xbmc, xbmcvfs

class Scanner(object):

    def walk(self, path, types):
        filenames = []
        dirnames = []
        dirpath  = []
        
        if path.startswith('multipath://'):
            dirs = path[12:-1].split('/')
            for item in dirs:
                dirpath, dirnames, filenames += self._walk(urllib.unquote_plus(item), types)
        else:
            dirpath, dirnames, filenames = self._walk(urllib.unquote_plus(path), types)
            
        return dirpath, dirnames, filenames
    
    def _walk(self, path, types):
        filenames = []
        dirnames  = []
        dirpath   = []

        if xbmcvfs.exists(xbmc.translatePath(path)):
            dirs, files = xbmcvfs.listdir(path)

            for item in files:
                if types is not None:
                    if os.path.splitext(item)[1].lower() in types:
                        filenames.append(os.path.join(path, item))
                        dirnames.append('')
                        dirpath.append(path)
                else:
                    filenames.append(os.path.join(path, item))
                    dirnames.append('')
                    dirpath.append(path)

            for item in dirs:
                dirpath, dirnames, filenames += self.walk(os.path.join(path, item))
                    
        return dirpath, dirnames, filenames
        
    def getname(self, file):
        return os.path.basename(file)
        
    def getlocalfile(self, file, callback_proc):
        if os.path.exists(file):
            callback_proc(destination)    
        else:
            tempdir     = xbmc.translatePath('special://temp')
            filename    = self.getname(file)
            destination = os.path.join(tempdir,filename)
            
            xbmcvfs.copy(file, destination)
            callback_proc(destination)
            xbmcvfs.delete(destination)
        