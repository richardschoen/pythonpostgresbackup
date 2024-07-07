#!/QOpenSys/pkgs/bin/python3
######!/usr/bin/python3
##### IBM i Specific
#####!/QOpenSys/pkgs/bin/python3
#------------------------------------------------
# Script name: pybackuppostgres.py
#
# Description: 
# This script will run pg_dump to backup a PostgreSQL database. 
#
# Links:
# https://stackoverflow.com/questions/23732900/postgresql-database-backup-using-python
#
# Pip packages needed:
#
# Parameters:
# --dbname=Database name to back up.
# --dbhost=PostgreSQL host name to connect to. Leave blank or omit this parm to use local sockets.
# --dbport=PostgreSQL TCP port connect to. Omit this parm to default to port: 5432.
# --dbuser=PostgreSQL user to connect as. Omit this parm to use "postgres" user as default user.
# --dbpass=PostgreSQL password to use. Omit this parm or pass empty parm if host is blank to use local socket connection.
# --outputfile=Output file for storing the pb_dump tar backup. Ex: /tmp/mybackup.tar
#   Special formatting keywords:
#   @@datetime or @@DATETIME - Replace with current date/time. 
#   Ex backup of --dbname mydb: /tmp/mydb-@@datetime.tar = /tmp/mydb-yyyymmdd-hhmmss.tar 
#   @@dbdatetime or @@DBDATETIME - Replace with database name and current date/time. 
#   Ex backup of --dbname mydb: /tmp/@@dbdatetime.tar = /tmp/mydb-yyyymmdd-hhmmss.tar 
# --replace=True=Replace output file. False=Halt if output file already exists.
#------------------------------------------------

#------------------------------------------------
# Imports and Environment setup
#------------------------------------------------
from distutils.util import * 
import sys
from sys import platform
import collections
import os
import os.path
import time
import traceback
import argparse
import re
from pathlib import Path
from datetime import date
import datetime

#------------------------------------------------
# Script initialization
#------------------------------------------------

# Initialize or set variables
exitcode=0 #Init exitcode
exitmessage=''
parmsexpected=5;
dashes="-------------------------------------------------------------------------------"
outputtype=""

#Output messages to STDOUT for logging
print(dashes)
print("PostgreSQL Database Backup")
print(f"Start of Main Processing -  {time.strftime('%H:%M:%S')}")
print("OS:" + platform)

#------------------------------------------------
# Define some useful functions
#------------------------------------------------

def str2bool(strval):
    #-------------------------------------------------------
    # Function: str2bool
    # Desc: Constructor
    # :strval: String value for true or false
    # :return: Return True if string value is" yes, true, t or 1
    #-------------------------------------------------------
    return strval.lower() in ("yes", "true", "t", "1")

def trim(strval):
    #-------------------------------------------------------
    # Function: trim
    # Desc: Alternate name for strip
    # :strval: String value to trim. 
    # :return: Trimmed value
    #-------------------------------------------------------
    return strval.strip()

def rtrim(strval):
    #-------------------------------------------------------
    # Function: rtrim
    # Desc: Alternate name for rstrip
    # :strval: String value to trim. 
    # :return: Trimmed value
    #-------------------------------------------------------
    return strval.rstrip()

def ltrim(strval):
    #-------------------------------------------------------
    # Function: ltrim
    # Desc: Alternate name for lstrip
    # :strval: String value to ltrim. 
    # :return: Trimmed value
    #-------------------------------------------------------
    return strval.lstrip()

#------------------------------------------------
# Main script logic
#------------------------------------------------
try: # Try to perform main logic

      # Set up the command line argument parsing.
      # If the parse_args function fails, the program will
      # exit with an error 2. In Python 3.9, there is 
      # an argument to prevent an auto-exit
      # Each argument has a long and short version
      parser = argparse.ArgumentParser()
      parser.add_argument('-d','--dbname', required=True,help="Database name")
      parser.add_argument('-H','--dbhost', required=False,default="",help="Database host. Blank=use local domain socket")
      parser.add_argument('-p','--dbport', required=False,default=5432,help="Database port")
      parser.add_argument('-U','--dbuser', required=False,default="postgres",help="Database user")
      parser.add_argument('-P','--dbpass', required=False,default="",help="Database pass")
      parser.add_argument('-o','--outputfile', required=True,help="Output TAR file")
      parser.add_argument('-r','--replace',default="False",required=False,help="True=Replace output file,False=Append if --haltexists=False or Halt if --haltexists=True. Default=False")
      
      # Parse the command line arguments 
      args = parser.parse_args()
      
      # Set parameter work variables from command line args
      parmscriptname = sys.argv[0] 
      parmdbname =args.dbname.strip()
      parmdbport =args.dbport
      parmdbhost =args.dbhost.strip()
      parmdbuser =args.dbuser.strip()
      parmdbpass =args.dbpass.strip()
      # Remove forward slash from password if found 
      # This is in case exclamation in password  
      parmdbpass=parmdbpass.replace("\!","!")   
      parmoutputfile = args.outputfile.strip()
      parmreplace=str2bool(args.replace)
      # Add special values to output file name if specified
      parmoutputfile=parmoutputfile.replace("@@datetime",time.strftime('%Y%m%d-%H%M%S'))
      parmoutputfile=parmoutputfile.replace("@@DATETIME",time.strftime('%Y%m%d-%H%M%S'))
      parmoutputfile=parmoutputfile.replace("@@dbdatetime",parmdbname + "-" + time.strftime('%Y%m%d-%H%M%S'))
      parmoutputfile=parmoutputfile.replace("@@DBDATETIME",parmdbname + "_" + time.strftime('%Y%m%d-%H%M%S'))
      print(f"Python script: {parmscriptname}")
      #print(f"Connection string: {parmconnstring}")
      print(f"Database host: {parmdbhost}")
      print(f"Database port: {parmdbport}")
      print(f"Database name: {parmdbname}")
      print(f"Database user: {parmdbuser}")
      print(f"Database pass: {parmdbpass}")
      print(f"Output file: {parmoutputfile}")
      print(f"Replace: {parmreplace}")
      filealreadyexists=False

      # Replace file
      filealreadyexists=False  
      if os.path.isfile(parmoutputfile):
         if parmreplace==True:
            os.remove(parmoutputfile)
            print(f"INFO:Existing backup file {parmoutputfile} deleted before processing.")
         else:
            # File exists, exit program
            raise Exception(f'Output file {parmoutputfile} already exists and replace not selected. Process cancelled.')

      # pg_dump example
      # pg_dump -F t -d mydatabase -p 5432 -U postgres --verbose > /tmp/mydatabase.tar      
      # Build pg_dump command line
      # cmd_pgdump=f"pg_dump -F t -d {parmdbname} -h '{parmdbhost}' -p {parmdbport} -U {parmdbuser} --verbose > {parmoutputfile}"
      hostswitch=""
      if (trim(parmdbhost)!=""):
         hostswitch=f"-h '{parmdbhost}'"
          
      cmd_pgdump=f"pg_dump -F t -d {parmdbname}  {hostswitch} -p {parmdbport} -U {parmdbuser} --verbose > {parmoutputfile}"
      # Build tar verify command line
      cmd_verifytar=f"tar -tvf {parmoutputfile}"

      # Run the pg_dump backup command
      print("")
      print(f"INFO: Starting pg_dump PostgreSQL backup to {parmoutputfile} - {time.strftime('%H:%M:%S')}")
      # Set password env var and pg_dump command line.
      print(cmd_pgdump) 
      # Run the command
      rtncmd=os.system(f"export PGPASSWORD={parmdbpass};{cmd_pgdump}")
      print(f"INFO: Completed pg_dump PostgreSQL backup to {parmoutputfile} - {time.strftime('%H:%M:%S')}")
   
      # Check return code
      if (rtncmd != 0):
         
         # If output file was created and is 0 bytes. Remove it
         if os.path.isfile(parmoutputfile):
            file_stats = os.stat(parmoutputfile)
            if (file_stats.st_size==0):
               os.remove(parmoutputfile)
               print(f"INFO:Removed 0 byte backup file {parmoutputfile} after processing.")

         raise Exception(f"Error {rtncmd} occurred while running pg_dump")

      # Run the tar verify command
      print("")
      print(f"INFO: Starting tar file verify for {parmoutputfile} - {time.strftime('%H:%M:%S')}")
      print(cmd_verifytar)
      # Run the command
      rtnverify=os.system(cmd_verifytar)
      print(f"INFO: Completed tar file verify for {parmoutputfile} - {time.strftime('%H:%M:%S')}")
   
      # Check return code
      if (rtnverify != 0):
         raise Exception(f"Error {rtnverify} occurred while verifying backup tar file {parmoutputfile}")

      # Set success info
      exitcode=0
      exitmessage=f"Backup of database {parmdbname} completed successfully to output tar file {parmoutputfile}"

#------------------------------------------------
# Handle Exceptions
#------------------------------------------------
# System Exit occurred. Most likely from argument parser
except SystemExit as ex:
     exitcode=ex.code # set return code for stdout
     exitmessage=str(ex) # set exit message for stdout

except argparse.ArgumentError as exc:
     exitcode=99 # set return code for stdout
     exitmessage=str(exc) # set exit message for stdout
     print('Traceback Info') # output traceback info for stdout
     traceback.print_exc()      
     sys.exit(99)

except Exception as ex: # Catch and handle exceptions
     exitcode=99 # set return code for stdout
     exitmessage=str(ex) # set exit message for stdout
     print('Traceback Info') # output traceback info for stdout
     traceback.print_exc()        
     sys.exit(99)
#------------------------------------------------
# Always perform final processing
#------------------------------------------------
finally: # Final processing
     # Do any final code and exit now
     # We log as much relevent info to STDOUT as needed
     print("")
     print(dashes)
     print('ExitCode:' + str(exitcode))
     print('ExitMessage:' + exitmessage)
     print(f"End of Main Processing -  {time.strftime('%H:%M:%S')}")
     print(dashes)

     # Exit the script now
     sys.exit(exitcode) 

