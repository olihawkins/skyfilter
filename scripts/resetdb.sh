#!/bin/zsh

dropdb skyfilter -U admin
createdb skyfilter -U admin -E utf8
psql -U admin -d skyfilter -f ./database/skyfilter-tables.sql