=================
JoséCoin REST API
=================

--------
Base URL
--------

All API requests are based off of this url:

.. code-block :: http

  https://jose.lnmds.me/api/

-------------
Authorization
-------------

All requests must contain an ``Authorization`` header containing your applications API key.

Not sending this will result in your requests failing.

======
Routes
======

----------
Get Wallet
----------

.. code-block :: http

  GET /wallets/:wallet_id

Get a wallet by it's ID, this works for users and taxbanks.

-------------
Create Wallet
-------------

.. code-block :: http

  POST /wallets/:wallet_id

Create a wallet using it's ID - the ID is the user or guild ID the wallet will be for.

The request must contain a json payload containing the wallet ``type``, being either ``0`` for 'user' or ``1`` for 'taxbank'.

-------------
Delete Wallet
-------------

.. code-block :: http

  DELETE /wallets/:wallet_id

Permanently delete a wallet using it's ID. This action can not be undone.

------------------
Transfer to Wallet
------------------

.. code-block :: http

  POST /wallets/:wallet_id/transfer

Transfer from a wallet to another. The wallet ID in the request URI is the wallet being transferred **from**.

The request body must contain a ``receiver`` as an integer wallet ID and an ``amount`` as a string.

.. note:: The amount can not be negative to transfer from the receivers account, you have to transfer with the other wallet.

-----------
Lock Wallet
-----------

.. code-block :: http

  POST /wallets/:wallet_id/lock

Lock a wallet from being used.

-------------
Unlock Wallet
-------------

.. code-block :: http

  DELETE /wallets/:wallet_id/lock

Unlock a wallet if it's locked.

------------
Reset Wallet
------------

.. code-block :: http

  POST /wallets/:wallet_id/reset

Reset a wallet. This sets the amount to 0 and resets any other statistics associated with it.

---------------------
Increment steal usage
---------------------

.. code-block :: http

  POST /wallets/:wallet_id/steal_use

Increment the wallet's `steal_uses` field by one.

---------------------
Mark successful steal
---------------------

.. code-block :: http

  POST /wallet/:wallet_id/steal_success

Increment the wallet's `steal_success` field by one.

-----------
Wallet Rank
-----------

.. code-block :: http

  GET /wallets/:wallet_id/rank

Get a wallets rank.
By default this returns the global rank, specifying a guild ID as a json parameter will also return the local ranking.

------------
JoséCoin GDP
------------

.. code-block :: http

  GET /gdp

Gets the GDP of the economy.

----------------
Coin Probability
----------------

.. code-block :: http

  GET /wallets/:wallet_id/probability

Get the probability of this wallet receiving random JoséCoins by sending messages.

------------
Get Accounts
------------

.. code-block :: http

  GET /wallets

To receive different top lists you can specify different, mostly optional query parameters.

The only required paramter is the ``key`` to specify by which criteria accounts get sorted.

========= ======= =======
parameter type    default
========= ======= =======
key       string
reverse   boolean false
guild_id  integer
limit     integer 20
========= ======= =======

