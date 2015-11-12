#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
=head1 NAME
znc_logs

=head1 DESCRIPTION
Shows lines/minute in today's znc-logs

=head2 CONFIGURATION
[znc_logs]
user znc # or any other user/group that can read the znclog-folder
group znc
env.logdir /var/lib/znc/moddata/log # path to the log-folder without a sep at the end

=head1 COPYRIGHT
GPL VERSION 3

=head1 AUTHOR
Thor77 <thor77[at]thor77.org>
'''
from sys import argv
from time import strftime
import os
from glob import glob

logdir = os.environ.get('logdir')

if not logdir:
    raise Exception('You have to set the logdir with env.logdir <path to log> in the plugin-conf!')

today = strftime('%Y-%m-%d')
last_values_file = os.environ['MUNIN_PLUGSTATE'] + os.sep + 'last_values'


def get_last():
    try:
        d = {}
        with open(last_values_file, 'r') as f:
            for line in f:
                line = line[:-1]
                key, value = line.split(':')
                d[key] = float(value)
        return d
    except FileNotFoundError:
        return {}


def data():
    last = get_last()
    current = {}
    logs = glob('{logdir}{sep}*{sep}*{sep}*.log'.format(logdir=logdir, sep=os.sep))
    for log in logs:
        network, channel, log_date = log.split(os.sep)[-3:]
        log_date = log_date.replace('.log', '')
        if log_date != today:
            continue
        current_activity = sum(
            1
            for i in open(log, 'r', encoding='utf-8', errors='replace')
        )
        network_channel_repr = '{}@{}'.format(channel, network)
        if network_channel_repr in last:
            last_activity = last[network_channel_repr]
            activity = (current_activity - last_activity) / 5  # subtrate last from current and divide through 5 to get new lines / minute
            if activity < 0:
                activity = 0
        else:
            activity = 0
        current[network_channel_repr] = activity

        # print munin-things
        print('{network_channel}.label {network_channel}'.format(
            network_channel=network_channel_repr))
        print('{network_channel}.value {activity}'.format(
            network_channel=network_channel_repr, activity=activity))
    with open(last_values_file, 'w') as f:
        for k, v in current.items():
            f.write('{}:{}\n'.format(k, v))

if len(argv) > 1 and argv[1] == 'config':
    print('graph_title Lines in the ZNC-log')
    print('graph_category znc')
    print('graph_vlabel lines/minute')
    print('graph_scale no')
data()
