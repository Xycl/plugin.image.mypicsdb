# -*- coding: utf8 -*-

""" 
Database abstraction layer for Sqlite and MySql
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

ATTENTION:
Needs the following entries in addon.xml
  <requires>
    .......
    <import addon="script.module.myconnpy" version="0.3.2"/>
  </requires>

"""

import xbmc

# Base class used for logging and "advanced" functions
class Database:
    
    DEBUGGING = True
    
    LOGDEBUG = 0
    LOGINFO = 1
    LOGNOTICE = 2
    LOGWARNING = 3
    LOGERROR = 4
    LOGSEVERE = 5
    LOGFATAL = 6
    LOGNONE = 7
    
    def log(msg, level=LOGDEBUG):
        if type(msg).__name__=='unicode':
            msg = msg.encode('utf-8')
        if DEBUGGING:
            xbmc.log(str("MyPicsDB >> %s"%msg.__str__()), level)
            
   def request(sqlrequest):
        try:
            self.execute( sqlrequest )
            retour = self.fetch_all()
            self.commit()
        except Exception,msg:
            self.log( "The request failed :", LOGERROR )
            self.log( "%s - %s"%(Exception,msg), LOGERROR )
            self.log( "SQL Request> %s"%sqlrequest, LOGERROR)
            self.log( "---", LOGERROR )
            retour= []
            
        return retour

    def request_with_binds(sqlrequest, bindVariablesOrg):

        bindVariables = []
        for value in bindVariablesOrg:
            if type(value).__name__ == 'str':
                bindVariables.append(decoder.smart_unicode(value))
            else:
                bindVariables.append(value)
        try:
            self.execute( sqlrequest, bindVariables )
            retour = self.fetch_all()
            self.commit()

        except Exception,msg:
            try:
                self.log( "The request failed :", LOGERROR )
                self.log( "%s - %s"%(Exception,msg), LOGERROR )
            except:
                pass
            try:
                self.log( "SQL RequestWithBinds > %s"%sqlrequest, LOGERROR)
            except:
                pass
            try:
                i = 1
                for var in bindVariables:
                    self.log ("SQL RequestWithBinds %d> %s"%(i,var), LOGERROR)
                    i=i+1
                self.log( "---", LOGERROR )
            except:
                pass
            retour= []
            
        return retour
        
class DBMysql(Database):

    def connect( db_name, db_user, db_pass, db_address, port=3306):
        self.db_name  = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        if db_port: 
            self.db_address = '%s:%s' %(db_address,db_port)
        else:
            self.db_address = db_address

        self.connection = mysql_database.connect(db_address, db_user, db_pass, db_name)
        self.connection.set_charset('utf-8')
        self.connection.set_unicode(True)
        self.cursor = self.connection.cursor()
        
    def execute(self, sql, binds=None):
        if binds is not None:
            sql = sql.replace('?', '%s')
        self.cursor.execute(sql, binds)
        
    def fetch(self):
        for row in self.cursor.fetchall():
            yield row
            
    def fetch_all(self):
        return [row for row in self.cursor.fetchall()]

    def commit(self):
        self.connection.commit()
        
    def disconnect(self):
        self.connection.close()
        
class DBSqlite(Database):

    def connect(self, dbname):
        self.connection = sqlite_database.connect(dbname)
        self.connection.text_factory = unicode
        self.cursor = self.connection.cursor()
        
    def execute(self, sql, binds=None):
        self.cursor.execute(sql, binds)
        
    def fetch(self):
        for row in self.cursor:
            yield row
            
    def fetch_all(self):
        return [row for row in self.cursor]
        
    def commit(self):
        self.connection.commit()
        
    def disconnect(self):
        self.cursor.close()

 

class DBFactory:
    backends = {'mysql':DBMysql, 'sqlite':DBSqlite}

    def __new__(self, backend):

        if backend == 'mysql':
            	import mysql.connector as mysql_database
                
        # default is to use Sqlite
        else:
            try:
                from sqlite3 import dbapi2 as sqlite_database
            except:
                from pysqlite2 import dbapi2 as sqlite_database        
                
        return DBFactory.backends[backend]()
    