CREATE TABLE IF NOT EXISTS clients (
       /* Clients connecting to the API should use a token. */
       client_id serial PRIMARY KEY,
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
)

/* both users and taxbanks go here */
CREATE TABLE IF NOT EXISTS accounts (
       account_id bigint PRIMARY KEY NOT NULL,
       account_type int NOT NULL,
       amount numeric DEFAULT 0
);

/* only user accounts here */
CREATE TABLE IF NOT EXISTS wallets (
       user_id bigint NOT NULL REFERENCES accounts (account_id) ON DELETE CASCADE,

       taxpaid numeric DEFAULT 0,

       /* for j!steal statistics */
       steal_uses int DEFAULT 0,
       steal_success int DEFAULT 0
);


/* The Log of all transactions */
CREATE TABLE IF NOT EXISTS transactions (
       idx serial PRIMARY KEY,
       transferred_at timestamp without time zone default now(),
       sender bigint NOT NULL REFERENCES accounts (account_id) ON DELETE RESTRICT,
       receiver bigint NOT NULL REFERENCES accounts (account_id) ON DELETE RESTRICT,
       amount numeric NOT NULL
);

/* If we want, we *could* group transactions */
CREATE TABLE IF NOT EXISTS blockchain (
       prev_hash text,
       blockstamp timestamp without time zone,
       block_data jsonb
);
