#!/bin/bash

ENV_FILE=".env"
KEY="INFLUXDB_ADMIN_TOKEN"
TOKEN=$(openssl rand -base64 48 | tr -d '\n=' | cut -c1-86)

# Update or add the token in the .env file
if grep -q "^$KEY=" "$ENV_FILE"; then
    sed -i.bak "s|^$KEY=.*|$KEY=$TOKEN|" "$ENV_FILE"
else
    echo "$KEY=$TOKEN" >> "$ENV_FILE"
fi

echo "New $KEY generated in .env"
