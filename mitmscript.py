#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/30 11:54
# @Author  : zjz
import threading
import mitmproxy.http
from mitmproxy import ctx
from config import url_info
from mqbase import RabbitPublisher

"""
根据不同的info信息分配不同的抽取规则，根据规则不同保存到不同的mysql表
"""
def response(flow):
    # if 'Project/V3/detail.' in flow.request.url:
    #     ctx.log.warn(flow.request.url)
    #     flow.response.text = flow.response.text.replace('isBay == false', 'false')
    for info in url_info:
        if info in flow.request.url:
            ctx.log.info(flow.request.url + '匹配到规则 ' + 'info' + ' 正在抓取')
            threading.Thread(target=RabbitPublisher.run, args=(info,)).start()