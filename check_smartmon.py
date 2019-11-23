#!/usr/local/bin/python

# -*- coding: iso8859-1 -*-
#
# $Id: version.py 133 2006-03-24 10:30:20Z fuller $
#
# check_smartmon
# Copyright (C) 2006  daemogorgon.net
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program; if not, write to the Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# patches for FreeBSD and SCSI disks: wtps0n@bsdserwis.com

"""Package versioning
"""


import os.path
import sys, re

from subprocess import Popen,PIPE
from optparse import OptionParser


__author__ = "fuller <fuller@daemogorgon.net>"
__version__ = "$Revision$"


# path to smartctl
_smartctlPath = "/usr/local/sbin/smartctl"

# application wide verbosity (can be adjusted with -v [0-3])
_verbosity = 0


def parseCmdLine(args):
        """Commandline parsing."""

        usage = "usage: %prog [options] device"
        version = "%%prog %s" % (__version__)

        parser = OptionParser(usage=usage, version=version)
	parser.add_option("-d", "--device", action="store", dest="device", default="", metavar="DEVICE",
			help="device to check")
        parser.add_option("-v", "--verbosity", action="store",
                        dest="verbosity", type="int", default=0,
                        metavar="LEVEL", help="set verbosity level to LEVEL; defaults to 0 (quiet), \
                                        possible values go up to 3")
        parser.add_option("-t", "--type", action="store", dest="devtype", default="ata", metavar="DEVTYPE",
                        help="type of device (ata|scsi)")
        parser.add_option("-w", "--warning-threshold", metavar="TEMP", action="store",
                        type="int", dest="warningThreshold", default=55,
                        help="set temperature warning threshold to given temperature (defaults to 55)")
        parser.add_option("-c", "--critical-threshold", metavar="TEMP", action="store",
                        type="int", dest="criticalThreshold", default="60",
                        help="set temperature critical threshold to given temperature (defaults to 60)")

        return parser.parse_args(args)
# end


def checkDevice(path):
        """Check if device exists and permissions are ok.
        
        Returns:
                - 0 ok
                - 1 no such device
                - 2 no read permission given
        """

        vprint(3, "Check if %s does exist and can be read" % path)
        if not os.access(path, os.F_OK):
                return (1, "UNKNOWN: no such device found")
        elif not os.access(path, os.R_OK):
                return (2, "UNKNOWN: no read permission given")
        else:
                return (0, "")
        # fi
# end


def checkSmartMonTools(path):
        """Check if smartctl is available and can be executed.

        Returns:
                - 0 ok
                - 1 no such file
                - 2 cannot execute file
        """

        vprint(3, "Check if %s does exist and can be read" % path)
        if not os.access(path, os.F_OK):
                return (1, "UNKNOWN: cannot find %s" % path)
        elif not os.access(path, os.X_OK):
                return (2, "UNKNOWN: cannot execute %s" % path)
        else:
                return (0, "")
        # fi
# end


def callSmartMonTools(path, device):
        # get health status
        cmd = "%s -H %s" % (path, device)
        vprint(3, "Get device health status: %s" % cmd)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        (child_stdout, child_stderr) = (p.stdout, p.stderr)
        line = child_stderr.readline()
        if len(line):
                return (3, "UNKNOWN: call exits unexpectedly (%s)" % line, "",
                                "")
        healthStatusOutput = ""
        for line in child_stdout:
                healthStatusOutput = healthStatusOutput + line
        # done

        # get temperature
        cmd = "%s -A %s" % (path, device)
        vprint(3, "Get device temperature: %s" % cmd)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        (child_stdout, child_stderr) = (p.stdout, p.stderr)
        line = child_stderr.readline()
        if len(line):
                return (3, "UNKNOWN: call exits unexpectedly (%s)" % line, "",
                                "")

        temperatureOutput = ""
        for line in child_stdout:
                temperatureOutput = temperatureOutput + line
        # done

        return (0 ,"", healthStatusOutput, temperatureOutput)
# end


def parseOutput(healthMessage, temperatureMessage, devType):
        """Parse smartctl output

        Returns (health status, temperature).
        """

        vprint(3, "parseOutput: Device type is %s" % devType)

        if devType == "ata":
                # parse health status
                #
                # look for line '=== START OF READ SMART DATA SECTION ==='
                statusLine = ""
                lines = healthMessage.split("\n")
                getNext = 0
                for line in lines:
                        if getNext:
                                if line <> "SMART STATUS RETURN: incomplete response, ATA output registers missing":
                                        statusLine = line
                                        break
                        elif line == "=== START OF READ SMART DATA SECTION ===":
                                getNext = 1
                        # fi
                # done
        
                if getNext:
                        parts = statusLine.split()
                        healthStatus = parts[-1]
                # fi
        
                # parse temperature attribute line
                temperature = 0
                lines = temperatureMessage.split("\n")
                for line in lines:
                        parts = line.split()
                        if len(parts):
                                # 194 is the temperature value id
                                if parts[0] == "194":
                                        temperature = int(parts[9])
                                        break
                                # fi
                        # fi
                # done
        # if devType == ata

        if devType == "scsi":
                stat_re = re.compile( r'SMART Health Status:' )
                lines = healthMessage.split("\n")
                for line in lines:
                        if stat_re.search( line ):
                               parts = line.split()
                               healthStatus = parts[-1]
                               break
                       # fi
                # done

                # get temperature from temperatureMessage
                stat_re = re.compile( r'Current Drive Temperature:' )
                lines = temperatureMessage.split("\n")
                for line in lines:
                        if stat_re.search( line ):
                               parts = line.split()
                               temperature = int(parts[-2])
                               break
                       # fi
                # done
                                
        # if devType == scsi

	vprint(3, "Health status: %s" % healthStatus)
        vprint(3, "Temperature: %d" %temperature)

        return (healthStatus, temperature)
# end

def createReturnInfo(device, healthStatus, temperature, warningThreshold,
                criticalThreshold):
        """Create return information according to given thresholds."""

        # this is absolutely critical!
        if healthStatus not in [ "PASSED", "OK" ]:
                return (2, "CRITICAL: device (%s) does not pass health status" %device)
        # fi

        if temperature > criticalThreshold:
                return (2, "CRITICAL: device (%s) temperature (%d) exceeds critical temperature threshold (%s)|TEMP=%d;%d;%d;" 
			% (device, temperature, criticalThreshold, temperature, warningThreshold, criticalThreshold))
        elif temperature > warningThreshold:
                return (1, "WARNING: device (%s) temperature (%d) exceeds warning temperature threshold (%s)|TEMP=%d;%d;%d;" 
			% (device, temperature, warningThreshold, temperature, warningThreshold, criticalThreshold))
        else:
                return (0, "OK: device (%s) is functional and stable (temperature: %d)|TEMP=%d;%d;%d;" 
			% (device, temperature, temperature, warningThreshold, criticalThreshold))
        # fi
# end


def exitWithMessage(value, message):
        """Exit with given value and status message."""

        print message
        sys.exit(value)
# end


def vprint(level, message):
        """Verbosity print.

        Decide according to the given verbosity level if the message will be
        printed to stdout.
        """

        if level <= verbosity:
                print message
        # fi
# end


if __name__ == "__main__":
        (options, args) = parseCmdLine(sys.argv)
        verbosity = options.verbosity

        vprint(2, "Get device name")
        device = options.device
        vprint(1, "Device: %s" % device)

        # check if we can access 'path'
        vprint(2, "Check device")
        (value, message) = checkDevice(device)
        if value != 0:
                exitWithMessage(3, message)
        # fi

        # check if we have smartctl available
        (value, message) = checkSmartMonTools(_smartctlPath)
        if value != 0:
                exitWithMessage(3, message)
        # fi
        vprint(1, "Path to smartctl: %s" % _smartctlPath)

        # FreeBSD specific - SCSI disks are /dev/da[0-9]
        device_re = re.compile( r'/dev/da[0-9]' )

        # check device type, ATA is default
        vprint(2, "Get device type")
        devtype = options.devtype
        vprint(2, "command line supplied device type is: %s" % devtype)
        if not devtype:
                if device_re.search( device ):
                        devtype = "scsi"
                else:
                        devtype4= "ata"

        vprint(1, "Device type: %s" % devtype)

        # call smartctl and parse output
        vprint(2, "Call smartctl")
        (value, message, healthStatusOutput, temperatureOutput) = callSmartMonTools(_smartctlPath, device)
        if value != 0:
                exitWithMessage(value, message)
        vprint(2, "Parse smartctl output")
        
        (healthStatus, temperature) = parseOutput(healthStatusOutput, temperatureOutput, devtype)
        vprint(2, "Generate return information")
        (value, message) = createReturnInfo(device, healthStatus, temperature,
                        options.warningThreshold, options.criticalThreshold)

        # exit program
        exitWithMessage(value, message)

# fi
