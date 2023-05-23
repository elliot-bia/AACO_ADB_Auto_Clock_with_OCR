# 代码逻辑
## main函数：  
1. 判断日期  
2. 读取配置机器
3. 进入phone_admin函数

## phone_admin函数
先进行连接测试，如果出错进行重试，抛出ConnectionError错误
然后进入phone_ctrl类
并在这里处理步骤

## phone_ctrl类
包含了check_right这个判断函数

