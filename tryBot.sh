#!/bin/bash
ps -ef | grep bot_main |grep -v grep > /dev/null 
if [ $? != 0 ] 
then
       /home/ubuntu/bot_telegram/bot_main.sh > /dev/null
fi
