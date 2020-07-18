#!/usr/bin/env python
# encoding: utf-8
# @author: liusir
# @file: requests_utils.py
# @time: 2020/7/12 8:49 上午

import ast
import re
import requests
import jsonpath
from common.config_utils import config
from common.check_utils import CheckUtils

class RequestsUtils():
    def __init__(self):
        self.hosts =  config.hosts
        self.headers = {"ContentType":"application/json;charset=utf-8"}
        self.session = requests.session()
        self.temp_variables = {}

    def __get(self,get_info):
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
        return result




    def __post(self,post_info):
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
        #调用CheckUtils()中的方法
        result = CheckUtils(response).run_check(post_info['期望结果类型'],post_info['期望结果'])
        return result

    def request(self,step_info):
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
        return result

    def request_by_step(self,step_infos):
        self.temp_variables = {}
        for step_info in step_infos:
            temp_result = self.request( step_info )
            if temp_result['code']!=0:
                break
            print( temp_result['response_body'] )
        return temp_result


if __name__=="__main__":
    case_info = [
        {'请求方式': 'get', '请求地址': '/cgi-bin/token', '请求参数(get)': '{"grant_type":"client_credential","appid":"wx55614004f367f8ca","secret":"65515b46dd758dfdb09420bb7db2c67f"}', '提交数据（post）': '', '取值方式': 'json取值', '传值变量': 'token', '取值代码': '$.access_token'},
        {'请求方式': 'post', '请求地址': '/cgi-bin/tags/delete', '请求参数(get)': '{"access_token":${token}}', '提交数据（post）': '{"tag":{"id":459}}', '取值方式': '无', '传值变量': '', '取值代码': ''}
    ]
    RequestsUtils().request_by_step( case_info )


