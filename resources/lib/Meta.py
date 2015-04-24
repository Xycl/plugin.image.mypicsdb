# -*- coding: utf8 -*-
"""
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

import resources.lib.common as common
import ImageRating
import xbmc
import mmap
import os

from resources.lib.EXIF import process_file as EXIF_file
from time import strftime, strptime
from resources.lib.iptcinfo import IPTCInfo
from resources.lib.iptcinfo import c_datasets as IPTC_FIELDS
from resources.lib.XMP import XMP_Tags


# noinspection PyBroadException
class Reader():
    def __init__(self, fullpath):
        self.lists_separator = "||"
        self.fullpath = fullpath

    def get_metas(self):

        picentry = {}

        ############################
        # getting  EXIF  infos     #
        ############################
        try:
            common.log("VFSScanner._get_metas()._get_exif()", 'Reading EXIF tags from "%s"' % self.fullpath)
            exif = self._get_exif()
            picentry.update(exif)
            common.log("VFSScanner._get_metas()._get_exif()", "Finished reading EXIF tags")
        except Exception, msg:
            common.log("VFSScanner._get_metas()._get_exif()", "Exception", xbmc.LOGERROR)
            common.log("VFSScanner._get_metas()._get_exif()", msg, xbmc.LOGERROR)

        ############################
        # getting  IPTC  infos     #
        ############################
        try:
            common.log("VFSScanner._get_metas()._get_iptc()", 'Reading IPTC tags from "%s"' % self.fullpath)
            iptc = self._get_iptc()
            picentry.update(iptc)
            common.log("VFSScanner._get_metas()._get_iptc()", "Finished reading IPTC tags")
        except Exception, msg:
            common.log("VFSScanner._get_metas()_get_iptc()", "Exception", xbmc.LOGERROR)
            common.log("VFSScanner._get_metas()._get_iptc()", msg, xbmc.LOGERROR)

        ###############################
        # getting  XMP infos          #
        ###############################
        try:
            common.log("VFSScanner._get_metas()._get_xmp()", 'Reading XMP tags from "%s"' % self.fullpath)
            xmp = self._get_xmp()
            picentry.update(xmp)
            common.log("VFSScanner._get_metas()._get_xmp()", "Finished reading XMP tags")
        except Exception, msg:
            common.log("VFSScanner._get_metas()._get_xmp()", "Exception", xbmc.LOGERROR)
            common.log("VFSScanner._get_metas()._get_xmp()", msg, xbmc.LOGERROR)

        picentry['Image Rating'] = ImageRating.Reader(picentry).get_rating()

        return picentry

    def _get_exif(self):

        EXIF_fields = [
            "Image Model",
            "Image Orientation",
            "Image Rating",
            "Image RatingPercent",
            "Image Artist",
            "GPS GPSLatitude",
            "GPS GPSLatitudeRef",
            "GPS GPSLongitude",
            "GPS GPSLongitudeRef",
            "Image DateTime",
            "EXIF DateTimeOriginal",
            "EXIF DateTimeDigitized",
            "EXIF ExifImageWidth",
            "EXIF ExifImageLength",
            "EXIF Flash",
            "Image ResolutionUnit",
            "Image XResolution",
            "Image YResolution",
            "Image Make",
            "EXIF FileSource",
            "EXIF SceneCaptureType",
            "EXIF DigitalZoomRatio",
            "EXIF ExifVersion"
        ]

        # try to open self.fullpath in modify/write mode. Windows needs this for memory mapped file support.
        try:
            # General for all OS. Use unicode for self.fullpath.
            # This fails with OpenElec or if modify/write attribute isn't set.
            f = open(self.fullpath, "r+b")
            common.log("VFSScanner._get_exif()", 'File opened with statement: %s' % 'f=open(self.fullpath,"r+b")')
        except:
            try:
                # Special for OpenElec. Use utf-8 for self.fullpath.
                # If modify/write attribute isn't set then it'll fail.
                f = open(self.fullpath.encode("utf-8"), "r+b")
                common.log("VFSScanner._get_exif()",
                           'File opened with statement: %s' % 'f=open(self.fullpath.encode("utf-8"),"r+b")')
            except:
                # Where're here because write/modify attribute is missing and file could not be opened.
                try:
                    # General for all OS. Use unicode for self.fullpath.
                    f = open(self.fullpath, "rb")
                    common.log("VFSScanner._get_exif()",
                               'File opened with statement: %s' % 'f=open(self.fullpath,"rb")')
                except:
                    # Special for OpenElec. Use utf-8 for self.fullpath.
                    f = open(self.fullpath.encode('utf-8'), "rb")
                    common.log("VFSScanner._get_exif()",
                               'File opened with statement: %s' % 'f=open(self.fullpath.encode("utf-8"),"rb")')
        common.log("VFSScanner._get_exif()", 'Calling function EXIF_file for "%s"' % self.fullpath)

        mmapfile = 0
        try:
            # If write/modify attribute isn't set then this will fail on Windows because above the file was opened read only!
            mmapfile = mmap.mmap(f.fileno(), 0)
            tags = EXIF_file(mmapfile, details=False)
            common.log("VFSScanner._get_exif()", 'EXIF_file with mmap support returned')
        except:
            try:
                # We've to open the file without memory mapped file support.
                tags = EXIF_file(f, details=False)
                common.log("VFSScanner._get_exif()", 'EXIF_file without mmap support returned')
            except Exception, msg:
                common.log("VFSScanner._get_exif", self.fullpath, xbmc.LOGERROR)
                common.log("VFSScanner._get_exif", "%s - %s" % (Exception, msg), xbmc.LOGERROR)

        if mmapfile != 0:
            mmapfile.close()

        f.close()

        picentry = {}

        for tag in EXIF_fields:
            if tag in tags.keys():
                if tag in ["EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime"]:
                    tagvalue = None
                    for datetimeformat in ["%Y:%m:%d %H:%M:%S", "%Y.%m.%d %H.%M.%S", "%Y-%m-%d %H:%M:%S"]:
                        try:
                            tagvalue = strftime("%Y-%m-%d %H:%M:%S", strptime(tags[tag].__str__(), datetimeformat))
                            break
                        except:
                            pass
                            # common.log("VFSScanner._get_exif",  "Datetime (%s) did not match for '%s' format... trying an other one..."%(tags[tag].__str__(),datetimeformat), xbmc.LOGERROR )
                    if not tagvalue:
                        common.log("VFSScanner._get_exif",
                                   "ERROR : the datetime format is not recognize (%s)" % tags[tag].__str__(),
                                   xbmc.LOGERROR)

                else:
                    tagvalue = tags[tag].__str__()
                try:
                    picentry[tag] = tagvalue
                except Exception, msg:
                    common.log("VFSScanner._get_exif", self.fullpath, xbmc.LOGERROR)
                    common.log("VFSScanner._get_exif", "%s - %s" % (Exception, msg), xbmc.LOGERROR)

        if not picentry.has_key("Image Rating"):
            picentry["Image Rating"] = ""

        return picentry

    def _get_iptc(self):

        try:
            info = IPTCInfo(self.fullpath)

        except Exception, msg:
            if not type(msg.args[0]) == type(int()):
                if msg.args[0].startswith("No IPTC data found."):
                    return {}
                else:
                    common.log("VFSScanner._get_iptc", "%s" % self.fullpath)
                    common.log("VFSScanner._get_iptc", "%s - %s" % (Exception, msg))
                    return {}
            else:
                common.log("VFSScanner._get_iptc", "%s" % self.fullpath)
                common.log("VFSScanner._get_iptc", "%s - %s" % (Exception, msg))
                return {}

        iptc = {}

        if len(info.data) < 2:
            return iptc

        try:
            for k in info.data.keys():
                if k in IPTC_FIELDS:
                    try:
                        if isinstance(info.data[k], unicode):
                            try:
                                iptc[IPTC_FIELDS[k]] = info.data[k]
                            except UnicodeDecodeError:
                                iptc[IPTC_FIELDS[k]] = common.smart_unicode(info.data[k])
                                # unicode(info.data[k].encode("utf8").__str__(),"utf8")

                        elif isinstance(info.data[k], list):
                            iptc[IPTC_FIELDS[k]] = common.smart_unicode(
                                self.lists_separator.join([i for i in info.data[k]]))

                        elif isinstance(info.data[k], str):
                            iptc[IPTC_FIELDS[k]] = common.smart_unicode(info.data[k])

                        else:
                            common.log("VFSScanner._get_iptc", "%s" % self.fullpath)
                            common.log("VFSScanner._get_iptc", "WARNING : type returned by iptc field is not handled :")
                            common.log("VFSScanner._get_iptc", repr(type(info.data[k])))
                    except:
                        common.log("VFSScanner._get_iptc", "failure")
                        pass
        except:
            pass

        return iptc

    def _get_xmp(self):
        ###############################
        # get XMP infos               #
        ###############################
        tags = {}
        try:
            xmp_class = XMP_Tags()

            tags = xmp_class.get_xmp(os.path.dirname(self.fullpath), os.path.basename(self.fullpath))

        except Exception, msg:
            common.log("VFSScanner._get_xmp", 'Error reading XMP tags for "%s"' % self.fullpath, xbmc.LOGERROR)
            common.log("VFSScanner._get_xmp", "%s - %s" % (Exception, msg), xbmc.LOGERROR)

        return tags
