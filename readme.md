# skyfilter

Read and process data from the Bluesky firehose.

## Environment

### Pipenv setup

See the next section for the equivalent setup with pip.

#### Create the environment

```zsh
pipenv install --python 3.10.13
```

#### Install packages

```zsh
pipenv install ipython atproto "psycopg[binary]"
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
pip install ipython atproto "psycopg[binary]"
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

AT Protocol SDK for Python
https://atproto.blue/en/latest/index.html

Firehose documentation
https://atproto.blue/en/latest/atproto_firehose/index.html

AT Protocol for Python on Github
https://github.com/MarshalX/atproto

Firehose example code
https://github.com/MarshalX/atproto/tree/main/examples/firehose