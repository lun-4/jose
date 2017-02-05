Extension API, EAPI
=======

The EAPI is a set of methods given to extensions by `jaux.Auxiliar` and `jcommon.Extension`

## List of methods in the EAPI

 * `self.is_admin(user_id)`
  * This function is a *coroutine*
  * **Returns** `bool`
  * Checks if user_id is capable of doing ADMIN stuff
  * Usually for commands like `!eval` and `!shutdown`

 * `self.codeblock(language, string)`
  * Just formats `string` to a Markdown codeblock using `language`
  * **Returns** `str`: the Markdown formatted string

 * `self.noasync(function, arguments)`
  * Runs a function in an async context
  * Example:
  ```python
  # checks if a user is admin but without async
  self.noasync(self.is_admin, [message.author.id])
  ```

 * `self.is_owner()`
  * Just like `self.is_admin`, but checks the author of the current message
  * **Returns** `bool`

  * `self.cbk_new(callback_id, function, sec)`
   * `callback_id`: `str`, the string that represents that callback
   * `function`: any function that is a **coroutine**
   * `sec`: `int`
   * Sets a function to be called every `sec` seconds
   * Made for functions that need to save stuff by every length of time, example:
   ```python
   # save databases every 5 minutes
   await self.set_callback('mydatabase', self.save_database, 300)
   ```

### Planned features/features to be documented in the EAPI

 * `self.cbk_call(callback_id)`
 * `self.cbk_remove(callback_id)`
