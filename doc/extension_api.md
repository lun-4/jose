Extension API, EAPI
=======

The EAPI is a set of methods given to extensions by `jaux.Auxiliar` and `jcommon.Extension`.

## List of methods in the EAPI

 * `self.is_admin(user_id)`
  * This function is a *coroutine*.
  * **Returns** `True` if user is an Admin(is in `ADMIN_IDS`), else raises `joseerror.PermissionError`.
  * Usually for commands like `!eval` and `!shutdown`.

 * `self.codeblock(language, string)`
  * Just formats `string` to a Markdown codeblock using `language`.
  * **Returns** `str`: the Markdown formatted string.

 * `self.noasync(function, arguments)`
  * Runs an async function when you're not in a async context, like `eval`.
  * Example:
  ```python
  # checks if a user is admin but without async
  self.noasync(self.is_admin, [message.author.id])
  ```

 * `self.is_owner(cxt)`
  * Just like `self.is_admin`, but checks through `cxt`.
  * **Returns** `bool`.

 * `self.cbk_new(callback_id, function, sec)`
  * `callback_id`: `str`, the string that represents that callback.
  * `function`: any function that is a **coroutine**.
  * `sec`: `int`
  * Sets a function to be called every `sec` seconds.
  * Made for functions that need to save stuff by every length of time, example:
  ```python
  # save databases every 5 minutes
  await self.cbk_new('mydatabase', self.save_database, 300)
  ```

 * `self.cbk_call(callback_id)`
  * This function is a *coroutine*.
  * `callback_id`: `str`
  * Calls a callback independent of the time needed to execute it.
  * Example:
  ```python
  async def c_savedb(self, message, args, cxt):
      await self.cbk_call('mydatabase')
  ```

 * `self.cbk_remove(callback_id)`
  * `callback_id`: `str`
  * Removes a callback from the callback dict; not immediately.
  * Example:
  ```python
  async def ext_unload(self, message, args, cxt):
      # remove callbacks on unload
      await self.cbk_remove('mydatabase')
  ```

## List of methods given by `jaux.Auxiliar` only
 * self.json_load(string)
  * This function is a *coroutine*.
  * Loads a JSON string, raises `joseerror.JSONError` on error.

 * self.http_get(url, timeout=5)
  * This function is a *coroutine*.
  * GETs from an url, raises respective errors.

 * self.json_from_url(url, timeout=5)
  * This function is a *coroutine*.
  * Load JSON from an url.

 * self.jcoin_pricing(cxt, amount)
  * This function is a *coroutine*.
  * Does *taxes*, sends `amount` from `cxt.message.author` to its respective taxbank.
