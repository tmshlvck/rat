#!/bin/bash
#
# This script download list of VLANS from Cisco routers or switches.
#
# by Tomas Hlavacek <tomas.hlavacek@ignum.cz>

DEVICE="host1.domain.tld"
HOSTNAME="host1"

DEST="/srv/netop/vlans/maude-vlans.txt"
DESTOWN="root:root"
DESTMOD="644"
TFTPROOT="/srv/tftp"
TFTPIP="1.2.3.4"
LOG_FILE="/tmd/host1-vlans-download.log"

DEBUG=0

BIN_RATCOM="/usr/local/bin/rat-com"
BIN_MV="/bin/mv"
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
    DF="$2"
    HN="$3"
    if [ -n "${DF}" ]&&[ -f "${DF}" ]&&[ -s "${DF}" ]; then
	debug "File ${DF} is present."

	debug "Saving ${DF} for device $HN to $DEST."
	$BIN_MV "${DF}" "$DEST"
	$BIN_CHOWN $DESTOWN "$DEST"
	$BIN_CHMOD $DESTMOD "$DEST"
	debug "Done file $CF saved to $DEST."
    else
        error "Error: Expected TFTPed file ${CF} is not present."
    fi
}

download_vlans(){
    H="$1"
    HN="$2"
    CF="vlan.txt-$RANDOM"
    debug "Initiating config copy from $H to file ${TFTPROOT}/${CF}"
    $BIN_RATCOM -c"show vlan | redirect tftp://${TFTPIP}/${CF}" $H >>$LOG_FILE 2>&1

    save_file_to_repo "$H" "${TFTPROOT}/${CF}" "$HN"
}






# main

download_vlans "$DEVICE" "$HOSTNAME"

exit 0

