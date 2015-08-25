# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
#
# The list of domains to be checked must be provided at domain_list_file.txt
# Add a line per domain with the format:
# DOMAIN_ID admin_url monitor_user monitor_password
#
# Usage: wlst.sh wls_top.py domain_list_file.txt


import sys
import re
from datetime import datetime

# ANSI codes
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BOLD = '\033[1m'
NORMAL = '\033[0m'
waitTime = 5000


def expand(text, expand_len, pad='c', fillchar=' ', color=None, red_on=0):
    """ Expand string to expand_len
    :param text: input text
    :param expand_len: "expand to" size
    :param pad: 'l' - left, 'r' - right, 'c' - center
    :param fillchar: char for string filling
    :param color:  prefix with ANSI color
    :param red_on: use RED on non zero value
    :return:
    """
    if red_on and str(text) != "0":
        color = BOLD + RED
    text = str(text)
    lpad = rpad = ''
    missing = expand_len - len(text)
    if pad == 'l':
        lpad = missing * fillchar
    if pad == 'r':
        rpad = missing * fillchar
    if pad == 'c':
        lpad = rpad = (missing / 2) * fillchar
    text = lpad + text + rpad
    if len(text) < expand_len:
        text += fillchar
    if color:
        text = color + text + NORMAL
    return text

def build_header():
    header = BOLD + "|"
    header_fields = [
        ('Server',  20, 'r'),
        ('State',   11, 'c'),
        ('Socks',   5,  'c'),
        ('Throu',   5,  'c'),
        ('Hogg',    4,  'c'),
        ('Pendi',   5,  'c'),
        ('Queue',   5,  'c'),
    ]
    for field, fill_len, pos in header_fields:
        header += expand(field, fill_len, pos)+"|"
    header += NORMAL

def print_subsystem_health(server):
    subsystemsHealth = server.getSubsystemHealthStates()
    for component in subsystemsHealth.tolist():
        comp, state, reason = \
        re.findall('Component:(.*),.*State:(\w*).*ReasonCode:\[(.*)\]', str(component))[0]
        if state != 'HEALTH_OK':
            print BOLD + RED + comp, state, reason + NORMAL

def build_serverinfo(server):
            sName = server.getName()
            runningServers.append(sName)
            serverState = server.getState()
            serverHealth = re.findall('State:(\w*)', str(server.getHealthState()))[0]
            openSockets = hogging = pending = queue_len = ''
            if serverState == 'RUNNING':
                serverState = serverHealth
                cd("/ServerRuntimes/" + sName)
                openSockets = cmo.getOpenSocketsCurrentCount()
                cd('ThreadPoolRuntime/ThreadPoolRuntime')
                throughput = int(get('Throughput'))
                hogging = get('HoggingThreadCount')
                pending = get('PendingUserRequestCount')
                queue_len = get('QueueLength')
                cd("../..")
                constraints = ls('MaxThreadsConstraintRuntimes', returnMap='true')
                cd("MaxThreadsConstraintRuntimes")
                constraintInfo = ''
                for constraint in constraints:
                    cd(constraint)
                    name = get('Name').replace('MaxThreadsCount', '')
                    deferred = str(get('DeferredRequests'))
                    if deferred != "0":
                        deferred = BOLD + RED + str(deferred) + NORMAL
                    executing = get('ExecutingRequests')
                    constraintInfo += '%s: %d/%s; ' % (name, executing, deferred)
                    cd('..')
                cd("..")
            if serverState == 'HEALTH_OK':
                serverState_color = GREEN
            else:
                serverState_color = BOLD + RED
            info_fields = [
                expand(sName, 20, 'r'),
                expand(serverState, 11, 'c', color=serverState_color),
                expand(openSockets, 5),
                expand(throughput, 5),
                expand(pending, 5, red_on=1),
                expand(hogging, 4),
                expand(queue_len, 5, red_on=1)
            ]
            info_line = '|'
            for field in info_fields:
                info_line += field + "|"
            print info_line + constraintInfo
            if serverState == 'RUNNING':
                print_subsystem_health(server)


redirect('/dev/null', 'false')
domain_list = open(sys.argv[1]).read().splitlines()

while 1:
    print "\n" + datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for domain in domain_list:
        block, admin_url, username, password = domain.split()

        print "\nConnecting to " + admin_url + "...",
        connect(username, password, admin_url)
        domainConfig = domainRuntimeService.getDomainConfiguration()
        domainRuntime()

        print build_header
        runningServers = []
        servers = domainRuntimeService.getServerRuntimes()
        for server in servers:
            serverInfo = build_serverinfo(server)

        stoppedServers = ''
        for server in domainConfig.getServers():
            if server.getName() not in runningServers:
                stoppedServers += server.getName() + " "
        if stoppedServers:
            print BOLD + "Stopped: " + YELLOW + stoppedServers + NORMAL
    java.lang.Thread.sleep(waitTime)
