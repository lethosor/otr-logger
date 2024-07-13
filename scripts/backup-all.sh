#!/bin/bash

set -e

DATA_DIR="$1"
BACKUP_DIR="$2"

if [[ -z "$DATA_DIR" ]] || [[ -z "$BACKUP_DIR" ]]; then
    echo "usage: $0 DATA_DIR BACKUP_DIR"
    exit 2
fi

backup_filename="$(realpath "$BACKUP_DIR")/backup-$(date +'%Y%m%d-%H%M%S').tar.bz2"
if [[ -f "$backup_filename" ]]; then
    echo "fatal: backup file already exists: ${backup_filename}"
    exit 1
fi

cd "$DATA_DIR"
tar cjf "$backup_filename" .
echo "created: ${backup_filename}"
