CREATE TABLE IF NOT EXISTS clients (
       /* Clients connecting to the API should use a token. */
       client_id text PRIMARY KEY,
       token text NOT NULL,
       client_name text NOT NULL,
       description text DEFAULT 'no description',

       /*
       0 = only fetching
       1 = full control
       */
       auth_level int NOT NULL DEFAULT 0
);

/* member table of all discord users José sees to write JOIN queries, updated in the bot itself */
CREATE TABLE IF NOT EXISTS members (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    PRIMARY KEY(guild_id, user_id)
);

/* both users and taxbanks go here */
CREATE TABLE IF NOT EXISTS accounts (
       account_id bigint PRIMARY KEY NOT NULL,
       account_type int NOT NULL,
       amount money DEFAULT 0
);

CREATE VIEW account_amount as
SELECT account_id, account_type, amount::money::numeric::float8
FROM accounts;

/* only user accounts here */
CREATE TABLE IF NOT EXISTS wallets (
       user_id bigint NOT NULL REFERENCES accounts (account_id) ON DELETE CASCADE,

       taxpaid money DEFAULT 0,
       hidecoins boolean DEFAULT false,

       /* for j!steal statistics */
       steal_uses int DEFAULT 0,
       steal_success int DEFAULT 0
);

CREATE VIEW wallets_taxpaid as
SELECT user_id, taxpaid::numeric::float8, hidecoins, steal_uses, steal_success
FROM wallets;

/* The Log of all transactions */
CREATE TABLE IF NOT EXISTS transactions (
       idx serial PRIMARY KEY,
       transferred_at timestamp without time zone default now(),
       sender bigint NOT NULL REFERENCES accounts (account_id) ON DELETE RESTRICT,
       receiver bigint NOT NULL REFERENCES accounts (account_id) ON DELETE RESTRICT,
       amount numeric NOT NULL,
       /* so we can search for description='steal', or something */
       description text DEFAULT 'transfer'
);

/* If we want, we *could* group transactions */
CREATE TABLE IF NOT EXISTS blockchain (
       prev_hash text,
       blockstamp timestamp without time zone,
       block_data jsonb
);


/* Steal related stuff */
CREATE TYPE cooldown_type AS ENUM ('prison', 'points');

CREATE TABLE IF NOT EXISTS steal_points (
    user_id bigint NOT NULL REFERENCES accounts (account_id),
    points int NOT NULL DEFAULT 3,
    primary key (user_id)
);

CREATE TABLE IF NOT EXISTS steal_cooldown (
    user_id bigint NOT NULL REFERENCES accounts (account_id),
    ctype cooldown_type NOT NULL,
    finish timestamp without time zone default now(),
    primary key (user_id, ctype)
);

CREATE TABLE IF NOT EXISTS steal_grace (
    user_id bigint NOT NULL PRIMARY KEY,
    finish timestamp without time zone default now()
);

CREATE VIEW steal_state as
SELECT (steal_points.user_id, points, steal_cooldown.ctype, steal_cooldown.finish) FROM steal_points
JOIN steal_cooldown ON steal_points.user_id = steal_cooldown.user_id;
