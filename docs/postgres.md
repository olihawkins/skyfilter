# Postgresql setup

Date: 2024-03-10

## Setup

Install postgresql with homebrew

```zsh
brew install postgresql@14
```

Start, run and and stop postgresql server:

Use `start` if you want postgres to start whenever the Mac boots

```zsh
brew services start postgresql@14
```

Use `run` instead if you don't want this behaviour

```zsh
brew services run postgresql@14
```

Use `stop` to shut down the server

```zsh
brew services stop postgresql@14
```

Set the root user password

```zsh
psql postgres -c "ALTER USER root_username WITH PASSWORD 'password';"
```

Create new superuser account that isn't the root user

```zsh
createuser admin --pwprompt --superuser
```

Connect to the postgres database as admin

```zsh
psql postgres -U admin
```

Check roles

```zsh
\du
```

Quit psql

```zsh
\q
```

## Disable trust authentication

Do the following if you want to enable password based authentication:

Connect to postgres database as the root user

```zsh
psql postgres
```

Get location of `pg_hba.conf`

```zsh
SHOW hba_file;
```

Quit psql

```zsh
\q
```

Stop postgres

```zsh
brew services stop postgresql@14
```

Edit `pg_hba.conf`: change `trust` to `scram-sha-256` in table

```zsh
nano /opt/homebrew/var/postgresql@14/pg_hba.conf
```

Start postgres

```zsh
brew services start postgresql
```

Connect to postgres database as root user and check password is required

```zsh
psql postgres
```

## Uninstall

```zsh
brew services stop postgresql@14
brew uninstall --force postgresql@14
rm -rf /opt/homebrew/var/postgresql@14
```

## Links

- https://wiki.postgresql.org/wiki/Homebrew
- https://www.moncefbelyamani.com/how-to-install-postgresql-on-a-mac-with-homebrew-and-lunchy/
- https://www.sqlshack.com/setting-up-a-postgresql-database-on-mac/
- https://www.mariadcampbell.com/blog/changing-your-homebrew-postgresql-configuration-from-trust-to-md5/