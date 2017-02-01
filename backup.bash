#!/bin/bash
# backup.bash - backup josé's databases to Google Drive
# need `gdrive` to function

JOSE_BACKUP_DIR="0ByEq2iIt9GXoWVF2YkNuMFMyMU0"
DATE=$(date +%d-%m-%y-%H-%M)
BACKUPFILE="jose-backup-$DATE.tar.gz"

tar cvzf $BACKUPFILE db/* markov-database.json database.db zelao.txt ext/*.db jcoin/*.db jcoin/*.journal jose-data.txt

gdrive upload --parent $JOSE_BACKUP_DIR $BACKUPFILE 


