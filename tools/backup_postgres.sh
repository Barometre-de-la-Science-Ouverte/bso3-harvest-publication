#!/bin/bash

##-------------------------------------------------------------------------------------------------------------------
# Argument: MOUNTED_ENDPOINT_POSTGRES_BACKUP should be supplied, otherwise it will be /var/lib/postgresql/data is put
# Recommendation: launch a CRON every week to backup the DB.
# Careful: old backups are removed before dumping current backup
# Launch: enter in the postgres pods (kubectl exec -it [POD_ID] -- bash) and run ./df_migration/bash backup_postgres.sh [PATH_TO_DB_DUMP]
# To recover: run : psql -d postgres_db  -U postgres -f [PATH_TO_DB_DUMP]
##-------------------------------------------------------------------------------------------------------------------

##----- 1. File location
#  Check if arguments supplied and put it in MOUNTED_ENDPOINT_POSTGRES_BACKUP
if [ -z "$1" ] || [ $# -eq 0 ]
  then
    echo "No argument supplied"
	MOUNTED_ENDPOINT_POSTGRES_BACKUP="/var/lib/postgresql/data"
  else
    MOUNTED_ENDPOINT_POSTGRES_BACKUP="$1"
fi

TODAY="$(date +'%F')"
DB_DUMP_NAME=db_dump_$TODAY.sql

##----- 2. remove old one
find $MOUNTED_ENDPOINT_POSTGRES_BACKUP -name '*db_dump*' -delete
echo Remove old db dumps in $MOUNTED_ENDPOINT_POSTGRES_BACKUP...

##----- 3. Dump backup
echo Dump backup of postgres_db here : $MOUNTED_ENDPOINT_POSTGRES_BACKUP/$DB_DUMP_NAME ...
pg_dump -U postgres -d postgres_db -f $MOUNTED_ENDPOINT_POSTGRES_BACKUP/$DB_DUMP_NAME
echo Successfully dumped backup of postgres_db here : $MOUNTED_ENDPOINT_POSTGRES_BACKUP/$DB_DUMP_NAME
