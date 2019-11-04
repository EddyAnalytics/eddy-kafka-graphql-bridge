# Start the topology as defined in http://debezium.io/docs/tutorial/
docker-compose up

# Start MySQL connector
curl -i -X POST -H "Accept:application/json" -H  "Content-Type:application/json" http://localhost:8083/connectors/ -d @register-mysql.json

# Consume messages from a Debezium topic
docker-compose exec kafka /kafka/bin/kafka-console-consumer.sh \
    --bootstrap-server kafka:9092 \
    --from-beginning \
    --property print.key=true \
    --topic mysql1.inventory.customers

# Modify records in the database via MySQL client
docker-compose exec mysql bash -c 'mysql -u $MYSQL_USER -p$MYSQL_PASSWORD inventory'

Or connect using a GUI, credentials are in the docker-compose.yml file

# Shut down the cluster
docker-compose down

# To improve performance
https://www.starlette.io/#performance

# Configure JWT
## symmetric
Make sure JWT_KEY is set to the key you want and JWT_ALGORITHM should be set to 'HS256' which is the default

## asymmetric
generate an RSA key pair:
```
# generate the private key
openssl genrsa -out private.pem 4096
# obtain the public key in pem format
openssl rsa -pubout -in private.pem -out public.pem
# obtain the public key in ssh format
ssh-keygen -f public.pem -i -mPKCS8 > public.ssh
```

Set `JWT_ALGORITHM` to `RS256` and set `JWT_KEY` to the contents of public.ssh
