#!/usr/bin/env bash

cat ./init.sql | docker exec -i CMAI_db psql -U soy -d CMAI
