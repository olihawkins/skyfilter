--create post_statuses:
CREATE TABLE post_statuses(
    status_id serial PRIMARY KEY,
    status_name text NOT NULL, 
    created_at timestamp NOT NULL DEFAULT now(),
    updated_at timestamp NOT NULL DEFAULT now()
);

--create posts
CREATE TABLE posts(
    post_id serial PRIMARY KEY,
    post_uri text NOT NULL UNIQUE,
    post_text text NOT NULL,
    post_created_at timestamp NOT NULL,
    post_status_id int NOT NULL DEFAULT 1,
    created_at timestamp NOT NULL DEFAULT now(),
    updated_at timestamp NOT NULL DEFAULT now(),
    FOREIGN KEY(post_status_id) REFERENCES post_statuses(status_id)
);

--create images
CREATE TABLE images(
    image_id serial PRIMARY KEY,
    image_url text NOT NULL,
    image_filepath text NOT NULL,
    image_alt text NOT NULL,
    image_height int,
    image_width int,
    image_score float,
    post_id int NOT NULL,
    created_at timestamp NOT NULL DEFAULT now(),
    updated_at timestamp NOT NULL DEFAULT now(),
    FOREIGN KEY(post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);