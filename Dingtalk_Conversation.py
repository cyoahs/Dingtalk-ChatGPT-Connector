# -*- coding: utf-8 -*-
from hashlib import sha256
import hmac, base64
import requests
import logging
import json
import time
import os

import fc2


# 验证钉钉机器人请求签名
def verify_sign(timestamp, appSecret, not_verify_sign):
    data = timestamp + "\n" + appSecret
    appSecret = appSecret.encode('utf-8')
    message = data.encode('utf-8')
    sign = base64.b64encode(hmac.new(appSecret, message, digestmod=sha256).digest())
    sign = str(sign, 'utf-8')
    return not_verify_sign == sign

def handler(environ, start_response):
    logger = logging.getLogger()

    # Endpoint地址详见文档https://help.aliyun.com/document_detail/52984.html
    ENDPOINT = os.environ.get('ENDPOINT')
    # 钉钉应用的appSecret
    APP_SECRET = os.environ.get('DINGTALK_APP_SECRET')
    # 服务名称
    SERVICE_NAME = os.environ.get('SERVICE_NAME')
    # chatgpt 函数名
    CHATGPT_FUNCTION = os.environ.get('CHATGPT_FUNCTION')
    # 日志级别
    VERBOSE = int(os.environ.get('VERBOSE')) if 'VERBOSE' in os.environ else 25

    timestamp = environ['HTTP_TIMESTAMP'] # 获取请求时间戳
    not_verify_sign = environ['HTTP_SIGN'] # 获取请求签名
    # 验证钉钉机器人请求签名，验证不通过时返回拒绝执行响应码
    if verify_sign(timestamp,APP_SECRET,not_verify_sign):
        logger.info('Dingtalk robot request signature verification successful！')
    else:
        logger.info('Dingtalk robot request signature verification failed！')
        status = '403 Forbidden'
        response_headers = [('Content-type', 'text/plain ')]
        start_response(status, response_headers)
        return [bytes('','utf-8')]

    # 获取请求体
    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0
    request_body = environ['wsgi.input'].read(request_body_size)
    request_body = json.loads(request_body) # Bytes转Json
    
    # 获取消息内容及接收回复的Webhook
    sessionExpiredTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(request_body['sessionWebhookExpiredTime']/1000))
    sessionWebhook = request_body['sessionWebhook']
    question = request_body['text']['content'] # 获取消息内容
    # userId = 'default' if 'user' not in request_body else request_body['user']
    userId = request_body['senderNick']
    logger.info('会话过期时间：' + sessionExpiredTime)
    logger.info('会话Webhook：' + sessionWebhook)
    logger.info('消息内容：' + question)

    # 获取异步调用函数计算的认证信息
    context = environ['fc.context']
    creds = context.credentials
    # 异步调用ChatGPT回复内容推送钉钉Webhook函数
    client = fc2.Client(endpoint=ENDPOINT,accessKeyID=creds.access_key_id,accessKeySecret=creds.access_key_secret,securityToken=creds.security_token)
    # 异步调用函数的参数对象
    payload = {'sessionExpiredTime':sessionExpiredTime,'sessionWebhook':sessionWebhook,'question':question,'id':userId}
    payload = json.dumps(payload,ensure_ascii=False)
    # 异步调用回复函数
    client.invoke_function(SERVICE_NAME, CHATGPT_FUNCTION, payload=payload.encode("utf-8"), headers={'x-fc-invocation-type': 'Async'})

    status = '200 OK'
    response_headers = [('Content-type', 'application/json; charset=utf-8')]
    start_response(status, response_headers)

    return [bytes('{}','utf-8')]