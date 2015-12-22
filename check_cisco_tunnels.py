#!/usr/bin/env python
###############################################################
#  ========================= INFO ==============================
# NAME:         check_cisco_tunnels.py
# AUTHOR:       Jeffrey Wolak
# LICENSE:      MIT
# ======================= SUMMARY ============================
# Checks SNMP ifDesc for all "Tunnel" interfaces and checks
# the operational status
#
# Returns OK if all tunnels are up
#
# =================== SUPPORTED DEVICES =======================
#
# ========================= NOTES =============================
# 12-21-2015: Initial version
#
# ======================= LICENSE =============================
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# ###############################################################
import netsnmp   # Requires net-snmp compiled with python bindings
import sys       # exit
import getopt    # for parsing options
import logging   # for debug option
import re        # pattern match

# Global program variables
__program_name__ = 'Cisco Tunnels'
__version__ = 1.0


###############################################################
#
# Exit codes and status messages
#
###############################################################
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3


def exit_status(x):
    return {
        0: 'OK',
        1: 'WARNING',
        2: 'CRITICAL',
        3: 'UNKNOWN'
    }.get(x, 'UNKNOWN')


###############################################################
#
# usage() - Prints out the usage and options help
#
###############################################################
def usage():
    print """
\t-h --help\t\t- Prints out this help message
\t-v --version\t\t- Prints the version number
\t-H --host <ip_address>\t- IP address of the cisco stack
\t-c --community <string>\t- SNMP community string
\t-d --debug\t\t- Verbose mode for debugging
"""
    sys.exit(UNKNOWN)


###############################################################
#
# parse_args() - parses command line args and returns options dict
#
###############################################################
def parse_args():
    options = dict([
        ('remote_ip', None),
        ('community', 'Public')
    ])
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvH:c:d", ["help", "host=", "version", "community=", "debug"])
    except getopt.GetoptError, err:
        # print help information and exit:
        print str(err)    # will print something like "option -a not recognized"
        usage()
    for o, a in opts:
        if o in ("-d", "--debug"):
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(funcName)s - %(message)s'
            )
            logging.debug('*** Debug mode started ***')
        elif o in ("-v", "--version"):
            print "{0} plugin version {1}".format(__program_name__, __version__)
            sys.exit(0)
        elif o in ("-h", "--help"):
            usage()
        elif o in ("-H", "--host"):
            options['remote_ip'] = a
        elif o in ("-c", "--community"):
            options['community'] = a
        else:
            assert False, "unhandled option"
    logging.debug('Printing initial variables')
    logging.debug('remote_ip: {0}'.format(options['remote_ip']))
    logging.debug('community: {0}'.format(options['community']))
    if options['remote_ip'] is None:
        print "Requires host to check"
        usage()
    return options


###############################################################
#
# plugin_exit() - Prints value and exits
# :param exitcode: Numerical or constant value
# :param message: Message to print
#
###############################################################
def plugin_exit(exitcode, message=''):
    logging.debug('Exiting with status {0}. Message: {1}'.format(exitcode, message))
    status = exit_status(exitcode)
    print '{0} {1} - {2}'.format(__program_name__, status, message)
    sys.exit(exitcode)


###############################################################
#
# get_status_table() - Acquire info about the interface status
# :param remote_ip: IP address of the system
# :param community: SNMP read community
# :return status_table: dict of dict of interface status
#
###############################################################
def get_status_table(remote_ip, community):
    status_table = {}
    # descriptions
    ifdesc_oid = netsnmp.VarList(netsnmp.Varbind('.1.3.6.1.2.1.2.2.1.2'))
    logging.debug('Walking if descriptions -- ')
    netsnmp.snmpwalk(ifdesc_oid, DestHost=remote_ip, Version=1, Community=community)
    if not ifdesc_oid:
        plugin_exit(CRITICAL, 'Unable to retrieve SNMP interface descriptions')
    for member in ifdesc_oid:
        logging.debug('Interface info: {0}'.format(member.print_str()))
        a = {'name': member.val, 'index': member.iid}
        status_table[a['index']] = a
    # status
    ifstatus_oid = netsnmp.VarList(netsnmp.Varbind('.1.3.6.1.2.1.2.2.1.8'))
    logging.debug('Walking if status -- ')
    netsnmp.snmpwalk(ifstatus_oid, DestHost=remote_ip, Version=1, Community=community)
    if not ifstatus_oid:
        plugin_exit(CRITICAL, 'Unable to retrieve SNMP interface status')
    for member in ifstatus_oid:
        logging.debug('Interface status info: {0}'.format(member.print_str()))
        a = {'status': member.val, 'index': member.iid}
        status_table[a['index']]['status'] = a['status']
    return status_table


###############################################################
#
# evaluate_results() - Evaluate status of the interfaces
# :param status: status info dict
# :return result: result for exit code
# :return message: status message string for exit
#
###############################################################
def evaluate_results(status):
    message = [""]
    result = OK
    logging.debug('Evaluating results -- ')
    for i, interface in status.iteritems():
        match = re.search('Tunnel', interface['name'])
        if match:
            i_status = 'UP'
            if interface['status'] is not '1':
                i_status = 'DOWN'
                result = CRITICAL
                logging.debug('{0} is down - changing result to CRITICAL'.format(interface['name']))
            logging.debug('{0} - {1}'.format(interface['name'], i_status))
            message.append("{0}: {1} ".format(interface['name'], i_status))
    message = ''.join(message)
    return result, message


###############################################################
#
# main() - Main function
#
###############################################################
def main():
    options = parse_args()
    status = get_status_table(options['remote_ip'], options['community'])
    result, message = evaluate_results(status)
    plugin_exit(result, message)


if __name__ == "__main__":
    main()
