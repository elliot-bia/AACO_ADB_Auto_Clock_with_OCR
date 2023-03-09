#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# date:        2018/5/18
# author:      he.zhiming
# ========================
#
# Update：  2022-11-23 09:59:14
# Editor：  Rami
#

"""
本文件描述:
对该文件进行小幅修改，让它用起来更顺手
主要是用来记录log，实现多log文件/目录、多handlers

用法：
from module import log_factory
log_factory.DEBUGGER.info('这里是日志')

注意：
会自动在base dir目录，也就是sys.path[-1]下，创建log目录

"""

from __future__ import unicode_literals, absolute_import

import logging
import logging.config
import logging.handlers
from datetime import datetime
import os
import sys

class _InfoFilter(logging.Filter):
    def filter(self, record):
        """only use INFO

        筛选, 只需要 INFO 级别的log

        :param record:
        :return:
        """
        if logging.INFO <= record.levelno < logging.ERROR:
            # 已经是INFO级别了
            # 然后利用父类, 返回 1
            return super().filter(record)
        else:
            return 0

 
# 自动创建文件夹
def check_and_mkdir(path):
    if os.path.exists(path):
        pass
    else:
        print('Path [{:s}] not exists, creating'.format(path))
        os.makedirs(path)

def _get_filename(*, filedir='', filename='app.log', log_level='info'):
    date_str = datetime.today().strftime('%Y%m%d')
    pidstr = str(os.getpid())
    log_dir = sys.path[-1] + "/log/" + filedir +'/'
    check_and_mkdir(log_dir)
    return ''.join((
        log_dir + date_str,'-', log_level, '-', filename,))
        # log_dir + date_str, '-', pidstr, '-', log_level, '-', filename,))


class _LogFactory:
    # 每个日志文件，使用 2GB
    _SINGLE_FILE_MAX_BYTES = 2 * 1024 * 1024 * 1024
    # 轮转数量是 10 个
    _BACKUP_COUNT = 10

    # 基于 dictConfig，做再次封装
    _LOG_CONFIG_DICT = {
        'version': 1,

        'disable_existing_loggers': False,

        'formatters': {
            # 开发环境下的配置
            'dev': {
                'class': 'logging.Formatter',
                'format': ('%(levelname)s %(asctime)s %(name)s %(module)s [%(processName)s %(threadName)s] '
                           '[%(filename)s %(lineno)s %(funcName)s] %(message)s'),
                'datefmt' : '"%Y-%m-%d %H:%M:%S"'
            },
            # 生产环境下的格式(越详细越好)
            'prod': {
                'class': 'logging.Formatter',
                'format': ('%(levelname)s [%(asctime)s %(created)f] %(name)s %(module)s %(process)d %(thread)d '
                           '[%(filename)s %(lineno)s %(funcName)s] %(message)s')
            },
        },
        # 针对 LogRecord 的筛选器
        'filters': {
            'info_filter': {
                '()': _InfoFilter,

            }
        },

        # 处理器(被loggers使用)
        'handlers': {
            'debug_console': {  # 按理来说, console只收集ERROR级别的较好
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
                'formatter': 'dev'
            },
            'debug_file_info': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': _get_filename(filename='DEBUGGER.log'),
                'maxBytes': _SINGLE_FILE_MAX_BYTES,  # 2GB
                'encoding': 'UTF-8',
                'backupCount': _BACKUP_COUNT,
                'formatter': 'prod',
                'delay': True,
                'filters': ['info_filter', ]
            },
            'debug_file_debug': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': _get_filename(log_level='debug',filename='DEBUGGER.log'),
                'maxBytes': _SINGLE_FILE_MAX_BYTES,  # 2GB
                'encoding': 'UTF-8',
                'backupCount': _BACKUP_COUNT,
                'formatter': 'prod',
                'delay': True,
            },
            'debug_file_error': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': _get_filename(filename='DEBUGGER.log', ),
                'maxBytes': _SINGLE_FILE_MAX_BYTES,  # 2GB
                'encoding': 'UTF-8',
                'backupCount': _BACKUP_COUNT,
                'formatter': 'prod',
                'delay': True,
            }

        },

        # 真正的logger(by name), 可以有丰富的配置
        'loggers': {
            'DEBUGGER': {
                # 输送到3个handler，它们的作用分别如下
                #   1. console：控制台输出，方便我们直接查看，只记录ERROR以上的日志就好
                #   2. file： 输送到文件，记录INFO以上的日志，方便日后回溯分析
                #   3. file_error：输送到文件（与上面相同），但是只记录ERROR级别以上的日志，方便研发人员排错
                # 'handlers': ['debug_console'],
                'handlers': ['debug_console','debug_file_debug', 'debug_file_error'],
                'level': 'DEBUG',
            },

        },
    }

    logging.config.dictConfig(_LOG_CONFIG_DICT)

    @classmethod
    def get_logger(cls, logger_name):
        return logging.getLogger(logger_name)


DEBUGGER = logging.getLogger('DEBUGGER')
