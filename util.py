import json

# debezium kafka message deserializer
def debezium_deserializer(serialized):
    return json.loads(serialized)

