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

/* both users and taxbanks go here */
CREATE TABLE IF NOT EXISTS accounts (
       account_id bigint PRIMARY KEY NOT NULL,
       account_type int NOT NULL,
       amount text DEFAULT '0'
);

/* only user accounts here */
CREATE TABLE IF NOT EXISTS wallets (
       user_id bigint NOT NULL REFERENCES accounts (account_id) ON DELETE CASCADE,

       taxpaid text DEFAULT '0',

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
       amount text NOT NULL
);

/* If we want, we *could* group transactions */
CREATE TABLE IF NOT EXISTS blockchain (
       prev_hash text,
       blockstamp timestamp without time zone,
       block_data jsonb
);
