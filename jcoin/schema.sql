CREATE TABLE IF NOT EXISTS accounts (
       account_id bigint PRIMARY KEY NOT NULL,
       account_type int NOT NULL,
       amount text DEFAULT "0",
);

/* only user accounts here */
CREATE TABLE IF NOT EXISTS wallets (
       user_id bigint NOT NULL REFERENCES accounts (account_id) ON DELETE CASCADE,

       taxpaid text DEFAULT "0",

       /* for j!steal statistics */
       steal_uses int DEFAULT 0,
       steal_success int DEFAULT 0,
);


/* The Log of all transactions */
CREATE TABLE IF NOT EXISTS transactions (
       transferred_at timestamp without time zone,
       sender bigint NOT NULL,
       receiver bigint NOT NULL,
       amount text NOT NULL,
);

/* If we want, we *could* group transactions */
CREATE TABLE IF NOT EXISTS blockchain (
       prev_hash text,
       blockstamp timestamp without time zone,
       block_data jsonb,
);
