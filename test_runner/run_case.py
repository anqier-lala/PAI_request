﻿# -*- coding: utf-8 -*-
# @Time : 2020/7/21 21:35
# @Author : lifangfang

# -*- coding: utf-8 -*-
import os
import time
import unittest
from common import HTMLTestReportCN
from common.email_utils import EmailUtils
from  nb_log import  LogManager


current_path=os.path.dirname(__file__)
test_report_path=os.path.join(current_path,'..','./test_reports/')
test_case_path=os.path.join(current_path,'..','./api_testcase')

logger = LogManager(__file__).get_logger_and_add_handlers(log_filename='ApiTest_%s.log'%time.strftime('%Y_%m_%d'))


class RunCase():
    def __init__(self):
        logger.info( '接口测试开始启动' )
        self.test_case_path = test_case_path
        self.report_path = test_report_path
        self.title = 'P1P2接口自动化测试报告'
        self.description = '自动化接口测试框架'
        self.tester = '测试开发组'
    def load_test_suite(self):
        discover = unittest.defaultTestLoader.discover(start_dir=self.test_case_path,
                                                       pattern='api_test.py',
                                                       top_level_dir=self.test_case_path)
        all_suite = unittest.TestSuite()
        all_suite.addTest( discover )
        logger.info('加载所有的测试模块及方法到测试套件')
        return all_suite
    def run(self):
        report_dir = HTMLTestReportCN.ReportDirectory(self.report_path)
        report_dir.create_dir(self.title)
        report_file_path = HTMLTestReportCN.GlobalMsg.get_value('report_path')
        fp = open( report_file_path ,'wb' )
        logger.info('初始化创建测试报告路径：%s'%report_file_path)
        runner = HTMLTestReportCN.HTMLTestRunner(stream=fp,
                                                 title=self.title,
                                                 description=self.description,
                                                 tester=self.tester)
        runner.run( self.load_test_suite() )
        fp.close()
        return report_file_path


if __name__=='__main__':
    report_path = RunCase().run()
    logger.info('测试活动结束')
    EmailUtils(open(report_path, 'rb').read(), report_path).send_mail()

