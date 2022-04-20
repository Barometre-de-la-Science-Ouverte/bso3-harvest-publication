#!/bin/bash
## Argument MOUNTED_ENDPOINT_POSTGRES_BACKUP has to be supplied, else the standard value /var/lib/postgresql/data is put
## MOUNTED_ENDPOINT_POSTGRES_BACKUP = /var/lib/postgresql/data
## The idea would be to launch a CRON every week to backup the DB, but it needs to remove the previous backup... Which is not
## done yet in this script.

## Check if arguments supplied
if [ -z "$1" ] || [ $# -eq 0 ]
  then
    echo "No argument supplied"
	MOUNTED_ENDPOINT_POSTGRES_BACKUP="/var/lib/postgresql/data"
  else
    MOUNTED_ENDPOINT_POSTGRES_BACKUP="$1"
fi

echo $MOUNTED_ENDPOINT_POSTGRES_BACKUP

TODAY="$(date +'%F')"
DB_DUMP_NAME=db_dump_$TODAY.sql
echo $DB_DUMP_NAME
echo $MOUNTED_ENDPOINT_POSTGRES_BACKUP/$DB_DUMP_NAME

pg_dump -U postgres -d postgres_db -f $MOUNTED_ENDPOINT_POSTGRES_BACKUP/$DB_DUMP_NAME

# To read the db dump :
# CREATE DATABASE targetdb;
# psql -U postgres -d targetdb -f $DB_DUMP_NAME