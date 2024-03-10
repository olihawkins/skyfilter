#!/bin/zsh

dropdb skyfilter -U admin
createdb skyfilter -U admin -E utf8
psql -U admin -d skyfilter -f /Users/oli/Data/Code/Repositories/olihawkins/skyfilter/database/skyfilter-tables.sql