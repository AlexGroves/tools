# flake8: noqa

import psycopg2
import datetime as dt
from pytz import timezone
import pytz


class S3ToRS(object):
    """
    This object can build and/or fill tables in Redshift using table ddl files
    from s3.

    Inputs (when initializing):
          awsAccountId = just that.
               awsRole = similarly.
        connectionArgs = dictionary of database name, user, password, host,
                         port.
                            {'dbname' : 'database name',
                               'user' : 'user',
                                'pwd' : 'password',
                               'host' : '...redshift.amazonaws.com',
                               'port' : port number}
             delimiter = the method of delimiting the data in the s3 files.
                         Default delimiter is pipe (|).

    Output:
        Newly defined tables in Redshift if they do not yet exist, and data
        appended on these tables. DDL files when new tables are created.
    _____________________________________________________________________________________________________________________
    """

    def __init__(self, awsAccountId, awsRole, connectionArgs,
                 schema, s3Location, delimiter='|'):

        self.schema = schema

        self.accountId = awsAccountId
        self.role = awsRole
        self.delimiter = delimiter
        self.s3Location = s3Location

        try:
            connectStr = "host='{host:s}' dbname='{dbname:s}' " \
                         "user='{user:s}' password='{pwd:s}' " \
                         "port='{port:d}'".format(**connectionArgs)
            self.con = psycopg2.connect(connectStr)

        except Exception:
            nowUtc = dt.datetime.now(tz=pytz.utc)
            nowPt = nowUtc.astimezone(timezone('US/Pacific'))

            logUpdate = "No luck. Could not connect to the database"
            print '--> ' + nowPt + ': ' + logUpdate

    # ________________________________________________________________________
    def PrintOutput(self, outputString):
        nowUtc = dt.datetime.now(tz=pytz.utc)
        nowPt = nowUtc.astimezone(timezone('US/Pacific'))
        nowPtStr = str(nowPt)

        if isinstance(outputString, Exception):
            print 'ERROR: ' + repr(outputString)

        else:
            print '--> ' + nowPtStr + ': ' + outputString

    # _________________________________________________________________________
    def TableCreate(self, tableName, ddlLocation):
        """
        Creates a table in Redshift if it does not already exist.

        Input:
            table = table name
            ddlLocation = location in which the ddl files will be saved. Can
                          either be the local folder or somewhere else as
                          defined in the .ini file.
        """

        con = self.con

        cur = con.cursor()

        self.PrintOutput(tableName)

        # Check if the table already exists. If it doesn't, create it.
        existenceCommand = """
            SELECT
                SUM(CASE WHEN table_name = '{0}' THEN 1 ELSE 0 END)
            FROM
                information_schema.tables
            WHERE
                table_schema = '""" + self.schema + "';"
        existenceCommand = existenceCommand.format(tableName)

        cur.execute(existenceCommand)
        exists = cur.fetchone()[0]

        if exists:
            self.PrintOutput(tableName + ' already exists.')

        else:
            try:
                self.PrintOutput(tableName + ' does not exist yet.')

                # open and read ddl file.
                fileName = ddlLocation + self.schema + '_' + tableName + '.sql'
                ddl = open(fileName, 'rb')
                sqlCommand = ddl.read(sqlCommand)
                ddl.close()

                # Create table.
                cur.execute(sqlCommand)
                self.PrintOutput(tableName + ' created successfully.')

            except Exception as err:
                self.PrintOutput(tableName + ' creation failed.')
                self.PrintOutput(err)

        cur.close()

    # _________________________________________________________________________
    def TableFill(self, fileName, tableName, dateFormat=None):
        """
        Takes the data in a compressed table text file in s3 and inserts it
        into the corresponding RedShift table.  This assumes that the file
        name in s3 will be: tableName_date.txt.gz
        (ex: events_2032-01-01.txt.gz).

        Input:
                    self = for the connection to Redshift.
               tableName = name of the table to insert.
             self.apiKey = just that.
          self.apiSecret = similarly.
          self.delimiter = the method used to separate the data. .
        """

        con = self.con
        delimiter = self.delimiter

        cur = con.cursor()

        awsKeyAndSecret = {'accountId': self.accountId,
                           'role': self.role}

        fullS3Path = self.s3Location + fileName
        copy = "COPY " + self.schema + "." + tableName + " from '" + fullS3Path
        # credentials = "' credentials 'aws_access_key_id={0};" \
        #     + "aws_secret_access_key={1}' \n"
        credentials = "' credentials 'aws_iam_role=arn:aws:iam::{accountId}:role/{role}'\n"
        credentials = credentials.format(**awsKeyAndSecret)

        delimiterStr = "delimiter '" + delimiter + "' escape \n"
        zipStr = "gzip NULL AS 'NULL' \nTRUNCATECOLUMNS;"

        if dateFormat:
            dateFormatStr = "TIMEFORMAT AS '{0}' \n".format(dateFormat)
            pgCommand = copy + credentials + dateFormatStr \
                + delimiterStr + zipStr

        else:
            pgCommand = copy + credentials + delimiterStr + zipStr

        try:
            cur.execute(pgCommand)
            con.commit()
            self.PrintOutput('Filled ' + tableName)

        except Exception as err:
            self.PrintOutput('Did not fill ' + tableName)
            self.PrintOutput(err)

        cur.close()

    # _________________________________________________________________________
    def CloseConnection(self):
        self.con.close()
