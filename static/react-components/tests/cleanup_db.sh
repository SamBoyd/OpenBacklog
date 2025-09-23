#! /bin/bash


TABLES_TO_CLEAN="field_definition group initiative_group initiative"

for TABLE in $TABLES_TO_CLEAN; do
    psql taskmanager_test_db -c "DELETE from dev.$TABLE"
done
