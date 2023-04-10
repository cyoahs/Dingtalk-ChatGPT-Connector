# -*- coding: utf-8 -*-
import requests
import logging
import json
import pickle
import os


def handler(event, context):
    # ChatGPT API Key
    CHATGPT_API_KEY = os.environ.get('CHATGPT_API_KEY')
    # oss mount point
    OSS_MOUNT_POINT = os.environ.get('OSS_MOUNT_POINT', '/mnt/oss')
    # 历史聊天记录长度
    HISTORY_LENGTH = int(os.environ.get('HISTORY_LENGTH', 5))
    # 日志级别
    VERBOSE = int(os.environ.get('VERBOSE', 25))
    # 超时
    TIMEOUT = int(os.environ.get('TIMEOUT', 55))

    logger = logging.getLogger()
    logger.setLevel(VERBOSE)

    # 获取函数调用传参
    evt = json.loads(event)
    logger.debug(f'raw event: {evt}')
    sessionExpiredTime = evt['sessionExpiredTime']
    sessionWebhook = evt['sessionWebhook']
    question = evt['question']
    user_id = evt['id']
    logger.info('会话过期时间：' + sessionExpiredTime)
    logger.info('会话Webhook：' + sessionWebhook)
    logger.info('消息内容：' + question)

    # 判断是否为指令
    command = question[1:] if question[0] == '\\' else ''
    clear = 'clear'

    # 读取聊天历史记录
    msg_file = os.path.join(OSS_MOUNT_POINT, f'{user_id}.pkl')
    exist = os.path.exists(msg_file)

    msg_history = []
    if exist:
        with open(msg_file, 'rb') as f:
            msg_history = pickle.load(f)[-HISTORY_LENGTH*2:]

    msg_history.append({"role": "user", "content": question})
    logger.debug(f'msg_history: {msg_history}')

    answer = ''
    if command:
        # 执行命令
        if command == clear:
            # 手动清理聊天记录
            if exist:
                os.remove(msg_file)
            answer = clear
            logger.info(clear)
        else:
            # 未知指令
            answer = f'未知指令：{command}'
            logger.warning(f'Unknown command: {command}')
    else:
        # 调用ChatGPT API
        data = {
            "model": "gpt-3.5-turbo",
            "messages": msg_history,
            "temperature": 0.7
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {CHATGPT_API_KEY}'
        }
        try:
            response = requests.post("https://api.openai.com/v1/chat/completions",
                                    headers=headers,
                                    json=data,
                                    timeout=TIMEOUT)
            logger.debug(f'response.text: {response.text}')
        except requests.exceptions.Timeout:
            logger.warning(f'ChatGPT 请求超时！')
            response = None

        reply_success = False
        if response is not None:
            try:
                answer = response.json()['choices'][0]['message']['content'].strip()
                reply_success = True
                logger.info(f'ChatGPT 回答：{answer}')
            except KeyError:
                answer = response.text
                logger.warning(f'无法读取回答！错误信息：{answer}')
        else:
            answer = 'ChatGPT 请求超时！'
            logger.warning(answer)

        # 保存聊天历史记录
        if reply_success:
            msg_history.append({"role": "assistant", "content": answer})
            with open(msg_file, 'wb') as f:
                pickle.dump(msg_history, f)

    # 推送Webhook消息
    msg = {"msgtype": "text", "text": {"content": answer}}
    result = requests.post(sessionWebhook, json=msg)
    logger.info('响应码：' + str(result.status_code))
    logger.info('响应内容：' + result.text)
    return result.text