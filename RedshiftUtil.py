import pandas as pd
import psycopg2 as psgsDB
import ConfigParser


# ______________________________________________________________________________
class RedshiftObject(object):

    def __init__(self, configDic={}):

        if len(configDic) == 0:

            config = ConfigParser.ConfigParser()
            config.read('ConfigFile.ini')

            self.password = config.get('AWS', 'password')
            self.user = config.get('AWS', 'user')
            self.host = config.get('AWS', 'host')
            self.port = config.get('AWS', 'port')
            self.dbname = config.get('AWS', 'dbname')

        else:
            self.password = configDic['password']
            self.user = configDic['user']
            self.host = configDic['host']
            self.port = configDic['port']
            self.dbname = configDic['dbname']

    def Query(self, sqlCommand, results=True):
        try:
            con = psgsDB.connect(dbname=self.dbname,
                                 host=self.host,
                                 port=self.port,
                                 user=self.user,
                                 password=self.password)
        except:
            print "Did not connect to Redshift."

        # Redshift query.
        with con:

            df = pd.read_sql_query(sqlCommand, con)
            if results:
                return df
