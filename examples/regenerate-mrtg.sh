#!/bin/bash

DEBUG=0
MRTGROOT="/var/www/mrtg"
COMM="public"

BIN_RATLIST="/usr/local/bin/rat-list"
BIN_CFGMAKER="/usr/bin/cfgmaker"
BIN_SNMPWALK="/usr/bin/snmpwalk"
BIN_INDEXMAKER="/usr/bin/indexmaker"

debug(){
  if [ -n "${DEBUG}" ] && (( $DEBUG > 0 )); then
    echo "$1"
  fi
}

config() {
HN="$1"
H="$2"

if [ -n "${HN}" ] && [ -n "${H}" ]; then
  if [ ! -d $MRTGROOT/mrtg-$HN ]; then
    debug "Making new directory $MRTGROOT/mrtg-$HN"
    mkdir $MRTGROOT/mrtg-$HN
  fi
  cd $MRTGROOT/mrtg-$HN
  $BIN_CFGMAKER --no-down --ifdesc=alias,catname --global "Options[_]: bits" --snmp-options=:::::2 --global "WorkDir: $MRTGROOT/mrtg-$HN" --output=$HN.cfg ${COMM}@$H >/dev/null 2>&1
#  echo #BIN_CFGMAKER --no-down --ifdesc=alias,catname --global "Options[_]: bits" --snmp-options=:::::2 --global "WorkDir: $MRTGROOT/mrtg-$HN" --output=$HN.cfg ${COMM}@$H

  if $BIN_SNMPWALK -v2c -c $COMM $H .1.3.6.1.4.1.9.9.48.1.1.1.5.1 | grep Gauge >/dev/null; then
    echo >>$HN.cfg
    echo "# CPU Usage" >>$HN.cfg
    echo "Target[${H}_cpu]: .1.3.6.1.4.1.9.2.1.56.0&.1.3.6.1.4.1.9.2.1.56.0:${COMM}@${H}" >>$HN.cfg
    echo "MaxBytes[${H}_cpu]: 100" >>$HN.cfg
    echo "Options[${H}_cpu]: gauge, nopercent, nolegend, transparent, noo" >>$HN.cfg
    echo "Title[${H}_cpu]: CPU Usage -- ${H}" >>$HN.cfg
    echo "PageTop[${H}_cpu]: <H1 align="center">CPU usage -- ${H}</H1>" >>$HN.cfg
    echo "YLegend[${H}_cpu]: CPU Utilization (%)" >>$HN.cfg
    echo "LegendI[${H}_cpu]: CPU Utilization:&nbsp" >>$HN.cfg
    echo "LegendO[${H}_cpu]: CPU Utilization:&nbsp" >>$HN.cfg
    echo "ShortLegend[${H}_cpu]: Percent" >>$HN.cfg
  fi

  if $BIN_SNMPWALK -v2c -c $COMM $H .1.3.6.1.4.1.9.9.48.1.1.1.5.1 | grep Gauge >/dev/null; then
    echo >>$HN.cfg
    echo >>$HN.cfg
    echo "# Memory Usage" >>$HN.cfg
    echo "Target[${H}_mem]: .1.3.6.1.4.1.9.9.48.1.1.1.5.1&.1.3.6.1.4.1.9.9.48.1.1.1.5.2:${COMM}@${H}" >>$HN.cfg
    echo "MaxBytes[${H}_mem]: 4294967296" >>$HN.cfg
    echo "Options[${H}_mem]: gauge, nolegend, nopercent, unknaszero, transparent" >>$HN.cfg
    echo "Title[${H}_mem]: Free Memory, Processor and I/O Pools -- ${H}" >>$HN.cfg
    echo "PageTop[${H}_mem]: <H1 align="center">Free Memory, Processor and I/O Pools -- ${H}</H1>" >>$HN.cfg
    echo "YLegend[${H}_mem]: Free Memory (/bytes)" >>$HN.cfg
    echo "LegendI[${H}_mem]: Processor Pool:&nbsp" >>$HN.cfg
    echo "LegendO[${H}_mem]: I/O Pool:&nbsp" >>$HN.cfg
    echo "ShortLegend[${H}_mem]: Bytes" >>$HN.cfg
    echo >>$HN.cfg
  fi

  if $BIN_SNMPWALK -v2c -c $COMM $H .1.3.6.1.4.1.9.9.273.1.1.2.1.1.1 | grep Gauge >/dev/null; then
    echo >>$HN.cfg
    echo >>$HN.cfg
    echo "# Memory Usage" >>$HN.cfg
    echo "Target[${H}_connc0]: .1.3.6.1.4.1.9.9.273.1.1.2.1.1.1&.1.3.6.1.4.1.9.9.273.1.1.2.1.1.1:${COMM}@${H}" >>$HN.cfg
    echo "MaxBytes[${H}_connc0]: 512" >>$HN.cfg
    echo "Options[${H}_connc0]: gauge, nolegend, nopercent, transparent, noo" >>$HN.cfg
    echo "Title[${H}_connc0]: Active wireless clients on Dot11Radio0 -- ${H}" >>$HN.cfg
    echo "PageTop[${H}_connc0]: <H1 align="center"> Active wireless clients on Dot11Radio0-- ${H}</H1>" >>$HN.cfg
    echo "YLegend[${H}_connc0]: Active wireless clients on Dot11Radio0" >>$HN.cfg
    echo "LegendI[${H}_connc0]: Active wireless clients:&nbsp" >>$HN.cfg
    echo "LegendO[${H}_connc0]: Active wireless clients:&nbsp" >>$HN.cfg
    echo "ShortLegend[${H}_connc0]: Connected clients" >>$HN.cfg
    echo >>$HN.cfg
  fi

  if $BIN_SNMPWALK -v2c -c $COMM $H .1.3.6.1.4.1.9.9.273.1.1.2.1.1.2 | grep Gauge >/dev/null; then
    echo >>$HN.cfg
    echo >>$HN.cfg
    echo "# Memory Usage" >>$HN.cfg
    echo "Target[${H}_connc1]: .1.3.6.1.4.1.9.9.273.1.1.2.1.1.2&.1.3.6.1.4.1.9.9.273.1.1.2.1.1.2:${COMM}@${H}" >>$HN.cfg
    echo "MaxBytes[${H}_connc1]: 512" >>$HN.cfg
    echo "Options[${H}_connc1]: gauge, nolegend, nopercent, transparent, noo" >>$HN.cfg
    echo "Title[${H}_connc1]: Active wireless clients on Dot11Radio1 -- ${H}" >>$HN.cfg
    echo "PageTop[${H}_connc1]: <H1 align="center"> Active wireless clients on Dot11Radio1-- ${H}</H1>" >>$HN.cfg
    echo "YLegend[${H}_connc1]: Active wireless clients on Dot11Radio1" >>$HN.cfg
    echo "LegendI[${H}_connc1]: Active wireless clients:&nbsp" >>$HN.cfg
    echo "LegendO[${H}_connc1]: Active wireless clients:&nbsp" >>$HN.cfg
    echo "ShortLegend[${H}_connc1]: Connected clients" >>$HN.cfg
    echo >>$HN.cfg
  fi


  $BIN_INDEXMAKER --output=index.html $HN.cfg >/dev/null 2>&1
fi
}


$BIN_RATLIST | while read l; do
  HN=`echo $l | cut -d" " -f1`
  H=`echo $l | cut -d" " -f2`
  A=`echo $l | cut -d" " -f4`
  if [ -n "${H}" ] && [ -n "${HN}" ]; then
    if [ -z "${A}" ] || (( $A > 0 )); then
      debug "Configuring $HN..."
      config $HN $H &
    fi
  fi
done

exit 0

