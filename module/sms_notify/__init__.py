#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# date：  2022-11-23 09:59:14
# author  Rami
#
"""
本文件描述:
阿里云短信通知接口
注意短信使用次数

用法：
from module import sms_notify

sms_notify.sms_monitor_send(phone_numbers='130xxxx',template_param='{"content":"%s"}' %("new_content"))

注意：
会自动在base dir目录，也就是sys.path[-1]下，创建log目录
"""

from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient

from pathlib import Path
import sys
from module import log_factory
BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
sys.path.append(BASE_DIR)
import configparser

def create_client(access_key_id: str,access_key_secret: str,) -> Dysmsapi20170525Client:
    """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
    config = open_api_models.Config(
        # 您的AccessKey ID,
        access_key_id=access_key_id,
        # 您的AccessKey Secret,
        access_key_secret=access_key_secret
    )
    # 访问的域名
    config.endpoint = f'dysmsapi.aliyuncs.com'
    return Dysmsapi20170525Client(config)

def sms_monitor_send(phone_numbers,template_param='{"code":"1234"}') -> None:
    config = configparser.ConfigParser()
    config.read(BASE_DIR + '/conf/config.ini')
    access_key_id = config['AliyunSMS']['Access_Key_ID']
    access_key_secret = config['AliyunSMS']['access_key_secret']
    sign_name = config['AliyunSMS']['sign_name']
    template_code = config['AliyunSMS']['template_code']

    if access_key_id == "":
        # 如果不填，直接返回
        return

    try:
        client = create_client(access_key_id, access_key_secret)
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            sign_name=sign_name,
            template_code=template_code,
            phone_numbers=phone_numbers,
            template_param=template_param
        )
    except Exception as e:
        log_factory.DEBUGGER.error(e,exc_info=True)

    runtime = util_models.RuntimeOptions()
    try:
        # 复制代码运行请自行打印 API 的返回值
        client.send_sms_with_options(send_sms_request, runtime)
        log_factory.DEBUGGER.info(f"短信发送成功！短信号码：{phone_numbers}，短信内容{template_param}")
    except Exception as error:
        # 如有需要，请打印 error
        log_factory.DEBUGGER.debug(error, exc_info=True)  
        messages = UtilClient.assert_as_string(error.message)
        log_factory.DEBUGGER.error(f"\n\n{'='*30}\n\n短信发送出错，官方出错代码为：{messages}\n\n{'='*30}\n\n", exc_info=True)  

if __name__ == '__main__':



    if not sys.version_info >= (3, 0):
        sys, exit('[x] WARNING - this script requires Python 3.x  Exiting')
    
    # 测试代码
    sms_monitor_send(phone_numbers='123456778',template_param='{"content":"%s"}' %("new_content"))