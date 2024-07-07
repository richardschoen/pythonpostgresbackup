# Python Postgres Backup Utility
This repository contains a PostgreSQL backup CLI utility written in Python. 
This should work on IBM i or any other platforn.

## Back up PostgreSQL database to TAR file - pybackuppostgres.py
This script will run pg_dump to backup a PostgreSQL database. 

Parameters   
```--dbname```=Database name tp back up.   

```--dbhost```=PostgreSQL host name to connect to. Leave blank or omit this parm to use local sockets.   

```--dbport```=PostgreSQL TCP port connect to. Omit this parm to default to port: 5432.   

```--dbuser```=PostgreSQL user to connect as. Omit this parm to use "postgres" user as default user.   

```--dbpass```=PostgreSQL password to use. Omit this parm or pass empty parm if host is blank to use local socket connection.   

```--outputfile```=Output file for storing the pb_dump tar backup. Ex: /tmp/mybackup.tar   
   Special formatting keywords:   
   ```@@datetime``` or ```@@DATETIME``` - Replace with current date/time. 
   Ex backup of --dbname mydb: /tmp/mydb-@@datetime.tar = /tmp/mydb-yyyymmdd-hhmmss.tar 
   ```@@dbdatetime``` or ```@@DBDATETIME``` - Replace with database name and current date/time. 
   Ex backup of --dbname mydb: /tmp/@@dbdatetime.tar = /tmp/mydb-yyyymmdd-hhmmss.tar   

```--replace```=True=Replace output file. False=Halt if output file already exists.   


### Example backup commands

#### Backup database using local sockets to unique file each time
This example backs up over local sockets connection using the specified port and user with no password.   

```python3 pybackuppostgres.py --dbname=mydb  --dbport=5432 --outputfile=/tmp/mydb-@@datetime.tar  --replace=false```   

#### Backup database using localhost host name to unique file each time
This example backs up over TCP port connection using the specified host name, port, user and password.   

```python3 pybackuppostgres.py --dbname=mydb  --dbport=5432 --outputfile=/tmp/mydb-@@datetime.tar  --replace=false --dbuser=postgres --dbpass=mypassword --dbhost=localhost```   

## Restore PostgreSQL database from TAR file - pyrestorepostgres.py
This script will run pg_restore to restore a PostgreSQL database backup.

Parameters   
```--action```=Action to run 
   **newdb**=Database will be created and then restored. Database should not exist yet or error will get thrown on createdb.
   **overwritedb**=Clean and overwrite existing database. Database must already exist or error thrown.
   **restoreasdb**=Create new database name and restore backup to the new database.   

```--dbname```=New database name, existing database name or restore as database name depending on which action was selected.       

```--dbhost```=PostgreSQL host name to connect to. Leave blank or omit this parm to use local sockets.   

```--dbport```=PostgreSQL TCP port connect to. Omit this parm to default to port: 5432.   

```--dbuser```=PostgreSQL user to connect as. Omit this parm to use "postgres" user as default user.   

```--dbpass```=PostgreSQL password to use. Omit this parm or pass empty parm if host is blank to use local socket connection.   

```--inputfile```=Input pb_dump tar backup file to restore from.    
Ex: /tmp/mybackup.tar


### Example restore commands

#### Restore database as new database with selected new database name
This example of using the --action=newdb switch will create the new database and then restore the database contents. Make sure database does not exist yet when using this option or the createdb command will error out.    

```python3 pyrestorepostgres.py --dbname=mydb  --dbport=5432 --inputfile=/tmp/mydb.tar --dbpass=mypass --dbuser=postgres  --action=newdb```

#### Restore database and overwrite existing database with the embedded --clean option
This example of using the --action=overwritedb will clean/clear and overwrite the existing database from the backup file. The database must already exist or error is thrown.   

```python3 pyrestorepostgres.py --dbname=mydb  --dbport=5432 --inputfile=/tmp/mydb.tar --dbpass=mypass --dbuser=postgres  --action=overwritedb```

#### Restore database and overwrite existing database with the embedded --clean option
This example of using the --action=restoreasdb will create the new database and then restore the database contents as the selected database name. Make sure database does not exist yet when using this option or the createdb command will error out.  

```python3 pyrestorepostgres.py --dbname=mydb2  --dbport=5432 --inputfile=/tmp/mydb.tar --dbpass=mypass --dbuser=postgres  --action=restoreasdb```

