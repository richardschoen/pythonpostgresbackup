#!/QOpenSys/pkgs/bin/python3
#####!/usr/bin/python3
##### IBM i Specific
#####!/QOpenSys/pkgs/bin/python3
#------------------------------------------------
# Script name: pyrestorepostgres.py
#
# Description: 
# This script will run pg_restore to restore a PostgreSQL database backup
#
# Links:
# https://stackoverflow.com/questions/23732900/postgresql-database-backup-using-python
#
# Pip packages needed:
#
# Parameters:
# --action=Action to run 
#   newdb=Database will be created and then restored. Database should not exist yet or error 
#    will get thrown on createdb.
#   overwritedb=Clean and overwrite existing database. Database must already exist or error thrown.
#   restoreasdb=Create new database name and restore backup to the new database.
# --dbname=New database name, existing database name or restore as database name
#   depending on which action was selected.    
# --dbhost=PostgreSQL host name to connect to. Leave blank or omit this parm to use local sockets.
# --dbport=PostgreSQL TCP port connect to. Omit this parm to default to port: 5432.
# --dbuser=PostgreSQL user to connect as. Omit this parm to use "postgres" user as default user.
# --dbpass=PostgreSQL password to use. Omit this parm or pass empty parm if host is blank to use local socket connection.
# --inputfile=Input pb_dump tar backup file to restore from. Ex: /tmp/mybackup.tar
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
rtncmd=0

#Output messages to STDOUT for logging
print(dashes)
print("PostgreSQL Database Restore")
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
      parser.add_argument('-a','--action', required=True,help="Restore action: newdb=database does not exist yet,overwritedb=clean and overwrite existing database,restoreasdb=restore as new name")
      parser.add_argument('-d','--dbname', required=True,help="Database name")
      parser.add_argument('-H','--dbhost', required=False,default="",help="Database host. Blank=use local domain socket")
      parser.add_argument('-p','--dbport', required=False,default=5432,help="Database port")
      parser.add_argument('-U','--dbuser', required=False,default="postgres",help="Database user")
      parser.add_argument('-P','--dbpass', required=False,help="Database pass")
      parser.add_argument('-i','--inputfile', required=True,help="Input pg_dump backup TAR file")
      
      # Parse the command line arguments 
      args = parser.parse_args()
      
      # Set parameter work variables from command line args
      parmscriptname = sys.argv[0] 
      parmaction=args.action.strip().lower()
      parmdbname=args.dbname.strip()
      parmdbport=args.dbport
      parmdbhost=args.dbhost.strip()
      parmdbuser=args.dbuser.strip()
      parmdbpass=args.dbpass.strip()
      # Remove forward slash from password if found 
      # This is in case exclamation in password  
      parmdbpass=parmdbpass.replace("\!","!")   
      parminputfile = args.inputfile.strip()
      print(f"Python script: {parmscriptname}")
      print(f"Database action: {parmaction}")
      print(f"Database host: {parmdbhost}")
      print(f"Database port: {parmdbport}")
      print(f"Database name: {parmdbname}")
      print(f"Database user: {parmdbuser}")
      ##print(f"Database pass: {parmdbpass}")
      print(f"Output file: {parminputfile}")

      # Bail if action is invalid
      if (parmaction != "newdb" and 
          parmaction != "overwritedb" and
          parmaction != "restoreasdb"):
            raise Exception("Action must be: newdb, overwritedb or restoreasdb")

      # Make sure tar backup input file exists. otherwise bail out
      if (os.path.isfile(parminputfile)==False):
            raise Exception(f"INFO:Backup file {parminputfile} does not exist. Restore cancelled.")

      # pg_restore example
      # Restore to original database if not found
      # pg_restore -C -d "postgres" -p 5432 -U postgres --verbose "/tmp/mydatabase.tar"
      # Restore to original database if already existing. Empties first
      # pg_restore -d "mydatabase" -p 5432 -U postgres --clean --verbose "/tmp/mydatabase.tar"
      
      hostswitch=""
      if (trim(parmdbhost)!=""):
         hostswitch=f"-h '{parmdbhost}'"

      # Build restore command line based on parmaction
      
      # Restore as new database with original database name from backup tar file
      # We specify "postgres" as the database since the database does not already 
      # exist. Have user enter database name, but we don't use it for new database
      # since we're restoring
      cmd_pgrestore=""
      cmd_createdb=""
      if (parmaction=="newdb"):
         cmd_createdb=f"createdb {hostswitch} -p {parmdbport} -U {parmdbuser} \"{parmdbname}\""
         cmd_pgrestore=f"pg_restore -d \"{parmdbname}\" {hostswitch} -p {parmdbport} -U {parmdbuser} --verbose  \"{parminputfile}\""
         ## Removed create new empty
         ##cmd_pgrestore=f"pg_restore -C -d \"postgres\" {hostswitch} -p {parmdbport} -U {parmdbuser} --verbose  \"{parminputfile}\""                
      # Clean/clear the existing database and restore the database if it already exists
      elif (parmaction=="overwritedb"):
         cmd_pgrestore=f"pg_restore -d \"{parmdbname}\" {hostswitch} -p {parmdbport} -U {parmdbuser} --clean --verbose  \"{parminputfile}\""
      # Restore as new database name. We also attempt to create the database
      # if db already exists, you should use the "overwritedb" action instead.
      elif (parmaction=="restoreasdb"):
         cmd_createdb=f"createdb {hostswitch} -p {parmdbport} -U {parmdbuser} \"{parmdbname}\""
         cmd_pgrestore=f"pg_restore -d \"{parmdbname}\" {hostswitch} -p {parmdbport} -U {parmdbuser} --verbose  \"{parminputfile}\""

      # Run the createdb command to create database if createdb command line specified
      if (cmd_createdb!=""):
         print("")
         print(f"INFO: Starting createdb for database {parmdbname} - {time.strftime('%H:%M:%S')}")
         # Display command line
         print(cmd_createdb) 
         # Export the PostgreSQL environment variable for password and then Run the command
         rtncmd=os.system(f"export PGPASSWORD={parmdbpass};{cmd_createdb}")
         print(f"INFO: Completed createdb for database {parmdbname} - {time.strftime('%H:%M:%S')}")

         # Check return code
         if (rtncmd != 0):
            raise Exception(f"Error {rtncmd} occurred while running createdb command")

      # Run the pg_restore restore command
      print("")
      print(f"INFO: Starting pg_restore PostgreSQL restore from {parminputfile} - {time.strftime('%H:%M:%S')}")
      # Display command line
      print(cmd_pgrestore) 
      # Export the PostgreSQL environment variable for password and then Run the command
      rtncmd=os.system(f"export PGPASSWORD={parmdbpass};{cmd_pgrestore}")
      print(f"INFO: Completed pg_restore PostgreSQL restore from {parminputfile} - {time.strftime('%H:%M:%S')}")
   
      # Check return code
      if (rtncmd != 0):
         raise Exception(f"Error {rtncmd} occurred while running pg_restore command")

      # Set success info
      exitcode=0
      exitmessage=f"Restore completed successfully to database {parmdbname} from file {parminputfile}"

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

