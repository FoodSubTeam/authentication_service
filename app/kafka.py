from confluent_kafka import Producer, Consumer, KafkaError
from kafka.admin import KafkaAdminClient, NewTopic
from app.topics import Topic

kafka_bootstrap_servers = 'kafka-service.kafka.svc.cluster.local:9092'

class KafkaProducerSingleton:
    _producer = None

    @classmethod
    def get_producer(cls):
        if cls._producer is None:
            cls._producer = Producer({
                'bootstrap.servers': kafka_bootstrap_servers,
                'client.id': 'authentication-service-producer'
            })
        return cls._producer

    @classmethod
    def produce_message(cls, topic, message):
        producer = cls.get_producer()
        producer.produce(topic, message)
        producer.flush()

def setup_topic(topic_name: str):
    admin_client = KafkaAdminClient(
        bootstrap_servers=kafka_bootstrap_servers,
        client_id="init-check"
    )
    topics = admin_client.list_topics()
    if topic_name not in topics:
        admin_client.create_topics([NewTopic(topic_name, num_partitions=1, replication_factor=1)])


def init_topics():
    required_topics = [Topic.AUTH_LOGIN_URL.value, Topic.USER_LOGIN.value]
    for topic in required_topics:
        setup_topic(topic)