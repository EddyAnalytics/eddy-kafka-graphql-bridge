import os
import json
import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from tartiflette import Subscription, Scalar
from tartiflette_starlette import TartifletteApp, GraphiQL


# load config from env variables
BOOTSTRAP_SERVERS = os.environ.get('BOOTSTRAP_SERVER', "kafka:9092")

# define the graphql sdl
sdl = """
scalar JSON

type Query {
  _: Boolean
}

type Subscription {
  kafka(topic: String): JSON
}
"""


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


def deserializer(serialized):
    return json.loads(serialized)


@Subscription("Subscription.kafka")
async def on_kafka(parent, args, context, info):
    consumer = AIOKafkaConsumer(
        args['topic'],
        bootstrap_servers=BOOTSTRAP_SERVERS,
        loop=asyncio.get_running_loop(),
        value_deserializer=deserializer
    )
    await consumer.start()
    try:
        async for msg in consumer:
            yield msg.value
    finally:
        await consumer.stop()


app = TartifletteApp(
    sdl=sdl,
    subscriptions=True,
    graphiql=GraphiQL(
        default_query="""
        subscription {
            kafka(topic: "mysql1.inventory.customers")
        }
        """
    ),
)
