#!/bin/sh

set -eu

: "${API_MAIL_TOKEN:?API_MAIL_TOKEN doit etre configure}"

printf 'X-API-TOKEN: %s\n' "$API_MAIL_TOKEN" | curl \
    --fail --silent --show-error --max-time 60 \
    --request POST --header @- \
    --header 'Content-Type: application/json' \
    --data '{"email":"direction@peraudiere.com"}' \
    'http://localhost:5000/rapport-contrats'