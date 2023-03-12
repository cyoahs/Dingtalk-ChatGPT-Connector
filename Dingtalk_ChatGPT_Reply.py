# -*- coding: utf-8 -*-
import requests
import logging
import json

def handler(event, context):
  logger = logging.getLogger()

  # ChatGPT API Key
  chatGPT_api_key = '修改为你的ChatGPT API Key' 

  # 获取函数调用传参
  evt = json.loads(event)
  sessionExpiredTime = evt['sessionExpiredTime']
  sessionWebhook = evt['sessionWebhook']
  question = evt['question']
  logger.info('会话过期时间：' + sessionExpiredTime)
  logger.info('会话Webhook：' + sessionWebhook)
  logger.info('消息内容：' + question)

  # 调用ChatGPT API  
  data = {
      "model": "gpt-3.5-turbo",
      "messages": [{"role": "user", "content": question}],
      "temperature": 0.7
  }
  headers = {'Content-Type' : 'application/json', 'Authorization' : f'Bearer {chatGPT_api_key}'}
  response = requests.post("https://api.openai.com/v1/chat/completions",headers=headers,json=data)
  answer = response.json()['choices'][0]['message']['content'].strip()
  logger.info(f'ChatGPT回答：{answer}')

  # 推送Webhook消息
  msg = {"msgtype": "text","text": {"content":answer}}
  result = requests.post(sessionWebhook,json = msg)
  logger.info('响应码：' + str(result.status_code))
  logger.info('响应内容：' + result.text)
  return result.text
