# Dingtalk-ChatGPT-Connector
在钉钉中直接与ChatGPT对话，基于阿里云函数计算 FC 与对象存储 OSS 构建 Serverless 服务。

### 运行环境
阿里云函数计算 Python 3.9 HTTP函数、事件函数

### 前提条件
1. 拥有一个OpenAI账号（ChatGPT归属于OpenAI的产品）
2. 拥有一个钉钉账号，自用可以注册一个钉钉组织
3. 拥有一个阿里云账号

**【Q&A】是否需要一台服务器进行部署？**

由于采用阿里云Serverless服务，服务运行在阿里云函数计算与对象存储中，无需服务器部署。

**【Q&A】函数计算的费用？**

阿里云函数计算采取按量付费的形式，及按函数运行时长、使用内存、CPU、流量进行计费，具体计费规则可参考阿里云文档。

函数计算实测最低的0.05cpu+128MB内存即可满足运行需求，一般仅个人使用，用量基本不会产生费用（函数计算按每小时用量计费，且对金额小数位2位后进行抹零，即费用小于0.01不会收费）。

对象存储每月 5GB 免费额度，每次调用存储+流量在 1 kB 左右，个人使用费用也可以忽略。

### 连接器原理
1. 用户向钉钉ChatGPT机器人发送消息
2. 钉钉机器人将消息通过HTTP协议转发到指定的消息接收地址，其中包含消息内容及会话Webhook（用于消息回复）
3. 钉钉会话HTTP函数接收到钉钉ChatGPT机器人发送的消息，异步调用ChatGPT回复事件函数（传递消息内容及会话Webhook），并响应钉钉机器人消息接收成功。
4. ChatGPT回复事件函数从OSS拉取聊天历史，将消息内容发送到ChatGPT API，收到ChatGPT API回复的内容后，将聊天内容保存在OSS，将回复内容发送到会话Webhook
5. 用户接收到ChatGPT机器人的回复内容

**【Q&A】为什么不在会话HTTP函数中直接调用ChatGPT API返回回复内容？而是异步调用ChatGPT回复事件函数？**

钉钉会话HTTP函数可以直接返回回复消息内容，但钉钉机器人对消息接收地址的响应时间有要求，超过10s未响应会主动关闭HTTP连接，当ChatGPT接收或回复内容较多时处理时间较长，消息未响应时钉钉机器人已关闭HTTP连接。

### 部署步骤

1. 注册OpenAI，获取调用ChatGPT API的Key（具体注册流程和API Key获取不再描述详细，请参详搜索引擎）

2. 开通阿里云函数计算服务，服务区域切换到美国-硅谷，创建 ChatGPT 服务 `ChatGTP_Services`。

3. 开通阿里云对象存储服务，创建一个Bucket，按需命名。

4. 在函数计算 `ChatGTP_Services` 的服务详情-存储配置中开启OSS挂载功能，挂载上一步所创建的Bucket，建议挂载点为 `/mnt/oss`。

5. ChatGPT服务下分别创建HTTP函数 `Dingtalk_Conversation` 和事件函数 `Dingtalk_ChatGPT_Reply`，代码参考本 Repository 的`Dingtalk_Conversation.py` 和 `Dingtalk_ChatGPT_Reply.py`
* HTTP函数 `Dingtalk_Conversation` 的HTTP触发器提供公网访问地址，用于接收钉钉机器人转发的用户消息
* 事件函数 `Dingtalk_ChatGPT_Reply` 用于调用ChatGPT API并回复用户消息

6. 为两个函数配置环境变量
```javascript
// 环境变量说明
// 函数：Dingtalk_Conversation:
{
    // 必填项
    "CHATGPT_FUNCTION": "Dingtalk_ChatGPT_Reply",
    "DINGTALK_APP_SECRET": "修改为你的钉钉应用的appSecret",
    "ENDPOINT": "修改为你的阿里云函数计算Endpoint地址",
    "SERVICE_NAME": "ChatGTP_Services",
    
    // 选填项
    "VERBOSE": "25", // 日志级别
}
// Endpoint地址详见文档 https://help.aliyun.com/document_detail/52984.html

// 函数: Dingtalk_ChatGPT_Reply
{
    // 必填项
    "CHATGPT_API_KEY": "修改为你的ChatGPT API Key",

    // 选填项
    "HISTORY_LENGTH": "5", // 历史记录长度（一问一答算一次）
    "OSS_MOUNT_POINT": "/mnt/oss", // 自定义 OSS 挂载点
    "TIMEOUT": "55", // chatgpt请求时间，请使用小于函数执行时间的数值
    "VERBOSE": "25", // 日志级别
}
```

7. 钉钉开发者后台中创建ChatGPT应用及机器人（政策原因机器人名称勿命名为ChatGPT），机器人消息接收地址填入Dingtalk_Conversation 的公网访问地址

**【注意事项】函数计算的服务区域不建议选择国内，建议选择美国本土，由于ChatGPT不对国内提供服务及政策等原因，国内IP可能无法访问ChatGPT API。**

**【注意事项】注意保护好阿里云账号的AccessKey！以防泄露造成损失！！！**

**【Q&A】创建完HTTP函数和事件函数后无法调用?**

建议简称一下HTTP函数和事件函数的调用日志，查看函数是否被调用或执行成功。

如果函数没有被调用，那有可能是下面的几种原因。

一、钉钉机器人接收消息的地址不正确认

请确保钉钉机器人接收消息的地址为HTTP函数的公网访问地址

二、函数配置->请求处理程序 配置不正确。

例如你的python文件名为index.py，函数计算执行所调用的方法名称为handler，那么请求处理程序配置的值应为 index.handler

https://help.aliyun.com/document_detail/74756.html?spm=a2c4g.11186623.0.0.47fd4e53Lfh2nR

三、HTTP函数异步调用事件函数的参数值不正确。

第一个参数为事件函数所在服务名称，第二个参数为函数的名称

client.invoke_function('service_name', 'function_name', headers = {'x-fc-invocation-type': 'Async'})

### 使用方式

方式一：用户在钉钉中搜索创建的机器人，发送消息，随后既可以收到ChatGPT的回复

方式二：将机器人添加到钉钉群里中，@机器人 并附带消息内容，随后既可以收到ChatGPT的回复

### 聊天历史

默认按照用户名存储过去5次对话，可以在函数 `Dingtalk_ChatGPT_Reply` 中添加环境变量 `HISTORY_LENGTH` 调整。在聊天中发送 `\clear` 可以强制清楚该用户的历史会话。

### 参考资料
* 原作者仓库：https://github.com/Sunny-Law/Dingtalk-ChatGPT-Connector
* ChatGPT API 调用文档：https://platform.openai.com/docs/api-reference/making-requests
* 钉钉机器人接收消息文档：https://open.dingtalk.com/document/orgapp/receive-message
* 阿里云函数计算概述文档：https://help.aliyun.com/document_detail/61009.html
* 阿里云对象存储文档: https://help.aliyun.com/product/31815.html
* 阿里云AccessKey获取方式: https://help.aliyun.com/document_detail/116401.htm
* 函数计算挂载OSS文档：https://help.aliyun.com/document_detail/454199.html
