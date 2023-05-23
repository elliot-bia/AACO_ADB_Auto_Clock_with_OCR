from pathlib import Path
import sys
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.append(BASE_DIR)
import os
import time
from datetime import datetime
import configparser
import random
from multiprocessing import Pool
from module.log_factory import DEBUGGER

from chinese_calendar import is_workday
from ppadb.client import Client as AdbClient
from module import sms_notify
from core import PhoneCtrl
import json


def phone_alive(User):
    """
    检查机器adb连接是否正常
    超时3次则认为机器无法连接，短信通知
    """

    DEBUGGER.debug(f"进入phone_alive函数")
    config = configparser.ConfigParser()
    config.read(BASE_DIR + '/conf/config.ini')
    client = AdbClient(host="127.0.0.1", port=5037)  #  ADB server port
    if config[User]['Connect_Type'] == 'Wifi':
        ip = config[User]['IP_Address']
        port = int(config[User]['Port'])
        name = config[User]['Device_Name']
        connect_status = client.remote_connect(ip, port)
        if connect_status:
            DEBUGGER.info(f"{name}设备连接成功！，ip地址{ip}，端口{port}")
        else:
            DEBUGGER.warn(f"{name}设备连接失败！稍后5秒重试！")
            time.sleep(5)
            connect_status = client.remote_connect(ip, port)
            if not connect_status:
                DEBUGGER.error(f"{name}设备重试连接失败!！")
                # send_sms()
                raise ConnectionError(f"设备{name}连接失败！")
    elif config[User]['Connect_Type'] == 'USB':
        name = config[User]['Device_Name']
        Series_Strings = config[User]['Series_Strings']
        if client.device(Series_Strings) != None:
            DEBUGGER.info(f"{name}设备连接成功！，序列号{Series_Strings}")
        else:
            DEBUGGER.warn(f"{name}设备连接失败！稍后5秒重试！")
            time.sleep(5)
            if client.device(Series_Strings) == None:
                DEBUGGER.error(f"{name}设备重试连接失败!！")
                # send_sms()
                raise ConnectionError(f"设备{name}连接失败！")

def phone_admin(User):
    DEBUGGER.debug(f"用户{User}进入phone_admin函数")
    config = configparser.ConfigParser()
    config.read(BASE_DIR + '/conf/config.ini')
    Device_Name = config[User]['Device_Name']
    SMS_Phone = config[User]['SMS_Phone']

    # 检查连接性
    try:
        phone_alive(User)
    except ConnectionError as e:
        # 进行短信通知逻辑判断
        if config[User]['SMS_Phone'] != "":
            sms_notify.sms_monitor_send(phone_numbers=SMS_Phone, template_param='{"content":"%s"}' % (
                f"{Device_Name}设备重试连接失败！进行短信通知！请进行手动打卡！"))
            if config['Config']['Admin_Phone_Num'] != "":
                if config['Config']['Admin_Phone_Num'] != config[User]['SMS_Phone']:
                    sms_notify.sms_monitor_send(phone_numbers=config['Config']['Admin_Phone_Num'], template_param='{"content":"%s"}' % (
                    f"{Device_Name}设备重试连接失败！进行短信通知！请通知他人进行手动打卡！"))
            DEBUGGER.error(f"{Device_Name}设备重试连接失败！进行短信通知！请进行手动打卡！")
        else:
            DEBUGGER.error(f"{Device_Name}设备重试连接失败！进行短信通知！请进行手动打卡！")

    # 进行步骤操作
    DEBUGGER.info(f"开始{Device_Name}打卡步骤")
    need_ctrl_phone = PhoneCtrl.PhoneAdbCtrl(User)
     # 先亮屏，再确定打卡APP类型
    need_ctrl_phone.open_phone()
    Close_APP_Retry = config.getint('Config', 'Close_APP_Retry')
    for Close_APP_Retry_Times in range(1, Close_APP_Retry + 2):
        if config['Config']['Punch_APP'] == "wework":
            need_ctrl_phone.open_wecom()
        try:
            step_num = config.getint('Steps', 'TotolSteps')
            for i in range(1,step_num+1):
                Step_Section = 'Step'+str(i)
                if config[Step_Section]['Step_Type'] == 'TEXT':
                    Input = config[Step_Section]['Step_Input']
                    Output = config[Step_Section]['Step_Output']
                    need_ctrl_phone.click_and_check_txt(Input,Output,Step_Section)
                elif config[Step_Section]['Step_Type'] == 'IMAGE':
                    IMG_Input = config[Step_Section]['Step_Input']
                    Output = config[Step_Section]['Step_Output']
                    need_ctrl_phone.click_and_check_img(IMG_Input, Output, Step_Section)
                    pass
                elif config[Step_Section]['Step_Type'] == 'FINISH':
                    Input = config[Step_Section]['Step_Input']
                    need_ctrl_phone.final_tap_check(Input, Step_Section)
                    pass
            break
        except Exception as e:
            DEBUGGER.error(f"{Device_Name}设备打卡出错，报错为{e}")
            DEBUGGER.error(f"{Device_Name}设备打卡出错，进行关闭APP重试，重试次数为{Close_APP_Retry_Times}")

        if Close_APP_Retry_Times == Close_APP_Retry+1:
            DEBUGGER.error(f"{Device_Name}设备打卡出错，进行短信提醒")
            # 进行短信通知逻辑判断
            if config[User]['SMS_Phone'] != "":
                sms_notify.sms_monitor_send(phone_numbers=SMS_Phone, template_param='{"content":"%s"}' % (
                    f"{Device_Name}设备重试连接失败！进行短信通知！请进行手动打卡！"))
                if config['Config']['Admin_Phone_Num'] != "":
                    if config['Config']['Admin_Phone_Num'] != config[User]['SMS_Phone']:
                        sms_notify.sms_monitor_send(phone_numbers=config['Config']['Admin_Phone_Num'], template_param='{"content":"%s"}' % (
                        f"{Device_Name}设备重试连接失败！进行短信通知！请通知他人进行手动打卡！"))
                DEBUGGER.error(f"{Device_Name}设备重试连接失败！进行短信通知！请进行手动打卡！")
            else:
                DEBUGGER.error(f"{Device_Name}设备重试连接失败！进行短信通知！请进行手动打卡！")


def main():
    "主函数入口"
    DEBUGGER.debug(f"开始判断今天是否需要打卡。。。")
    if is_workday(datetime.today()):
        DEBUGGER.debug(f"重启adb服务器中...")
        os.system('adb kill-server')
        time.sleep(5)
        os.system('adb start-server')
        DEBUGGER.debug(f"读取配置中。。。")
        config = configparser.ConfigParser()
        config.read(BASE_DIR + '/conf/config.ini')
        User_list = config.get('Users', 'User_list')
        User_literal = User_list.split(',')
        # 进行随机等待
        sleep_time = random.randint(0,config.getint('Config', 'sleep_time')*60)
        DEBUGGER.info(f"等待时间{sleep_time}")
        time.sleep(sleep_time)
        start = time.time()
        DEBUGGER.debug(f"开始多进程,当前时间为 {start}")
        p = Pool(int(config['Config']['pool']))
        # 添加线程
        for user in User_literal:
            p.apply_async(phone_admin, args=(user,))  # 非常重要！！！需要在参数后面添加逗号，参数需要以元组的形式传递，并在最后一个参数后面加上 ,号
        DEBUGGER.debug('等待所有子进程完成。')
        # close 和 join 是確保主程序結束後，子程序仍然繼續進行
        p.close()
        p.join()        # 调用join之前，先调用close函数，否则会出错。执行完close后不会有新的进程加入到pool,join函数等待所有子进程结束
        end = time.time()
        DEBUGGER.info("结束时间为{},总共用时{}秒".format(end, (end - start)))
    else:
        DEBUGGER.info("今天不打卡！")

if __name__ == '__main__':
    DEBUGGER.debug(f"函数开始,当前母进程: {os.getpid()}")
    if not sys.version_info >= (3, 0):
        sys, exit('[x] WARNING - this script requires Python 3.x  Exiting')
    main()