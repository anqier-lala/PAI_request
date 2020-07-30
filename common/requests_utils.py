#!/usr/bin/env python
# encoding: utf-8
# @author: liusir
# @file: requests_utils.py
# @time: 2020/7/12 8:49 上午

import time
import ast
import re
import requests
import jsonpath
from requests.exceptions import RequestException
from requests.exceptions import ProxyError
from requests.exceptions import ConnectionError
from nb_log import LogManager
from common.config_utils import config
from common.check_utils import CheckUtils
from common.testdata_utils import TestdataUtils

logger = LogManager(__file__).get_logger_and_add_handlers(log_filename='ApiTest_%s.log'%time.strftime('%Y_%m_%d'))


class RequestsUtils():
    def __init__(self):
        self.hosts =  config.hosts
        self.headers = {"ContentType":"application/json;charset=utf-8"}
        self.session = requests.session()
        self.temp_variables = {}

    def __get(self,get_info):
        try:
            url = self.hosts + get_info["请求地址"]
            response = self.session.get( url = url,
                                         params = ast.literal_eval(get_info["请求参数(get)"])
                                         )
            response.encoding = response.apparent_encoding
            if get_info["取值方式"] == "json取值":
                value = jsonpath.jsonpath( response.json(),get_info["取值代码"] )[0]
                self.temp_variables[ get_info["传值变量"] ] = value
            elif get_info["取值方式"] == "正则取值":
                value = re.findall(get_info["取值代码"],response.text)[0]
                self.temp_variables[get_info["传值变量"]] = value
            result = CheckUtils(response).run_check(get_info['期望结果类型'], get_info['期望结果'])
        except ProxyError as e:
            result = {'code': 4, 'result': '[%s]请求：代理错误异常' % (get_info["接口名称"])}
        except ConnectionError as e:
            result = {'code': 4, 'result': '[%s]请求：连接超时异常' % (get_info["接口名称"])}
        except RequestException as e:
            result = {'code': 4, 'result': '[%s]请求：Request异常，原因：%s' % (get_info["接口名称"], e.__str__())}
        except Exception as e:
            result = {'code':4,'result':'[%s]请求：系统异常，原因：%s'%(get_info["接口名称"],e.__str__())}
        return result

    def __post(self,post_info):
        try:
            url = self.hosts + post_info["请求地址"]
            response = self.session.post( url = url,
                                         headers = self.headers,
                                         params = ast.literal_eval(post_info["请求参数(get)"]),
                                        # data = post_infos["提交数据（post）"],
                                         json=ast.literal_eval(post_info["提交数据（post）"])
                                        )
            response.encoding = response.apparent_encoding
            if post_info["取值方式"] == "json取值":
                value = jsonpath.jsonpath( response.json(),post_info["取值代码"] )[0]
                self.temp_variables[ post_info["传值变量"] ] = value
            elif post_info["取值方式"] == "正则取值":
                value = re.findall(post_info["取值代码"],response.text)[0]
                self.temp_variables[post_info["传值变量"]] = value
            #调用CheckUtils()
            result = CheckUtils(response).run_check(post_info['期望结果类型'],post_info['期望结果'])
        except ProxyError as e:
            result = {'code': 4, 'result': '[%s]请求：代理错误异常' % (post_info["接口名称"])}
        except ConnectionError as e:
            result = {'code': 4, 'result': '[%s]请求：连接超时异常' % (post_info["接口名称"])}
        except RequestException as e:
            result = {'code': 4, 'result': '[%s]请求：Request异常，原因：%s' % (post_info["接口名称"], e.__str__())}
        except Exception as e:
            result = {'code':4,'result':'[%s]请求：系统异常，原因：%s'%(post_info["接口名称"],e.__str__())}
        return result

    def request(self,step_info):
        try:
            request_type = step_info["请求方式"]
            param_variable_list = re.findall('\\${\w+}', step_info["请求参数(get)"])
            if param_variable_list:
                for param_variable in param_variable_list:
                    step_info["请求参数(get)"] = step_info["请求参数(get)"]\
                        .replace(param_variable,'"%s"' % self.temp_variables.get(param_variable[2:-1]))
            if request_type == "get":
                result = self.__get( step_info )
            elif request_type == "post":
                data_variable_list = re.findall('\\${\w+}', step_info["提交数据（post）"])
                if data_variable_list:
                    for param_variable in data_variable_list:
                        step_info["提交数据（post）"] = step_info["提交数据（post）"] \
                            .replace(param_variable, '"%s"' % self.temp_variables.get(param_variable[2:-1]))
                result = self.__post( step_info )
            else:
                result = {'code':1,'result':'请求方式不支持'}
                logger.error('请求方式不支持')
        except Exception as e:
            result = {'code':4,'result':'用例编号[%s]的[%s]步骤出现系统异常，原因：%s'%(step_info['测试用例编号'],step_info["测试用例步骤"],e.__str__())}
            logger.error('用例编号[%s]的[%s]步骤出现系统异常，原因：%s'%(step_info['测试用例编号'],step_info["测试用例步骤"],e.__str__()))
        return result

    def request_by_step(self,step_infos):
        self.temp_variables = {}
        for step_info in step_infos:
            temp_result = self.request( step_info )
            print(temp_result)
            if temp_result['code']!=0:
                TestdataUtils().write_result_to_excel(step_info["测试用例编号"],step_info['测试用例步骤'],"失败")
                break
            else:
                TestdataUtils().write_result_to_excel(step_info["测试用例编号"], step_info['测试用例步骤'])
        return temp_result

if __name__=="__main__":

    case_info = [
        {'请求方式': 'get', '请求地址': '/cgi-bin/token', '请求参数(get)': '{"grant_type":"client_credential","appid":"wxc036fc4ba09c7c16","secret":"bc85b7bc56a9c6bb2d7011f758ab9d7e"}', '提交数据（post）': '', '取值方式': 'json取值', '传值变量': 'token', '取值代码': '$.access_token', '期望结果类型': '正则匹配', '期望结果': '{"access_token":"(.+?)","expires_in":(.+?)}'},
        {'请求方式': 'post', '请求地址': '/cgi-bin/tags/create', '请求参数(get)': '{"access_token":${token}}', '提交数据（post）': '{"tag" : {"name" : "衡东"}}','取值方式': '无', '传值变量': '', '取值代码': '', '期望结果类型': '正则匹配', '期望结果': '{"tag":{"id":(.+?),"name":"衡东"}}'}
    ]
    RequestsUtils().request_by_step(case_info)