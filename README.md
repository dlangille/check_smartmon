check_smartmon
==============

A python script that wraps over smartctl to provide nagios-friendly output and exit
statuses.

Forked from David Moreau Simard's [check_smartmon](https://github.com/dmsimard/check_smartmon) in order to
work with Python 3.6

check_smartmon.py - Standard script. Most use cases call for this script. I use this script instead of the one provided by [net-mgmt/nagios-check_smartmon](https://www.freshports.org/net-mgmt/nagios-check_smartmon/). That port uses a script from http://ftp.bsdserwis.com/pub/FreeBSD/ports/distfiles/ which is [not-trivially patched](https://svnweb.freebsd.org/ports/head/net-mgmt/nagios-check_smartmon/files/patch-check_smartmon?view=markup) by the port.

check_smartmon_twa - Also a Python script, but specifically for use with a 3Ware RAID card.  I used it like this: `check_smartmon_twa -d 0`, but sadly it will work only for `twa0`; there is on way to specific `twa1` for example.
