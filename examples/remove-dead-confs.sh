#!/bin/bash

CONFDIR="/srv/ratconfigs"

BIN_RATLIST="/usr/local/bin/rat-list"
BIN_GREP="/bin/grep"
BIN_SED="/bin/sed"
BIN_GIT="/usr/bin/git"


SWLIST=`$BIN_RATLIST -q`

cd $CONFDIR
for f in *; do
  if ! echo "$f" | grep -E "^\.">/dev/null; then
    DEVNAME=`echo "$f" | $BIN_SED 's/-confg//'`
    if ! echo "$SWLIST" | $BIN_GREP -E "^$DEVNAME$">/dev/null; then
#      echo "File $f is going to be removed."
      $BIN_GIT rm $f >/dev/null
      $BIN_GIT commit -m "delete non-existent switch $f" >/dev/null
    fi
#  else
#    echo "Ignoring file $f"
  fi
done

