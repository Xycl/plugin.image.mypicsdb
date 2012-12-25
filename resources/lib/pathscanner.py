#!/usr/bin/python
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

import os, urllib, re
import xbmc, xbmcvfs

class Scanner(object):

    def walk(self, path, recursive = False, types = None):
        filenames = []
        dirnames  = []

        if type(path).__name__=='unicode':
            path = path.encode('utf-8')
            
        if path.startswith('multipath://'):
            dirs = path[12:-1].split('/')
            for item in dirs:
                dirnames1, filenames1 = self._walk(urllib.unquote_plus(item), recursive, types)

                for dir in dirnames1:
                    dirnames.append(dir)
                for file in filenames1:
                    filenames.append(file)               
               
        else:
            #print "In else"
            dirnames, filenames = self._walk(urllib.unquote_plus(path), recursive, types)

                    
        return dirnames, filenames


    def _walk(self, path, recursive, types):
        filenames = []
        dirnames   = []
        dirs      = []
        files     = []

        path = xbmc.translatePath(path)

        if xbmcvfs.exists(xbmc.translatePath(path)) or re.match(r"[a-zA-Z]:\\", path) is not None:
            print "in exists"
            subdirs, files = xbmcvfs.listdir(path)
            for dir in subdirs:
                dirnames.append(os.path.join(path, dir))

            for file in files:
                if types is not None:
                    if os.path.splitext(file)[1].upper() in types or os.path.splitext(file)[1].lower() in types :
                        filenames.append(os.path.join(path, file))
                else:              
                    filenames.append(os.path.join(path, file))


            if recursive:
                for item in subdirs:
                    dirnames1, filenames1 = self._walk(os.path.join(path, item), recursive, types)
                    for item in dirnames1:
                        dirnames.append(item)
                    for item in filenames1:
                        filenames.append(item)
        
        else:
            print path 
            print "does not exists"
        return dirnames, filenames


    def getname(self, file):
        return os.path.basename(file)

    def delete(self, file):
        xbmcvfs.delete(file)
        
    def getlocalfile(self, file):
        
        if os.path.exists(file):
            #print "Local = " + file
            return file, False
        else:
            tempdir     = xbmc.translatePath('special://temp')
            filename    = self.getname(file)
            destination = os.path.join(tempdir,filename)
            xbmcvfs.copy(file, destination)

            #print "Remote = " + destination
            return destination, True

        