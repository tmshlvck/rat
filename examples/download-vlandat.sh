#!/bin/bash
#
# This script download vlan.dat files from Cisco routers or switches.
#
# by Tomas Hlavacek <tomas.hlavacek@ignum.cz>

DEVICE1="host1.domain.tld"
HOSTNAME1="host1"
SRC1="cat4000_flash:/vlan.dat"

DEVICE2="host2.domain.tld"
HOSTNAME2="host2"
SRC2="cat4000_flash:/vlan.dat"

REPO="/srv/ratvlans"
REPOOWN="root:root"
REPOMOD="644"
TFTPROOT="/srv/tftp"
TFTPIP="1.2.3.4"
LOG_FILE="/tmp/vlan-download.log"

DEBUG=0

BIN_RATCOM="/usr/local/bin/rat-com"
BIN_MV="/bin/mv"
BIN_RM="/bin/rm"
BIN_GIT="/usr/bin/git"
BIN_CHOWN="/bin/chown"
BIN_CHMOD="/bin/chmod"
BIN_DATE="/bin/date"

debug(){
  echo "$BIN_DATE : $1" >>$LOG_FILE

  if [ -n "${DEBUG}" ] && (( $DEBUG > 0 )); then
    echo "$1"
  fi
}

error(){
    echo "$BIN_DATE : $1" >>$LOG_FILE
    echo "$1" >&2
}

save_file_to_repo(){
    H="$1"
    CF="$2"
    if [ -n "${CF}" ]&&[ -f "${CF}" ]&&[ -s "${CF}" ]; then
	debug "File ${CF} is present."

	T="${REPO}/${H}-vlan.dat-`$BIN_DATE +%Y-%m-%d-%H-%M`"
	debug "Saving vlan.dat for device $HN to $T."
	$BIN_MV "${CF}" "$T"
	$BIN_CHOWN $REPOOWN "$T"
	$BIN_CHMOD $REPOMOD "$T"
	debug "Done file $CF saved to $T for host $H."
    else
        error "Error: Expected TFTPed file ${CF} is not present."
    fi
}

download_ios_vlan(){
    H="$1"
    HN="$2"
    SRC="$3"
    CF="$HN-vlan.dat-$RANDOM"
    debug "Initiating config copy from $H to file ${TFTPROOT}/${CF}"
    $BIN_RATCOM -c"copy $SRC tftp://${TFTPIP}/${CF}" $H >>$LOG_FILE 2>&1

    save_file_to_repo "$H" "${TFTPROOT}/${CF}"
}






# main

download_ios_vlan "$DEVICE1" "$HOSTNAME1" "$SRC1"
download_ios_vlan "$DEVICE2" "$HOSTNAME2" "$SRC2"

exit 0

