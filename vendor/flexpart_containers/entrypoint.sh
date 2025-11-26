#!/bin/bash
# By MB
# run FLEXPART, but provide a bit of information

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
report() {
    if [ $? -eq 0 ]; then
        printf "%-68s[$GREEN%10s$NC]\n" "$@" "OK"
        return 0
    else
        printf "%-68s[$RED%10s$NC]\n" "$@" "FAILED"
        return 1
    fi
}

echo "Welcome, running FLEXPART "
test -e /pathnames
report "Using defaults (/pathnames)"
cat /pathnames
echo "Mount volumes to change inputs"
echo "Git: $COMMIT"
echo "EXECUTING FLEXPART"
if [ $# -eq 1 ]; then
    test -e /src/"$1"
    report "Executing: /src/$1"
    if [ $? -eq 0 ]; then
        /src/"$1" /pathnames
    else
        test -e "$1"
        report "Executing: $1"
        if [ $? -eq 0 ]; then
            exec "$1"
        fi
    fi

elif [ $# -eq 2 ]; then
    test -e /src/"$1"
    report "Executing: /src/$1 $2"
    if [ $? -eq 0 ]; then
        /src/"$1" "$2"
    fi
else
    test -e /src/FLEXPART_ETA
    report "Executing: /src/FLEXPART_ETA"
    /src/FLEXPART_ETA /pathnames
fi
echo "FINISHED"
