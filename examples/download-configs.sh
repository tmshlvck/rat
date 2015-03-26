#!/bin/bash
#
# This script download configs from Cisco and HP routers and switches and
# saves them in GIT repo.
#
# by Tomas Hlavacek <tomas.hlavacek@ignum.cz>

DEBUG=0
DEVICE_EXCEPT=""
ACCEPT_TYPE='^(ios|nxos|procurve|ironware)$'
REPO="/srv/netconfigs"
REPOOWN="root:root"
REPOMOD="644"
TFTPROOT="/srv/tftp"
TFTPIP="1.2.3.4"
LOG_FILE="/tmp/config-download.log"
RAT_TIMEOUT=60

MAX_DOWNLOAD_RETRIES=3

BIN_RATLIST="/usr/local/bin/rat-list"
BIN_RATCOM="/usr/local/bin/rat-com"
BIN_MV="/bin/mv"
BIN_RM="/bin/rm"
BIN_DIFF="/usr/bin/diff"
BIN_GIT="/usr/bin/git"
BIN_CHOWN="/bin/chown"
BIN_CHMOD="/bin/chmod"
BIN_GREP="/bin/grep"
BIN_TR="/usr/bin/tr"
BIN_DATE="/bin/date"

debug(){
    echo "`$BIN_DATE` : $1" >>$LOG_FILE

    if [ -n "${DEBUG}" ] && (( $DEBUG > 0 )); then
        echo "$1"
    fi
}

error(){
    echo "`$BIN_DATE` : $1" >>$LOG_FILE
    echo "$1" >&2
}

save_file_to_repo(){
    H="$1"
    CF="$2"

    if [ -n "${CF}" ]&&[ -f "${CF}" ]&&[ -s "${CF}" ]; then
	debug "File ${CF} is present."
	
	# normalize file (Cisco sux with " -> 0x03 char)
	$BIN_TR '\3' '"' <"${CF}" >"${CF}-n"
	$BIN_RM "${CF}"
	CF="${CF}-n"
	
	# drop changes of ntp clock-period which recalculates automatically
	# drop changes of L2TPv3 passwords which recalculates automatically
	# drop changes in all whole-line comments

	if [ ! -f "${REPO}/${H}-confg" ]  || ! $BIN_DIFF -I "^ntp clock-period" -I "^ *password 7" -I "^ *!" "${CF}" "${REPO}/${H}-confg" >/dev/null; then
	    debug "Config for device $HN has changed."
	    $BIN_MV "${CF}" "${REPO}/${H}-confg"
	    $BIN_CHOWN $REPOOWN "${REPO}/${H}-confg"
	    $BIN_CHMOD $REPOMOD "${REPO}/${H}-confg"
	    cd $REPO
	    $BIN_GIT add . >/dev/null
	    $BIN_GIT commit -a -m "Automatic commit after a change in $H config." >/dev/null
	    debug "Done file $CF for host $H."
	else
	    debug "Config for device $HN is unchanged."
	    $BIN_RM "${CF}"
	    debug "Done file $CF for host $H."
	fi
    else
	error "Error: Expected TFTPed file ${CF} is not present."
    fi
}

attempt_download_conf(){
    H="$1"
    CF="$2"
    T="$3"

    if echo $T | $BIN_GREP "^procurve$">/dev/null; then
      c="copy running-config tftp ${TFTPIP} ${CF}"
    elif echo $T | $BIN_GREP "^nxos$">/dev/null; then
      c="copy run tftp://${TFTPIP}/${CF} vrf default"
    elif echo $T | $BIN_GREP "^ironware$">/dev/null; then
      c="copy run tftp ${TFTPIP} ${CF}"
    else # Cisco + generic
      c="copy run tftp://${TFTPIP}/${CF}"
    fi

    debug "Initiating config copy from $H to file ${CF} with command $c"
    $BIN_RATCOM -o $RAT_TIMEOUT -c"$c" $H >>$LOG_FILE 2>&1
    sleep 10
}

download_conf(){
    H="$1"
    HN="$2"
    T="$3"

    CF="$HN-$RANDOM"

    TRY=0
    while (( $TRY < $MAX_DOWNLOAD_RETRIES )); do
	debug "Attempt $TRY to download config from $H to ${TFTPROOT}/${CF}".
	attempt_download_conf "$H" "$CF" "$T"
	    
	if [ -n "${TFTPROOT}/${CF}" ]&&[ -f "${TFTPROOT}/${CF}" ]&&[ -s "${TFTPROOT}/${CF}" ]; then
	    save_file_to_repo "$H" "${TFTPROOT}/${CF}"
	    break
	else
	    debug "Failed to download config from host $H to file $CF ."
	fi

	TRY=$(( $TRY + 1 ))
    done

    if (( $TRY == $MAX_DOWNLOAD_RETRIES )); then
	error "Failed to download config from host $H to file $CF after $MAX_DOWNLOAD_RETRIES retries."
    fi
}








# main
$BIN_RATLIST | while read L; do
	HN=`echo $L | cut -d" " -f1`
	H=`echo $L | cut -d" " -f2`
	T=`echo $L | cut -d" " -f3`
	A=`echo $L | cut -d" " -f4`
	
	if [ -n "${A}" ] && (( $A > 0 )) && ( [ -z "${DEVICE_EXCEPT}" ] || ! echo $HN | $BIN_GREP -E "$DEVICE_EXCEPT">/dev/null ); then
		if echo $T | $BIN_GREP -E "$ACCEPT_TYPE">/dev/null; then
			debug "Working on host $HN ($H $T)..."
			download_conf "$H" "$HN" "$T" &
		else
			debug "Skipping host $HN of unacceptable type ($H $B $T)..."
		fi
	else
		debug "Host $HN is blocked. Skipping."
	fi
done

exit 0
