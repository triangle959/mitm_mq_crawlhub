# mitm_mq_crawlhub
手机爬虫框架

自己造轮子，框架原理：
- 设置手机自动滑动脚本，mitmproxy截取请求，设置需要抓取的接口或者H5，通过rabbitmq发布解析任务
- 接取MQ的任务进行消费清洗，对于不同routing_key进行不同的清洗(json\html)，对于不同的routing_key保存入不同的数据库表
- routing_key 设置为 数据源_数据表_数据格式