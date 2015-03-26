#!/bin/bash
#
# This script generates configuration for smokeping.
#
# by Tomas Hlavacek <tomas.hlavacek@ignum.cz>

DEVICE_EXCEPT="router3"
OUTPUT="/etc/smokeping/config.d/TargetsNetOp"

DEBUG=0

BIN_RATLIST="/usr/local/bin/rat-list"
BIN_MV="/bin/mv"
BIN_RM="/bin/rm"
BIN_DIFF="/usr/bin/diff"
BIN_GREP="/bin/grep"
BIN_DATE="/bin/date"
BIN_MKTEMP="/bin/mktemp"
BIN_CHMOD="/bin/chmod"
BIN_RCSMOKEPING="/etc/init.d/smokeping"

debug(){
    if [ -n "${DEBUG}" ] && (( $DEBUG > 0 )); then
        echo "$1"
    fi
}

error(){
    echo "$1" >&2
}


create_conf(){
    OUT="$1"
    H="$2"
    HN="$3"
    T="$4"

    cat >> $OUT <<EOF
++ netop-$HN
menu = $HN
title = $H
host = $H

EOF
}



# main

TMPOUT=`$BIN_MKTEMP`

$BIN_RATLIST | while read L; do
	HN=`echo $L | cut -d" " -f1`
	H=`echo $L | cut -d" " -f2`
	T=`echo $L | cut -d" " -f3`
	A=`echo $L | cut -d" " -f4`
	
	if [ -n "${A}" ] && (( $A > 0 )) && ( [ -z "${DEVICE_EXCEPT}" ] || ! echo $HN | $BIN_GREP -E "$DEVICE_EXCEPT">/dev/null ); then
	    debug "Working on host $HN ($H $B $T)..."
	    create_conf "$TMPOUT" "$H" "$HN" "$T"
	else
	    debug "Host $HN is blocked. Skipping."
	fi
done

if ! $BIN_DIFF $TMPOUT $OUTPUT >/dev/null; then
    debug "Configuration has changed. Activating..."
    $BIN_MV $TMPOUT $OUTPUT
    $BIN_CHMOD 644 $OUTPUT
    $BIN_RCSMOKEPING reload >/dev/null
else
    debug "Configuration unchanged. Removing temporary file(s)."
    $BIN_RM $TMPOUT
fi

exit 0
