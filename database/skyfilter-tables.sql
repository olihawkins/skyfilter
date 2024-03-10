--create posts
CREATE TABLE posts(
    post_id serial PRIMARY KEY,
    post_uri text NOT NULL UNIQUE,
    post_text text NOT NULL,
    post_created_at timestamp NOT NULL,
    post_catalogued boolean NOT NULL DEFAULT FALSE,
    created_at timestamp NOT NULL DEFAULT now(),
    updated_at timestamp NOT NULL DEFAULT now()
);