#!/bin/bash

DEBUG=0
MRTGROOT="/var/www/mrtg"

BIN_RATLIST="/usr/local/bin/rat-list"
BIN_MRTG="/usr/bin/mrtg"

debug(){
  if [ -n "${DEBUG}" ] && (( $DEBUG > 0 )); then
    echo "$1"
  fi
}

update() {
  HN="$1"
  H="$2"

  env LANG=C $BIN_MRTG $MRTGROOT/mrtg-$HN/$HN.cfg >/dev/null 2>&1
#  env LANG=C $BIN_MRTG $MRTGROOT/mrtg-$HN/$HN.cfg
}

$BIN_RATLIST | while read l; do
  HN=`echo $l | cut -d" " -f1`
  H=`echo $l | cut -d" " -f2`
  A=`echo $l | cut -d" " -f4`
  if [ -n "${H}" ] && [ -n "${HN}" ]; then
    if [ -z "${A}" ] || (( $A > 0 )); then
      debug "Updating $HN..."
      update $HN $H &
    else
      debug "Skipping $HN..."
    fi
  fi
done

exit 0

