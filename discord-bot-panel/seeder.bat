@echo off
type init.sql | docker exec -i CMAI_db psql -U soy -d CMAI
