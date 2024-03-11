#!/bin/zsh

psql -U admin -d skyfilter -f ./database/skyfilter-tables.sql
