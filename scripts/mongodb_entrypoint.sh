#!/bin/bash

# Execute the standard entrypoint to start mongodb, but add the additional parameters to setup the replica set
echo "Starting MongoDB through default entrypoint..."

# Avoid unbound variable error as there are no parameters in the initialisation command
if [ "$#" -eq 0 ]; then
  set -- mongod
fi

/usr/local/bin/docker-entrypoint.sh "$@" &

# Wait for MongoDB to be ready to run commands on
echo "Waiting for MongoDB to be ready..."
until mongosh --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase=admin --eval "db.adminCommand('ping')" > /dev/null 2>&1; do
  sleep 1
done

# Initialise indexes if not already setup
for database_name in object-storage test-object-storage; do
  if ! mongosh "$database_name" --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase=admin --quiet --eval "db.attachments.getIndexes().forEach(i => print(i.name))" | grep -q '^attachments_file_name_uniqueness_index$'; then
    echo "Initialising unique file name index for attachments and images collections ($database_name)..."
    mongosh "$database_name" --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase=admin \
      --eval 'db.attachments.createIndex({ "entity_id": 1, "code": 1 }, { name: "attachments_file_name_uniqueness_index", unique: true })' \
      --eval 'db.images.createIndex({ "entity_id": 1, "code": 1 }, { name: "images_file_name_uniqueness_index", unique: true })'
  fi
done

wait
