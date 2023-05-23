#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# date：  2022-11-23 09:59:14
# author  Rami
#
"""
本文件描述:

定义 PhoneCtrl类，执行功能有：
PhoneCtrl.conn()
PhoneCtrl.clock_in
PhoneCtrl.clock_off

加入retry、跟短信告警

"""

from ppadb.client import Client as AdbClient
import time
from pathlib import Path
import sys
BASE_DIR = str(Path(__file__).resolve().parent.parent)
sys.path.append(BASE_DIR)
# 导入本地包
from module import log_factory
# 导入图像识别包
import aircv as ac
# 导入crc文字识别包
from cnocr import CnOcr
import numpy as np
import configparser


class PhoneAdbCtrl():
    def __init__(self,User) -> None:
        self.config = configparser.ConfigParser()
        self.config.read(BASE_DIR + '/conf/config.ini')
        self.name = self.config[User]['Device_Name']
        self.client = AdbClient(host="127.0.0.1", port=5037)
        if self.config[User]['Connect_Type'] == 'Wifi':
            self.ip = self.config[User]['IP_Address']
            self.port = int(self.config[User]['Port'])
            self.phone = self.client.device(str(self.ip) + ':' + str(self.port))
        elif self.config[User]['Connect_Type'] == 'USB':
            Series_Strings = self.config[User]['Series_Strings']
            self.phone = self.client.device(Series_Strings)

        self.OCR_Timeout_Retry = self.config.getint('Config','OCR_Timeout_Retry')




    def send_tap(self,x,y):
        self.phone.input_tap(x,y)

    def img_match(self,imsrc_path,imsch_path):
        imsrc = ac.imread(imsrc_path) # 原始图像
        imsch = ac.imread(imsch_path) # 带查找的部分
        ac_postion = ac.find_template(imsrc, imsch)

        log_factory.DEBUGGER.debug(f"查找源{imsrc_path}，目标{imsch_path}，成功匹配到图像！位置：{ac_postion}")
        return ac_postion


    def text_identify(self,text,img_path):
        """
        传入需要识别的文字和图片，返回点击坐标
        
        如果返回为-1, 则是未识别图片

        TODO:尽量不要出现多个同样的text
        """
        
        img_fp = img_path
        ocr = CnOcr() 
        out = ocr.ocr(img_fp)
        axis_postion = "-1"
        for i in out:
            if text in i['text']:
                axis_postion = np.mean(i['position'],axis=0)
                # print(axis_postion)
                log_factory.DEBUGGER.debug(f"成功获取坐标！位置：{axis_postion}")

        return axis_postion


    def screenshot(self,level="info",save_path="/screenshot/"):
        """
        进行截图，如果是error等级的，会进行重命名
        如果是info等级，处理结束后会使用正则进行匹配命名删除

        一个机器一次只处理一张截图，返回截图路径+文件名
        """
        if level == "error":
            save_path = sys.path[-1] + save_path + self.name + "-" + self.photo_name + "-error.png"
        else:
            save_path = sys.path[-1] + save_path + self.name + "-" + self.photo_name + "-info.png"
        log_factory.DEBUGGER.debug(f"进行设备{self.name}的{self.photo_name}过程截图")
        result = self.phone.screencap()
        with open(save_path, "wb") as fp:
            fp.write(result)
        return save_path

    def send_keyevent(self, keycode):
        """
        发送一个按键事件
        https://developer.android.com/reference/android/view/KeyEvent.html
        :return:
        """
        self.phone.input_keyevent(keycode)

    def try_click(self):
        """
        尝试点击确认、确定、允许、继续 这几个字眼, 加上稍后
        """
        result = self.text_identify("稍后",self.screenshot_path)
        if result != "-1":
            log_factory.DEBUGGER.info(f"设备{self.name}的{self.photo_name}过程截图尝试点击《稍后》")
            self.send_tap(result[0],result[1])
        result = self.text_identify("确认",self.screenshot_path)
        if result != "-1":
            log_factory.DEBUGGER.info(f"设备{self.name}的{self.photo_name}过程截图尝试点击《确认》")
            self.send_tap(result[0],result[1])
        result = self.text_identify("确定",self.screenshot_path)
        if result != "-1":
            log_factory.DEBUGGER.info(f"设备{self.name}的{self.photo_name}过程截图尝试点击《确定》")
            self.send_tap(result[0],result[1])
        result = self.text_identify("允许",self.screenshot_path)
        if result != "-1":
            log_factory.DEBUGGER.info(f"设备{self.name}的{self.photo_name}过程截图尝试点击《允许》")
            self.send_tap(result[0],result[1])
        result = self.text_identify("继续",self.screenshot_path)
        if result != "-1":
            log_factory.DEBUGGER.info(f"设备{self.name}的{self.photo_name}过程截图尝试点击《继续》")
            self.send_tap(result[0],result[1])
        pass




    def check_right(self,text):
        """
        此函数用做超时检查，避免因为机型性能问题导致等待时间过长

        传入需要识别的文字/图片，进行判断，超时2的指数重试5次，重试3次后就重头开始

        同时如果出现 确认、确定、允许三个字眼的时候，进行尝试点击
        """

        time_sleep = 1
        for i in range(0, self.OCR_Timeout_Retry):
            # i为等待超时
            self.screenshot_path = self.screenshot()
            result = self.text_identify(text,self.screenshot_path)
            if result != "-1":
                log_factory.DEBUGGER.info(f"进行设备{self.name}的{self.photo_name}过程截图识别成功,坐标{result}")
                return
            elif result == "-1":
                log_factory.DEBUGGER.warning(f"进行设备{self.name}的{self.photo_name}过程截图识别不成功,进行重试第{i}次中！")
                log_factory.DEBUGGER.info(f"等待{time_sleep}秒中")
                self.try_click()
                time.sleep(time_sleep)
                time_sleep *= 2
            else:
                pass
                log_factory.DEBUGGER.error(f"{self.name}设备无法打开{self.photo_name},重新尝试")

        self.screenshot(level="error")
        log_factory.DEBUGGER.error(f"{self.name}设备无法打开{self.photo_name},超时等待无效，进行重试")
        return "-1"


            
    def final_tap_check(self, Input, Step_Section):
        text = Input
        self.photo_name= Step_Section
        log_factory.DEBUGGER.debug(f"设备{self.name}进行点击最后步骤{Step_Section},点击目标为{Input}")

        # 确定需要等待咋办
        self.check_right(text)
        # 有两个确定咋办？
        self.screenshot_path = self.screenshot()

        img_fp = self.screenshot_path
        ocr = CnOcr() 
        out = ocr.ocr(img_fp)
        axis_postion = []
        for i in out:
            # 返回存在的坐标
            if text in i['text']:
                axis_postion.append(np.mean(i['position'],axis=0))
                # print(axis_postion)
                log_factory.DEBUGGER.debug(f"成功{text}获取坐标！第{i}个位置：{axis_postion}")
        for j in axis_postion:
                self.phone.input_tap(j[0],j[1])
                log_factory.DEBUGGER.info(f"{self.name}设备在截图{self.photo_name}中尝试点击{text}")
                result = self.text_identify("正常",self.screenshot_path)
                if result == "-1":
                    log_factory.DEBUGGER.warning(f"{self.name}设备在截图{self.photo_name}中点击{text}未成功，继续")
                    continue
                else:
                    pass
        
        self.photo_name="FINASH"
        self.screenshot()
        log_factory.DEBUGGER.info(f"{self.name}设备打卡成功！")


    def tap_button(self):
        self.photo_name="tap_button"
        log_factory.DEBUGGER.debug(f"设备{self.name}尝试点击打开，进行图片匹配")
        for i in range(0,3):
            return_postion = self.click_and_check_img(target= sys.path[-1] + "/src_img/buoy.png",click_type="img")
            if return_postion == None:
                log_factory.DEBUGGER.warning(f"设备{self.name}进行图片匹配未发现，尝试下滑{i}次")
                self.phone.input_swipe(540, 1300, 540, 500, 100)
                continue
            else:
                x = return_postion['result'][0]
                y = return_postion['result'][1]
                log_factory.DEBUGGER.debug(f"设备{self.name}进行图片匹配成功，坐标{x}，{y}")
                self.send_tap(x,y)
                break

            





    def retrun_img_match_position(self,target):
        self.screenshot_path = self.screenshot()
        imsrc = ac.imread(self.screenshot_path) # 原始图像
        imsch = ac.imread(target) # 带查找的部分
        click_axios = ac.find_template(imsrc, imsch)
        log_factory.DEBUGGER.debug(f"查找源{self.screenshot_path}，目标{target}，成功匹配到图像！位置：{click_axios}")
        return click_axios


    def click_and_check_txt(self,Input,Output,Step_Section):
        """
        先对当前页面进行截图
        然后判断Input，点击，如果无法成功(超时OCR_Timeout_Retry次数)，就认为识别失败，返回TimeoutError
        往下滑动Downslide_Retry次，重复识别check_right，识别错误则抛出Exception
        检查Ouput是否点击成功
        """
        self.photo_name=Step_Section
        log_factory.DEBUGGER.info(f"设备{self.name}开始打卡步骤{Step_Section},类型为『TXT』，打卡关键字为{Input}，打卡成功关键字为{Output}")
        for i in range(1,self.config.getint('Config','Downslide_Retry')+2): # range是用1，2，3不使用
            # 进行截图并返回路径
            self.screenshot_path = self.screenshot()
            click_axios = self.text_identify(Input, self.screenshot_path)
            self.send_tap(click_axios[0], click_axios[1])
            if self.check_right(Output) != "-1":
                log_factory.DEBUGGER.info(f"{self.name}设备尝试打开{Output}成功，成功找到{Output}!")
                # 成功找到就跳出循环
                break
            elif self.check_right(Output) == "-1":
                log_factory.DEBUGGER.warning(f"{self.name}设备打卡步骤{Step_Section}识别Input{Input}和Output{Output}失败，进行下滑，次数{i}次!")
                self.phone.input_swipe(540, 1300, 540, 500, 100)
                # 没有找到就继续咯
            if i == self.config.getint('Config','Downslide_Retry')+1:
                # 尝试最后都没匹配到，抛出识别错误
                raise Exception(f"{self.name}设备打卡步骤{Step_Section}识别Input{Input}和Output{Output}失败，进行下滑次数{i}次均失败!,抛出错误")



    def click_and_check_img(self,IMG_Input, Output, Step_Section):
        self.photo_name=Step_Section
        log_factory.DEBUGGER.info(f"设备{self.name}开始打卡步骤{Step_Section},类型为『IMAGE』，打卡关键图像为{IMG_Input}，打卡成功关键字为{Output}")
        for i in range(1,self.config.getint('Config','Downslide_Retry')+2):
            return_postion = self.retrun_img_match_position(target= sys.path[-1] + IMG_Input)
            time.sleep(2)
            if return_postion == None:
                log_factory.DEBUGGER.warning(f"设备{self.name}进行图片匹配未发现，尝试下滑{i}次")
                self.phone.input_swipe(540, 1300, 540, 500, 100)
                
            else:
                x = return_postion['result'][0]
                y = return_postion['result'][1]
                log_factory.DEBUGGER.info(f"设备{self.name}进行图片匹配成功，坐标{x}，{y}")
                self.send_tap(x,y)
                break
            if i == self.config.getint('Config','Downslide_Retry')+1:
                # 尝试最后都没匹配到，抛出识别错误
                raise Exception(f"{self.name}设备打卡步骤{Step_Section}识别Input{IMG_Input}和Output{Output}失败，进行下滑次数{i}次均失败!")


    def open_wecom(self):
        # self.phone.shell("am start com.tencent.mm/com.tencent.mm.ui.LauncherUI")
        self.phone.shell("am force-stop com.tencent.wework")
        time.sleep(0.5)
        self.phone.shell("am start com.tencent.wework/com.tencent.wework.launch.LaunchSplashActivity")
        time.sleep(0.5)

        self.photo_name="open_wecom"

        log_factory.DEBUGGER.debug(f"设备{self.name}尝试打开微信，判断关键字：消息")
        self.check_right("消息")



    def open_phone(self):
        if "false" in self.phone.shell("dumpsys deviceidle | grep mScreenOn"):
            log_factory.DEBUGGER.debug(f"设备{self.name}未亮屏，进行亮屏")
            self.send_keyevent("KEYCODE_POWER")
        self.send_keyevent("KEYCODE_HOME")
        time.sleep(1)
        self.photo_name="open_phone"
        self.screenshot()
        pass


if __name__ == '__main__':


    if not sys.version_info >= (3, 0):
        sys, exit('[x] WARNING - this script requires Python 3.x  Exiting')
    
    # 测试代码
    # log_factory.DEBUGGER.debug(f"设备未亮屏，进行亮屏")

