# -*- coding: utf-8 -*-
import requests
import logging
import json
import time
import fc2

def handler(environ, start_response):
    logger = logging.getLogger()

    # Endpoint地址详见文档https://help.aliyun.com/document_detail/52984.html
    endpoint = '修改为你的阿里云函数计算Endpoint地址' 

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
    logger.info('会话过期时间：' + sessionExpiredTime)
    logger.info('会话Webhook：' + sessionWebhook)
    logger.info('消息内容：' + question)

    # 获取异步调用函数计算的认证信息
    context = environ['fc.context']
    creds = context.credentials
    # 异步调用ChatGPT回复内容推送钉钉Webhook函数
    client = fc2.Client(endpoint=endpoint,accessKeyID=creds.access_key_id,accessKeySecret=creds.access_key_secret,securityToken=creds.security_token)
    # 异步调用函数的参数对象
    payload = {'sessionExpiredTime':sessionExpiredTime,'sessionWebhook':sessionWebhook,'question':question}
    payload = json.dumps(payload,ensure_ascii=False)
    # 异步调用回复函数
    client.invoke_function('ChatGTP_Services', 'Dingtalk_ChatGPT_Reply', payload=payload.encode("utf-8"), headers={'x-fc-invocation-type': 'Async'})

    status = '200 OK'
    response_headers = [('Content-type', '"application/json; charset=utf-8')]
    start_response(status, response_headers)

    return [bytes('{}','utf-8')]
