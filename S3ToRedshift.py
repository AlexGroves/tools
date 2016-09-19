import ConfigParser
import argparse
import datetime as dt
from pytz import timezone
import pytz

from S3ToRedshiftUtil import S3ToRS

# ________________________________________________________________________
def PrintOutput(outputString):
    """
        Prints progress as we move along the script.
    """

    nowUtc = dt.datetime.now(tz=pytz.utc)
    nowPt = nowUtc.astimezone(timezone('US/Pacific'))
    nowPtStr = str(nowPt)

    if isinstance(outputString, Exception):
        print 'ERROR: ' + repr(outputString)

    else:
        print '--> ' + nowPtStr + ': ' + outputString

# ________________________________________________________________________
def S3ToRedshift(config, fileName, tableName):
    """
        Takes the list of data files (dataFiles) and puts them in s3.
        This script assumes that the columns of the table are static: it will
        throw an error if something is amiss. All columns are assumed to be 
        surrounded by quotes, and delimited by pipes (|).
    """

    awsConnectionArgs = {'dbname': config.get('AWS', 'dbname'),
                         'user': config.get('AWS', 'user'),
                         'pwd': config.get('AWS', 'pwd'),
                         'host': config.get('AWS', 'host'),
                         'port': int(config.get('AWS', 'port'))}

    schema = config.get('AWS', 'schema')
    awsAccountId = config.get('AWS', 'accountId')
    awsRole = config.get('AWS', 'role')
    s3Location = config.get('AWS', 's3Location')

    rs = S3ToRS(awsAccountId, awsRole, awsConnectionArgs,
                schema, s3Location)

    try:
        rs.TableFill(fileName, tableName)
        PrintOutput(tableName + ' filled successfully.')

    except Exception as err:
        PrintOutput(tableName + ' update failed.')
        PrintOutput(err)

    rs.CloseConnection()


# ________________________________________________________________________
# ________________________________________________________________________
if __name__ == "__main__":

    # Initialize config variables.
    description = "Moves data from s3 to Redshift."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--configFileName", dest="configFileName",
                        required=True,
                        help="Name of config file to be used.")
    parser.add_argument("--tableName", dest="tableName",
                        required=True,
                        help="Name of the table to be copied from S3.")
    parser.add_argument("--fileName", dest="fileName",
                        required=True,
                        help="Name of the file to be copied from S3.")

    args = vars(parser.parse_args())

    configFileName = args['configFileName']
    config = ConfigParser.ConfigParser()
    config.read(configFileName)
    
    fileName = args['fileName']
    tableName = args['tableName']

    S3ToRedshift(config, fileName, tableName)
