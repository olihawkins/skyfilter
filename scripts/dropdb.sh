#!/bin/zsh

echo "This will delete all existing posts and images in the database. Are you sure you want to proceed? (yes/no) " 
read answer

case $answer in
    [Yy]es )
        echo "Dropping dataset..."
        dropdb skyfilter -i -U admin
        find database/images -mindepth 1 -not -name '.gitignore' -exec rm -rf {} +
        ;;
    [Nn]o )
        echo "Operation aborted."
        exit
        ;;
    * )
        echo "Operation aborted. Please answer 'yes' or 'no'."
        ;;
esac
