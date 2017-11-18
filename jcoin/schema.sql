CREATE TABLE IF NOT EXISTS accounts (
       user_id bigint,

       /* To be used as decimal on Python land */
       amount text,
       taxpaid text,

       /* for j!steal statistics */
       steal_uses int,
       steal_success int,

       trust_score int,
);


CREATE TABLE IF NOT EXISTS taxbanks (
       guild_id bigint,
       amount text,
);

/* The Log of all transactions */
CREATE TABLE IF NOT EXISTS transactions (
       txtimestamp timestamp without time zone,
       id_from bigint,
       id_to bigint,
       amount text,
);

/* If we want, we *could* group transactions */
CREATE TABLE IF NOT EXISTS blockchain (
       prev_hash text,
       blockstamp timestamp without time zone,
       blobk_data jsonb,
);
