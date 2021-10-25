#!/usr/bin/env bash

# 前端：
# 1. 没有此状态文件时，对登陆用户就正常显示同步按钮。
# 2. 有此文件时，对登陆用户就显示一个 <Span> ，不是 button，写 “同步中，请等待””
# 3. 用户点击按钮后，在后台create一个文件，里面写0，表示待同步
# 后端：
# 1. 加一条crontab，每分钟跑一次脚本
# 2. 脚本判断下：
# 2.1 文件存在+内容是0-待同步+没有同步脚本在跑  —>  文件内容改成1，跑同步脚本
# 2.2 文件存在+内容是0-待同步+有同步脚本在跑 —> 文件内容改1
# 2.3 文件存在+内容是1-同步中+有同步脚本在跑 —> 啥也不做
# 2.4 文件存在+内容是1-同步中+没有同步脚本在跑 —> 删除文件
# 2.5 文件存在+内容不是0/1  —> 删除文件
# 2.6 文件不存在  ——> 啥也不做

syncdbfilepath="/home/www/ecustCourseInfo/src/courseinfo/data/syncdbstatus.txt"

[ ! -f ${syncdbfilepath} ] && echo "2.6 exit" && exit
syncdbflag=$(cat ${syncdbfilepath})
# [ "x${syncdbflag}" != "x0" ] && ["x${syncdbflag}" != "x1" ] && rm -rf ${syncdbfilepath} && echo "2.5 rm file & exit" && exit
