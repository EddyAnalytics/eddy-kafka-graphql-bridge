import json

# debezium kafka message deserializer
def debezium_deserializer(serialized):
    return json.loads(serialized)

def utf8_deserializer(serialized):
    return serialized.decode('utf-8')

