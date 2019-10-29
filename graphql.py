import asyncio
from aiokafka import AIOKafkaConsumer
from tartiflette import Subscription, Scalar, Resolver
from tartiflette_starlette import TartifletteApp, GraphiQL, Subscriptions
from util import debezium_deserializer, utf8_deserializer
import config
import time


# define the graphql sdl
sdl = """
scalar JSON

type Query {
  _: Boolean
}

type Subscription {
  kafka(topics: [String], from: Int): JSON
  sample(topic: String!, rate: Float): String
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
        bootstrap_servers=config.BOOTSTRAP_SERVERS,
        loop=asyncio.get_running_loop(),
        value_deserializer=debezium_deserializer
    )
    try:
        await consumer.start()
        start_from = args.get('from', int(time.time())) * 1000
        partitions = consumer.assignment()
        partition_times = {partition: start_from for partition in partitions}
        partition_offsets = await consumer.offsets_for_times(partition_times)
        for partition in partitions:
            if partition in partition_offsets and partition_offsets[partition]:
                consumer.seek(partition, partition_offsets[partition].offset)
            async for msg in consumer:
                yield msg.value
    except Exception as e:
        yield repr(e)
    finally:
        await consumer.stop()


@Subscription("Subscription.topics")
async def on_topics(parent, args, context, info):
    consumer = AIOKafkaConsumer(
        bootstrap_servers=config.BOOTSTRAP_SERVERS,
        loop=asyncio.get_running_loop(),
        value_deserializer=debezium_deserializer
    )
    await consumer.start()
    topics = []
    try:
        while True:
            new_topics = [topic for topic in await consumer.topics()]
            if topics != new_topics:
                topics = new_topics
                yield topics
            await asyncio.sleep(10)
    except Exception as e:
        yield repr(e)
    finally:
        await consumer.stop()


@Subscription("Subscription.sample")
async def on_sample(parent, args, context, info):
    from secrets import token_urlsafe
    topic = args["topic"]
    consumer = AIOKafkaConsumer(
        topic,
        group_id="kafka-graphql-bridge" + token_urlsafe(16),
        bootstrap_servers=config.BOOTSTRAP_SERVERS,
        loop=asyncio.get_running_loop(),
        value_deserializer=utf8_deserializer
    )
    await consumer.start()
    previous_offset = -1
    try:
        while True:
            partitions = consumer.assignment()
            end_offsets = await consumer.end_offsets(partitions)
            for partition, offset in end_offsets.items():
                if offset and previous_offset != offset:
                    consumer.seek(partition, max(0, offset-1))
                    sample = await consumer.getone()
                    previous_offset = offset
                    yield sample.value
            await asyncio.sleep(1/min(args["rate"], 1000))
    except Exception as e:
        yield repr(e)
    finally:
        await consumer.stop()

graphql_app = TartifletteApp(
    sdl=sdl,
    subscriptions=True,
    graphiql=GraphiQL(
        default_query="""
        subscription {
            kafka(topics: ["mysql1.inventory.customers"]),
        }
        """
     ) if config.DEBUG else None,
)
