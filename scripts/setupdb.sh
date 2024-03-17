#!/bin/zsh

psql -U admin -d skyfilter -f ./database/skyfilter-tables.sql
psql -U admin -d skyfilter -f ./database/skyfilter-setup.sql
