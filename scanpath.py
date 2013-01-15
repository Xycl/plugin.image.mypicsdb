#!/usr/bin/python
# -*- coding: utf8 -*-

# xbmc modules
import xbmc, xbmcaddon
__addonname__ = 'plugin.image.mypicsdb'
__addon__ = xbmcaddon.Addon(id=__addonname__)
__language__ = __addon__.getLocalizedString

# python modules
import optparse
import os
from urllib import unquote_plus
from traceback import print_exc
from time import strftime,strptime

#local modules
from resources.lib.pathscanner import Scanner
from resources.lib.CharsetDecoder import smart_utf8, smart_unicode, log
import resources.lib.MypicsDB as mpdb
# local tag parsers
from resources.lib.iptcinfo import IPTCInfo
from resources.lib.iptcinfo import c_datasets as IPTC_FIELDS
from resources.lib.EXIF import process_file as EXIF_file
from resources.lib.XMP import XMP_Tags



#xbmc addons
from DialogAddonScan import AddonScan


db_type  = 'mysql' if __addon__.getSetting('mysql')=='true' else 'sqlite'
db_name  = 'Pictures.db' if len(__addon__.getSetting('db_name')) == 0 else __addon__.getSetting('db_name')
if db_type == 'sqlite':
    db_user    = ''
    db_pass    = ''
    db_address = ''
    db_port    = ''
else:
    db_user    = __addon__.getSetting('db_user')
    db_pass    = __addon__.getSetting('db_pass')
    db_address = __addon__.getSetting('db_address')
    db_port    = __addon__.getSetting('db_port')


class VFSScanner:

    def __init__(self):

        self.exclude_folders    = []
        self.all_extensions     = []
        self.picture_extensions = []
        self.video_extensions   = []
        self.lists_separator = "||"
        
        self.picsdeleted = 0
        self.picsupdated = 0
        self.picsadded   = 0
        self.picsscanned = 0
        self.current_root_entry = 0
        self.total_root_entries = 0
        self.totalfiles  = 0

        for path,recursive,update,exclude in mpdb.RootFolders():
            if exclude:
                self.exclude_folders.append(smart_unicode(path[:len(path)-1]))

        for ext in __addon__.getSetting("picsext").split("|"):
            self.picture_extensions.append("." + ext.replace(".","").upper())

        for ext in __addon__.getSetting("vidsext").split("|"):
            self.video_extensions.append("." + ext.replace(".","").upper())

        self.use_videos = __addon__.getSetting("usevids")

        self.all_extensions.extend(self.picture_extensions)
        self.all_extensions.extend(self.video_extensions)

        self.filescanner = Scanner()


    def dispatcher(self, options):

        self.options = options

        if self.options.rootpath:
            self.scan = AddonScan()
            self.scan.create( __language__(30000) )
            self.current_root_entry = 1
            self.total_root_entries = 1
            self.scan.update(0,0,
                        __language__(30000)+" ["+__language__(30241)+"]",#MyPicture Database [preparing]
                        __language__(30247))#please wait...
            self.options.rootpath = smart_utf8(unquote_plus( self.options.rootpath)).replace("\\\\", "\\").replace("\\\\", "\\").replace("\\'", "\'")
            self._countfiles(self.options.rootpath)
            self.total_root_entries = 1
            self._addpath(self.options.rootpath, None, self.options.recursive, True)
            
            self.scan.close()

        elif self.options.database:
            paths = mpdb.RootFolders()

            if paths:
                self.scan = AddonScan()
                self.scan.create( __language__(30000) )
                self.current_root_entry = 0
                self.total_root_entries = 0
                self.scan.update(0,0,
                            __language__(30000)+" ["+__language__(30241)+"]",#MyPicture Database [preparing]
                            __language__(30247))#please wait...
                for path,recursive,update,exclude in paths:
                    if exclude==0:
                        self.total_root_entries += 1
                        self._countfiles(path,False)

                for path,recursive,update,exclude in paths:
                    if exclude==0:
                        try:
                            self.current_root_entry += 1
                            self._addpath(path, None, recursive, update)
                        except:
                            print_exc()

                self.scan.close()

        xbmc.executebuiltin( "Notification(%s,%s)"%(__language__(30000).encode("utf8"),
                                                    __language__(30248).encode("utf8")%(self.picsscanned,self.picsadded,self.picsdeleted,self.picsupdated)
                                                    )
                             )


    def _countfiles(self, path, reset = True, recursive = True):
        if reset:
            self.totalfiles = 0
        
        (dirs, files) = self.filescanner.walk(path, recursive, self.picture_extensions if self.use_videos == "false" else self.all_extensions)
        self.totalfiles += len(files)

        return self.totalfiles


    def _addpath(self, path, parentfolderid, recursive, update):
        dirnames        = []
        filenames       = []
        """
        try:
        """
        path = smart_unicode(path)

        log("VFSScanner._addpath", "Scanning directory %s"%smart_utf8(path) )
        # Check excluded paths
        if path in self.exclude_folders:
            self.picsdeleted = self.picsdeleted + mpdb.RemovePath(path)
            return

        (dirnames, filenames) = self.filescanner.walk(path, False, self.picture_extensions if self.use_videos == "false" else self.all_extensions)

        # insert the new path into database
        foldername = smart_unicode(os.path.basename(path))
        if len(foldername)==0:
            foldername = os.path.split(os.path.dirname(path))[1]
        
        folderid = mpdb.DB_folder_insert(foldername, path, parentfolderid, 1 if len(filenames)>0 else 0 )
        
        # get currently stored files for 'path' from database.
        # needed for 'added', 'updated' or 'deleted' decision
        filesfromdb = mpdb.DB_listdir(smart_unicode(path))

        action = __language__(30242)#Updating
        # scan pictures and insert them into database
        if filenames:
            for pic in filenames:
                self.picsscanned += 1
                filename = smart_unicode(os.path.basename(pic))
                extension = os.path.splitext(pic)[1].upper()
                    
                picentry = { "idFolder": folderid,
                             "strPath": path,
                             "strFilename": filename,
                             "ftype": extension in self.picture_extensions and "picture" or extension in self.video_extensions and "video" or "",
                             "DateAdded": strftime("%Y-%m-%d %H:%M:%S"),
                             "Thumb": "",
                             "ImageRating": None
                             }



                sqlupdate = False
                filesha   = 0
                
                # get the meta tags. but only for pictures
                if extension in self.picture_extensions:
                    (localfile, isremote) = self.filescanner.getlocalfile(pic)
                    log( "VFSScanner._addpath", "Scanning picture %s"%smart_utf8(pic))
                    filesha = mpdb.fileSHA(localfile) 

                    tags = self._get_metas(smart_unicode(localfile))
                    picentry.update(tags)

                    # if isremote == True then the file was copied to cache directory.
                    if isremote:
                        self.filescanner.delete(localfile)
                        
                    if filename in filesfromdb:  # then it's an update

                        sqlupdate   = True
                        if mpdb.getFileSha(path,filename) != filesha:  # if sha is equal then don't scan again
                            self.picsupdated += 1
                            log( "VFSScanner._addpath", "Picture already exists and must be updated")
                            filesfromdb.pop(filesfromdb.index(filename))
                        else:
                            filesfromdb.pop(filesfromdb.index(filename))
                            log( "VFSScanner._addpath", "Picture already exists but not modified")

                            if self.scan and self.totalfiles!=0 and self.total_root_entries!=0:
                                self.scan.update(int(100*float(self.picsscanned)/float(self.totalfiles)),
                                              int(100*float(self.current_root_entry)/float(self.total_root_entries)),
                                              smart_utf8(__language__(30000)+"[%s] (%0.2f%%)"%(action,100*float(self.picsscanned)/float(self.totalfiles))),#"MyPicture Database [%s] (%0.2f%%)"
                                              smart_utf8(filename))
                                            
                            continue


                    else:
                        sqlupdate  = False
                        log( "VFSScanner._addpath", "New picture will be inserted into dB")
                        self.picsadded   += 1
                        
                # videos aren't scanned and therefore never updated
                elif extension in self.video_extensions:
                    log( "VFSScanner._addpath", "Adding video file %s"%smart_utf8(pic))
                    
                    if filename in filesfromdb:  # then it's an update
                        sqlupdate   = True
                        filesfromdb.pop(filesfromdb.index(filename))
                        continue


                    else:
                        sqlupdate  = False
                        self.picsadded   += 1

                else:
                    continue

                mpdb.DB_file_insert(path, filename, picentry, sqlupdate, filesha)
                if sqlupdate:
                    log( "VFSScanner._addpath", "Picture %s updated"%smart_utf8(pic))
                else:
                    log( "VFSScanner._addpath", "Picture %s inserted"%smart_utf8(pic))

                if self.scan and self.totalfiles!=0 and self.total_root_entries!=0:
                    self.scan.update(int(100*float(self.picsscanned)/float(self.totalfiles)),
                                  int(100*float(self.current_root_entry)/float(self.total_root_entries)),
                                  smart_utf8(__language__(30000)+"[%s] (%0.2f%%)"%(action,100*float(self.picsscanned)/float(self.totalfiles))),#"MyPicture Database [%s] (%0.2f%%)"
                                  smart_utf8(filename))
                
        # all pics left in list filesfromdb weren't found in file system.
        # therefore delete them from db
        if filesfromdb:
            for pic in filesfromdb:
                mpdb.DB_del_pic(path, pic)
                log( "VFSScanner._addpath", "Picture %s deleted from DB"%smart_utf8(pic))
                self.picsdeleted += 1

        if recursive:
            for dirname in dirnames:
                self._addpath(dirname, folderid, True, update)
        """
        except Exception,msg:
            print_exc
            log( "VFSScanner._addpath", "pic = filename")
            pass
        """

    def _get_metas(self, fullpath):
        picentry = {}
        extension = os.path.splitext(fullpath)[1].upper()
        if extension in self.picture_extensions:
            ###############################
            #    getting  EXIF  infos     #
            ###############################
            try:
                exif = self._get_exif(fullpath)
                picentry.update(exif)
            except Exception,msg:
                log( "VFSScanner._get_metas()._get_exif()", "Exception", xbmc.LOGERROR)
                print msg

            ###############################
            #    getting  IPTC  infos     #
            ###############################
            try:
                iptc = self._get_iptc(fullpath)
                picentry.update(iptc)
            except Exception,msg:
                log( "VFSScanner._get_metas()_get_iptc()", "Exception", xbmc.LOGERROR)
                print msg


            ###############################
            #    getting  XMP infos       #
            ###############################
            try:
                xmp = self._get_xmp(fullpath)
                picentry.update(xmp)
            except Exception,msg:
                log( "VFSScanner._get_metas()._get_xmp()", "Exception", xbmc.LOGERROR)
                print msg


        return picentry


    def _get_exif(self, picfile):

        EXIF_fields =[
                    "Image Model",
                    "Image Orientation",
                    "Image Rating",
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

        try:
            f=open(picfile,"rb")
        except:
            f=open(picfile.encode('utf-8'),"rb")

        tags = EXIF_file(f,details=False)

        f.close()

        picentry={}

        for tag in EXIF_fields:
            if tag in tags.keys():
                if tag in ["EXIF DateTimeOriginal","EXIF DateTimeDigitized","Image DateTime"]:
                    tagvalue=None
                    for datetimeformat in ["%Y:%m:%d %H:%M:%S","%Y.%m.%d %H.%M.%S","%Y-%m-%d %H:%M:%S"]:
                        try:
                            tagvalue = strftime("%Y-%m-%d %H:%M:%S",strptime(tags[tag].__str__(),datetimeformat))
                            break
                        except:
                            log("VFSScanner._get_exif",  "Datetime (%s) did not match for '%s' format... trying an other one..."%(tags[tag].__str__(),datetimeformat), xbmc.LOGERROR )
                    if not tagvalue:
                        log("VFSScanner._get_exif",  "ERROR : the datetime format is not recognize (%s)"%tags[tag].__str__(), xbmc.LOGERROR )

                else:
                    tagvalue = tags[tag].__str__()
                try:
                    picentry[tag]=tagvalue
                except Exception, msg:
                    log("VFSScanner._get_exif",  picfile , xbmc.LOGERROR)
                    log("VFSScanner._get_exif",  "%s - %s"%(Exception,msg), xbmc.LOGERROR )
        return picentry


    def _get_xmp(self, fullpath):
        ###############################
        # get XMP infos               #
        ###############################
        xmpclass = XMP_Tags()

        tags = xmpclass.get_xmp(os.path.dirname(fullpath), os.path.basename(fullpath))

        for tagname in tags:

            if tagname == 'Iptc4xmpExt:PersonInImage':
                key = 'persons'

                if tags.has_key(key):
                    tags[key] += '||' + tags[tagname]
                else:
                    tags[key] = tags[tagname]

        if tags.has_key('Iptc4xmpExt:PersonInImage'):
            del(tags['Iptc4xmpExt:PersonInImage'])
        return tags


    def _get_iptc(self, fullpath):

        try:
            info = IPTCInfo(fullpath)
        except Exception,msg:
            if not type(msg.args[0])==type(int()):
                if msg.args[0].startswith("No IPTC data found."):
                    return {}
                else:
                    log("VFSScanner._get_iptc", "%s"%fullpath )
                    log("VFSScanner._get_iptc", "%s - %s"%(Exception,msg) )
                    return {}
            else:
                log("VFSScanner._get_iptc", "%s"%fullpath )
                log("VFSScanner._get_iptc", "%s - %s"%(Exception,msg) )
                return {}
        iptc = {}

        if len(info.data) < 4:
            return iptc

        for k in info.data.keys():
            if k in IPTC_FIELDS:

                if isinstance(info.data[k],unicode):
                    try:
                        iptc[IPTC_FIELDS[k]] = info.data[k]
                    except UnicodeDecodeError:
                        iptc[IPTC_FIELDS[k]] = unicode(info.data[k].encode("utf8").__str__(),"utf8")
                elif isinstance(info.data[k],list):
                    iptc[IPTC_FIELDS[k]] = self.lists_separator.join([i for i in info.data[k]])
                elif isinstance(info.data[k],str):
                    iptc[IPTC_FIELDS[k]] = info.data[k].decode("utf8")
                else:
                    log("VFSScanner._get_iptc", "%s"%fullpath )
                    log("VFSScanner._get_iptc",  "WARNING : type returned by iptc field is not handled :" )
                    log("VFSScanner._get_iptc", repr(type(info.data[k])) )

            else:
                log("VFSScanner._get_iptc", "IPTC problem with file: %s"%fullpath, xbmc.LOGERROR)
                try:
                    log("VFSScanner._get_iptc", " '%s' IPTC field is not handled. Data for this field : \n%s"%(k,info.data[k][:80]) , xbmc.LOGERROR)
                except:
                    log("VFSScanner._get_iptc",  " '%s' IPTC field is not handled (unreadable data for this field)"%k , xbmc.LOGERROR)
                log("VFSScanner._get_iptc", "IPTC data for picture %s will be ignored"%fullpath , xbmc.LOGERROR)
                ipt = {}
                return ipt

        return iptc



if __name__=="__main__":

    parser = optparse.OptionParser()
    parser.enable_interspersed_args()
    parser.add_option("--database","-d",action="store_true", dest="database",default=False)
    parser.add_option("-p","--rootpath",action="store", type="string", dest="rootpath")
    parser.add_option("-r","--recursive",action="store_true", dest="recursive", default=False)
    (options, args) = parser.parse_args()

    obj = VFSScanner()
    obj.dispatcher(options)

