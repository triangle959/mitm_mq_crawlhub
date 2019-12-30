#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/30 13:40
# @Author  : zjz
import traceback
import pika
import threading
import json
import datetime
import time
from pika.exceptions import ChannelClosed
from pika.exceptions import ConnectionClosed
from config import Username,Password,RabbitMQ_IP,RabbitMQ_PORT,url_info

# rabbitmq 配置信息
MQ_CONFIG = {
    "host": RabbitMQ_IP,
    "port": RabbitMQ_PORT,
    "vhost": "/",
    "user": Username,
    "passwd": Password,
    "exchange": "mitm_exchange",
    "sendId": "ProduceService",
    "recvId": "ConsumerService"
}


class RabbitMQServer(object):
    _instance_lock = threading.Lock()

    def __init__(self):
        self.recv_serverid = ""
        self.send_serverid = ""
        self.exchange = MQ_CONFIG.get("exchange")
        self.connection = None
        self.channel = None

    def reconnect(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            credentials = pika.PlainCredentials(MQ_CONFIG.get("user"), MQ_CONFIG.get("passwd"))
            parameters = pika.ConnectionParameters(MQ_CONFIG.get("host"), MQ_CONFIG.get("port"), MQ_CONFIG.get("vhost"),
                                                   credentials)
            self.connection = pika.BlockingConnection(parameters)

            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=self.exchange, exchange_type="direct")

            if isinstance(self, RabbitComsumer):
                result = self.channel.queue_declare(queue="queue_{0}".format(self.recv_serverid), exclusive=True, durable=True)
                queue_name = result.method.queue
                self.channel.queue_bind(exchange=self.exchange, queue=queue_name, routing_key=self.recv_serverid)
                self.channel.basic_consume(self.consumer_callback, queue=queue_name, no_ack=False)
        except Exception as e:
            print(e)


class RabbitComsumer(RabbitMQServer):

    def __init__(self):
        super(RabbitComsumer, self).__init__()

    def consumer_callback(self, ch, method, properties, body):
        """
        :param ch:
        :param method:
        :param properties:
        :param body:
        :return:
        """
        ch.basic_ack(delivery_tag=method.delivery_tag)
        process_id = threading.current_thread()
        print("current process id is {0} body is {1}".format(process_id, body))

    def start_consumer(self):
        while True:
            try:
                self.reconnect()
                self.channel.start_consuming()
            except ConnectionClosed as e:
                self.reconnect()
                time.sleep(2)
            except ChannelClosed as e:
                self.reconnect()
                time.sleep(2)
            except Exception as e:
                traceback.print_exc()
                self.reconnect()
                time.sleep(2)

    @classmethod
    def run(cls, recv_serverid):
        consumer = cls()
        consumer.recv_serverid = recv_serverid
        consumer.start_consumer()


class RabbitPublisher(RabbitMQServer):

    def __init__(self):
        super(RabbitPublisher, self).__init__()

    def start_publish(self, text):
        self.reconnect()
        while True:
            message = {"result": text}
            message = dict_to_json(message)
            try:
                self.channel.basic_publish(exchange=self.exchange, routing_key=self.send_serverid, body=message)
                break
            except ConnectionClosed as e:
                self.reconnect()
                time.sleep(2)
            except ChannelClosed as e:
                self.reconnect()
                time.sleep(2)
            except Exception as e:
                self.reconnect()
                time.sleep(2)

    @classmethod
    def run(cls, send_serverid, text):
        publish = cls()
        # 定义好routing_key，再进行实例化连接
        publish.send_serverid = send_serverid
        publish.start_publish(text)


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)


def dict_to_json(po):
    jsonStr = json.dumps(po, ensure_ascii=False, cls=CJsonEncoder)
    return jsonStr


def json_to_dict(jsonstr):
    if isinstance(jsonstr, bytes):
        jsonstr = jsonstr.decode("utf-8")
    d = json.loads(jsonstr)
    return d

if __name__ == '__main__':
    recv_serverid = MQ_CONFIG.get("recvId")
    send_serverid = MQ_CONFIG.get("sendId")
    # 这里分别用两个线程去连接和发送
    threading.Thread(target=RabbitComsumer.run, args=(recv_serverid,)).start()
    threading.Thread(target=RabbitPublisher.run, args=(send_serverid,)).start()
    # 这里也是用两个连接去连接和发送，
    # threading.Thread(target=RabbitComsumer.run, args=(send_serverid,)).start()
    # RabbitPublisher.run(recv_serverid)
