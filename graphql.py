#change
import asyncio
from aiokafka import AIOKafkaConsumer
from tartiflette import Subscription, Scalar
from tartiflette_starlette import TartifletteApp, GraphiQL, Subscriptions
from util import debezium_deserializer
from config import BOOTSTRAP_SERVERS


# define the graphql sdl
sdl = """
scalar JSON

type Query {
  _: Boolean
}

type Subscription {
  kafka(topics: [String]): JSON
  topics: JSON
}
"""


# define graphql Scalar for json
@Scalar("JSON")
class ScalarJSON:
    def coerce_output(self, value):
        return value

    def coerce_input(self, value):
        return json.loads(value)

    def parse_literal(self, ast):
        if isinstance(ast, StringValueNode):
            return json.loads(ast)
        return "UNDEFINED_VALUE"


# define a graphql subscription allowing one to subscribe to any kafka topic
@Subscription("Subscription.kafka")
async def on_kafka(parent, args, context, info):
    consumer = AIOKafkaConsumer(
        *args['topics'],
        bootstrap_servers=BOOTSTRAP_SERVERS,
        loop=asyncio.get_running_loop(),
        value_deserializer=debezium_deserializer
    )
    await consumer.start()
    try:
        async for msg in consumer:
            yield msg.value
    finally:
        await consumer.stop()


@Subscription("Subscription.topics")
async def on_topics(parent, args, context, info):
    consumer = AIOKafkaConsumer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        loop=asyncio.get_running_loop(),
        value_deserializer=debezium_deserializer
    )
    await consumer.start()
    topics = []
    while True:
        new_topics = [topic for topic in await consumer.topics()]
        if topics != new_topics:
            topics = new_topics
            yield topics
        await asyncio.sleep(10)


graphql_app = TartifletteApp(
    sdl=sdl,
    subscriptions=True,
    graphiql=GraphiQL(
        default_query="""
        subscription {
            kafka(topics: ["mysql1.inventory.customers"]),
        }
        """
    ),
)
