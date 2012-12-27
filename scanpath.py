#!/usr/bin/python
# -*- coding: utf8 -*-

# xbmc modules
import xbmc, xbmcgui, xbmcaddon
Addon = xbmcaddon.Addon(id='plugin.image.mypicsdb')
__language__ = Addon.getLocalizedString

# python modules
import optparse
import os
from urllib import unquote_plus
from traceback import print_exc
from time import strftime,strptime

#local modules
from resources.lib.pathscanner import Scanner
from resources.lib.CharsetDecoder import smart_utf8, smart_unicode
import resources.lib.MypicsDB as mpdb
# local tag parsers
from resources.lib.iptcinfo import IPTCInfo
from resources.lib.iptcinfo import c_datasets as IPTC_FIELDS
from resources.lib.EXIF import process_file as EXIF_file
from resources.lib.XMP import XMP_Tags



#xbmc addons
from DialogAddonScan import AddonScan


db_type  = 'mysql' if Addon.getSetting('mysql')=='true' else 'sqlite'
db_name  = 'Pictures.db' if len(Addon.getSetting('db_name')) == 0 else Addon.getSetting('db_name')
if db_type == 'sqlite':
    db_user    = ''
    db_pass    = ''
    db_address = ''
    db_port    = ''
else:
    db_user    = Addon.getSetting('db_user')
    db_pass    = Addon.getSetting('db_pass')
    db_address = Addon.getSetting('db_address')
    db_port    = Addon.getSetting('db_port')


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
                self.exclude_folders.append(smart_unicode(path))

        for ext in Addon.getSetting("picsext").split("|"):
            self.picture_extensions.append("." + ext.replace(".","").upper())

        for ext in Addon.getSetting("vidsext").split("|"):
            self.video_extensions.append("." + ext.replace(".","").upper())

        self.use_videos = Addon.getSetting("usevids")

        self.all_extensions.extend(self.picture_extensions)
        self.all_extensions.extend(self.video_extensions)

        self.filescanner = Scanner()
        

    LOGDEBUG = 0
    LOGINFO = 1
    LOGNOTICE = 2
    LOGWARNING = 3
    LOGERROR = 4
    LOGSEVERE = 5
    LOGFATAL = 6
    LOGNONE = 7

    def log(self, msg, level=LOGDEBUG):
        if type(msg).__name__=='unicode':
            msg = msg.encode('utf-8')

        xbmc.log(str("MyPicsDB >> %s"%msg.__str__()), level)


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
        fullpath        = []
        uniquedirnames  = []
        olddir          = ''

        path = smart_unicode(path)
        
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

        # scan pictures and insert them into database
        if filenames:
            for pic in filenames:
                self.picsscanned += 1
                filename = smart_unicode(os.path.basename(pic))
                extension = os.path.splitext(pic)[1].upper()

                if filename in filesfromdb:
                    if update:
                        sqlupdate   = True
                        self.picsupdated += 1
                        filesfromdb.pop(filesfromdb.index(filename))
                    else:
                        filesfromdb.pop(filesfromdb.index(filename))
                        continue

                else:
                    sqlupdate  = False
                    self.picsadded   += 1
                    
                picentry = { "idFolder": folderid,
                             "strPath": path,
                             "strFilename": filename,
                             "ftype": extension in self.picture_extensions and "picture" or extension in self.video_extensions and "video" or "",
                             "DateAdded": strftime("%Y-%m-%d %H:%M:%S"),
                             "Thumb": "",
                             "ImageRating": None
                             }


                # get the meta tags. but only for pictures
                try:

                    if extension in self.picture_extensions:
                        (file, isremote) = self.filescanner.getlocalfile(pic)
                        self.log("Scanning file %s"%smart_utf8(file))
                        tags = self._get_metas(smart_unicode(file))
                        picentry.update(tags)

                        # if isremote == True then the file was copied to cache directory.
                        if isremote:
                            self.filescanner.delete(file)
                except Exception,msg:
                    print msg
                    pass

                mpdb.DB_file_insert(path, filename, picentry, sqlupdate)
                
                straction = __language__(30242)#Updating
                if self.scan and self.totalfiles!=0 and self.total_root_entries!=0:
                    self.scan.update(int(100*float(self.picsscanned)/float(self.totalfiles)),#cptscanned-(cptscanned/100)*100,
                                  #cptscanned/100,
                                  int(100*float(self.current_root_entry)/float(self.total_root_entries)),
                                  __language__(30000)+"[%s] (%0.2f%%)"%(straction,100*float(self.picsscanned)/float(self.totalfiles)),#"MyPicture Database [%s] (%0.2f%%)"
                                  filename)
                
        # all pics left in list filesfromdb weren't found in file system.
        # therefore delete them from db
        if filesfromdb:
            for pic in filesfromdb:
                mpdb.DB_del_pic(path, pic)
                self.picsdeleted += 1

        if recursive:
            for dir in dirnames:
                self._addpath(dir, folderid, True, update)


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
                print msg

            ###############################
            #    getting  IPTC  infos     #
            ###############################
            try:
                iptc = self._get_iptc(fullpath)
                picentry.update(iptc)
            except Exception,msg:
                print msg


            ###############################
            #    getting  XMP infos       #
            ###############################
            try:
                xmp = self._get_xmp(fullpath)
                picentry.update(xmp)
            except Exception,msg:
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
                            self.log( "Datetime (%s) did not match for '%s' format... trying an other one..."%(tags[tag].__str__(),datetimeformat), VFSScanner.LOGERROR )
                    if not tagvalue:
                        self.log( "ERROR : the datetime format is not recognize (%s)"%tags[tag].__str__(), VFSScanner.LOGERROR )

                else:
                    tagvalue = tags[tag].__str__()
                try:
                    picentry[tag]=tagvalue
                except Exception, msg:
                    self.log(">> get_exif %s"%picfile , VFSScanner.LOGERROR)
                    self.log( "%s - %s"%(Exception,msg), VFSScanner.LOGERROR )
                    self.log( "~~~~", VFSScanner.LOGERROR )
                    self.log( "", VFSScanner.LOGERROR )
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
                    self.log( "EXCEPTION >> get_iptc %s"%fullpath, VFSScanner.LOGDEBUG )
                    self.log( "%s - %s"%(Exception,msg), VFSScanner.LOGDEBUG )
                    return {}
            else:
                self.log( "EXCEPTION >> get_iptc %s"%fullpath, VFSScanner.LOGDEBUG )
                self.log( "%s - %s"%(Exception,msg), VFSScanner.LOGDEBUG )
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
                    self.log( "%s,%s"%(path,filename) )
                    self.log( "WARNING : type returned by iptc field is not handled :" )
                    self.log( repr(type(info.data[k])) )

            else:
                self.log("IPTC problem with file: %s"%fullpath, VFSScanner.LOGERROR)
                try:
                    self.log( " '%s' IPTC field is not handled. Data for this field : \n%s"%(k,info.data[k][:80]) , VFSScanner.LOGERROR)
                except:
                    self.log( " '%s' IPTC field is not handled (unreadable data for this field)"%k , VFSScanner.LOGERROR)
                self.log( "IPTC data for picture %s will be ignored"%filename , VFSScanner.LOGERROR)
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

