 - **[DESIGN]** Split things up, JoséCoin will have its backend *separated* from the main bot,
   using an HTTP API with authorization, that will make other bots able to use
   JoséCoin features.

 - **[IMPL]** Use an `asyncio.Queue` to make a queue of transactions
   before we commit them to Mongo using a consumer coroutine.

 - **[IDEA]** Bring back loans, but between users
   - Make a *Trust Score* for users, if they don't pay back their
   loans, gotten from another users, their trust score will be lower

   - The maximum amount you can loan is based on that trust score.

 - **[MOD]** Add bail to the stealing business