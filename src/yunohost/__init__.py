#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import glob

import moulinette
from moulinette import m18n
from moulinette.utils.log import configure_logging
from moulinette.interfaces.cli import colorize, get_locale

def is_installed():
    return os.path.isfile('/etc/yunohost/installed')


def cli(debug, quiet, output_as, timeout, args, parser):

    init_logging(interface="cli", debug=debug, quiet=quiet)

    # Check that YunoHost is installed
    if not is_installed():
        check_command_is_valid_before_postinstall(args)

    ret = moulinette.cli(
        ['yunohost'] + extensions(),
        args,
        output_as=output_as,
        timeout=timeout,
        parser_kwargs={'top_parser': parser},
    )
    sys.exit(ret)


def api(debug, host, port):

    init_logging(debug=debug)

    def is_installed_api():
        return {'installed': is_installed()}

    # FIXME : someday, maybe find a way to disable route /postinstall if
    # postinstall already done ...

    ret = moulinette.api(
        ['yunohost'] + extensions(),
        host=host,
        port=port,
        routes={('GET', '/installed'): is_installed_api},
        use_websocket=True
    )
    sys.exit(ret)


def extensions():
    # This is probably not used anywhere, but the actionsmap and code can be
    # extended by creating such files that contain bits of actionmap...
    return [f.split('/')[-1][:-4] for f in glob.glob("/usr/share/moulinette/actionsmap/ynh_*.yml")]


def check_command_is_valid_before_postinstall(args):

    allowed_if_not_postinstalled = ['tools postinstall',
                                    'tools versions',
                                    'backup list',
                                    'backup restore',
                                    'log display']

    if (len(args) < 2 or (args[0] + ' ' + args[1] not in allowed_if_not_postinstalled)):
        init_i18n()
        print(colorize(m18n.g('error'), 'red') + " " + m18n.n('yunohost_not_installed'))
        sys.exit(1)


def init_i18n():
    # This should only be called when not willing to go through moulinette.cli
    # or moulinette.api but still willing to call m18n.n/g...
    m18n.load_namespace('yunohost')
    m18n.set_locale(get_locale())


def init_logging(interface="cli",
                 debug=False,
                 quiet=False,
                 logdir="/var/log/yunohost"):

    logfile = os.path.join(logdir, "yunohost-%s.log" % interface)

    if not os.path.isdir(logdir):
        os.makedirs(logdir, 0750)

    # ####################################################################### #
    #  Logging configuration for CLI (or any other interface than api...)     #
    # ####################################################################### #
    if interface != "api":
        configure_logging({
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'tty-debug': {
                    'format': '%(relativeCreated)-4d %(fmessage)s'
                },
                'precise': {
                    'format': '%(asctime)-15s %(levelname)-8s %(name)s %(funcName)s - %(fmessage)s'
                },
            },
            'filters': {
                'action': {
                    '()': 'moulinette.utils.log.ActionFilter',
                },
            },
            'handlers': {
                'tty': {
                    'level': 'DEBUG' if debug else 'INFO',
                    'class': 'moulinette.interfaces.cli.TTYHandler',
                    'formatter': 'tty-debug' if debug else '',
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'formatter': 'precise',
                    'filename': logfile,
                    'filters': ['action'],
                },
            },
            'loggers': {
                'yunohost': {
                    'level': 'DEBUG',
                    'handlers': ['file', 'tty'] if not quiet else ['file'],
                    'propagate': False,
                },
                'moulinette': {
                    'level': 'DEBUG',
                    'handlers': [],
                    'propagate': True,
                },
                'moulinette.interface': {
                    'level': 'DEBUG',
                    'handlers': ['file', 'tty'] if not quiet else ['file'],
                    'propagate': False,
                },
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['file', 'tty'] if debug else ['file'],
            },
        })
    # ####################################################################### #
    #  Logging configuration for API                                          #
    # ####################################################################### #
    else:
        configure_logging({
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'console': {
                    'format': '%(relativeCreated)-5d %(levelname)-8s %(name)s %(funcName)s - %(fmessage)s'
                },
                'precise': {
                    'format': '%(asctime)-15s %(levelname)-8s %(name)s %(funcName)s - %(fmessage)s'
                },
            },
            'filters': {
                'action': {
                    '()': 'moulinette.utils.log.ActionFilter',
                },
            },
            'handlers': {
                'api': {
                    'level': 'DEBUG' if debug else 'INFO',
                    'class': 'moulinette.interfaces.api.APIQueueHandler',
                },
                'file': {
                    'class': 'logging.handlers.WatchedFileHandler',
                    'formatter': 'precise',
                    'filename': logfile,
                    'filters': ['action'],
                },
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'console',
                    'stream': 'ext://sys.stdout',
                    'filters': ['action'],
                },
            },
            'loggers': {
                'yunohost': {
                    'level': 'DEBUG',
                    'handlers': ['file', 'api'] + ['console'] if debug else [],
                    'propagate': False,
                },
                'moulinette': {
                    'level': 'DEBUG',
                    'handlers': [],
                    'propagate': True,
                },
            },
            'root': {
                'level': 'DEBUG',
                'handlers': ['file'] + ['console'] if debug else [],
            },
        })
