#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/30 11:55
# @Author  : zjz

from config import url_info

class Extract:
    def __init__(self):
        self.name = ""

    def doExtract(self, **kwargs):
        json_text = kwargs.get('result')


class Consumer:
    def __init__(self):
        print("init")