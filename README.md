# Dingtalk-ChatGPT-Connector
在钉钉中直接与ChatGPT对话，基于阿里云函数计算Serverless服务构建。

### 运行环境
阿里云函数计算 Python 3.9 HTTP函数、事件函数

### 前提条件
1. 拥有一个OpenAI账号（ChatGPT归属于OpenAI的产品）
2. 拥有一个钉钉账号，自用可以注册一个钉钉组织
3. 拥有一个阿里云账号

**【Q&A】是否需要一台服务器进行部署？**

由于采用阿里云Serverless服务，服务运行在阿里云函数计算中，无需服务器部署

**【Q&A】函数计算的费用？**

阿里云函数计算采取按量付费的形式，及按函数运行时长、使用内存、CPU、流量进行计费，具体计费规则可参考阿里云文档。

实测最低的0.05cpu+128MB内存即可满足运行需求，一般仅个人使用，用量基本不会产生费用（函数计算按每小时用量计费，且对金额小数位2位后进行抹零，即费用小于0.01不会收费）。


### 连接器原理
1. 用户向钉钉ChatGPT机器人发送消息
2. 钉钉机器人将消息通过HTTP协议转发到指定的消息接收地址，其中包含消息内容及会话Webhook（用于消息回复）
3. 钉钉会话HTTP函数接收到钉钉ChatGPT机器人发送的消息，异步调用ChatGPT回复事件函数（传递消息内容及会话Webhook），并响应钉钉机器人消息接收成功。
4. ChatGPT回复事件函数将消息内容发送到ChatGPT API，收到ChatGPT API回复的内容后，将回复内容发送到会话Webhook
5. 用户接收到ChatGPT机器人的回复内容


**【Q&A】为什么不在会话HTTP函数中直接调用ChatGPT API返回回复内容？而是异步调用ChatGPT回复事件函数？**

钉钉会话HTTP函数可以直接返回回复消息内容，但钉钉机器人对消息接收地址的响应时间有要求，超过10s未响应会主动关闭HTTP连接，当ChatGPT接收或回复内容较多时处理时间较长，消息未响应时钉钉机器人已关闭HTTP连接。

### 部署步骤

1. 注册OpenAI，获取调用ChatGPT API的Key（具体注册流程和API Key获取不再描述详细，请参详搜索引擎）

2. 开通阿里云函数计算服务，服务区域切换到美国-硅谷，创建ChatGPT服务“ChatGTP_Services”。

3. ChatGPT服务下分别创建HTTP函数“Dingtalk_Conversation”和事件函数“Dingtalk_ChatGPT_Reply”，代码参考本Repository的Dingtalk_Conversation.py和Dingtalk_ChatGPT_Reply.py
* HTTP函数 Dingtalk_Conversation 的HTTP触发器提供公网访问地址，用于接收钉钉机器人转发的用户消息
* 事件函数 Dingtalk_ChatGPT_Reply 用于调用ChatGPT API并回复用户消息

4. 钉钉开发者后台中创建ChatGPT应用及机器人（政策原因机器人名称勿命名为ChatGPT），机器人消息接收地址填入Dingtalk_Conversation 的公网访问地址

**【注意事项】函数计算的服务区域不建议选择国内，建议选择美国本土，由于ChatGPT不对国内提供服务及政策等原因，国内IP可能无法访问ChatGPT API。**

#### 使用方式
1. 用户在钉钉中搜索创建的机器人，发送消息，随后既可以收到ChatGPT的回复
2. 将机器人添加到钉钉群里中，@机器人 并附带消息内容，随后既可以收到ChatGPT的回复

### 参考资料
* ChatGPT API 调用文档：https://platform.openai.com/docs/api-reference/making-requests
* 钉钉机器人接收消息文档：https://open.dingtalk.com/document/orgapp/receive-message
* 阿里云函数计算概述文档：https://help.aliyun.com/document_detail/61009.html
