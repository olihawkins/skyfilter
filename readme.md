# skyfilter

Read and process data from the Bluesky firehose.

## Environment variables

The project is set up to use `dotenv` to load environment variables from a file in the project root called `.env` (which is gitignored).

The following environment variables should be defined in `.env` to connect to Postgres.

```zsh
DB_HOST=localhost
DB_PORT=5432
DB_NAME=skyfilter
DB_USER=postgres_user_name
DB_PASS=postgres_user_passworrd
```

You can stream from the Bluesky firehose without authentication, but if you want to make follow up requests for more detailed data on individual posts using the `fetch_post_thread` function in `process.py` you should also define the following environment variables with your Bluesky credentials.

```zsh
BSKY_USER=usernname.bsky.social
BSKY_PASS=bluesky_password
```

## Streaming

Run `stream` as a module to start streaming.

```zsh
python -m skyfilter.stream
```

Send SIGINT with Ctrl + C to shut down gracefully.

## Environment

### Pipenv setup

See the next section for the equivalent setup with pip.

#### Create the environment

```zsh
pipenv install --python 3.10.13
```

#### Install packages

```zsh
pipenv install ipython atproto "psycopg[binary]" python-dotenv
```

#### Activate the environment

```zsh
pipenv shell
```

#### Deactivate the environment

```zsh
exit
```

### Pip setup

#### Create the environment

```zsh
/usr/bin/python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
```

#### Install packages

```zsh
pip install ipython atproto "psycopg[binary]" python-dotenv
```

#### Activate the environment

```zsh
source .venv/bin/activate
```

#### Deactivate the environment

```zsh
deactivate
```

## Links

- [AT Protocol SDK for Python](https://atproto.blue/en/latest/index.html)
- [Firehose documentation](https://atproto.blue/en/latest/atproto_firehose/index.html)
- [AT Protocol for Python on Github](https://github.com/MarshalX/atproto)
- [Firehose example code](https://github.com/MarshalX/atproto/tree/main/examples/firehose)