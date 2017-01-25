José's Modules
============

José's code is separated in 3 parts:
 * `main`, located at `jose-bot.py`. which has some commands and the discord.py events
 * `ext`, located at `ext/`. jose's extensions, most of the functionality is there
 * `jcoin`, located at `jcoin/josecoin.py` just for JoseCoin

Some code is in `/contrib`, they are just tools to help with some stuff like:
 * Reading the josecoin journals
 * Backup the meme database
 * Apply filter to the global text database

Each module is described in the form `class@file`.

### List of Modules
 * `jose` is the main module, which can load the others
 * `joseArtif@joseartif`


### Loading of a Module(`jose.load_ext`)
 * To load a module, you need the file of that module and the class that represents it.
 * If that module was already loaded, it's `ext_unload` method is called
 * Else, `load_ext` makes an instance of the class and puts that in the module dictionary in the form `self.modules[module_name]['inst']`

 * When instantiated, its `ext_load` method is called
 * After that, `load_ext` goes through all methods of that instance
  * If the method starts with `c_`, this method becomes a command:

```python
    async def c_ping(self, message, args):
        await self.say("pong")
```

  * If the method starts with `e_`, it becomes an [event handler](https://github.com/lkmnds/jose/blob/master/doc/events.md)

```python
    async def c_any_message(self, message):
        await self.say("I received a message: %s" % message)
```

 * If any errors happened and that was before any connection to Discord was made(before login), it exits.
 * ELSE, if it was already connected to Discord, it sends emoji based on the status of load_ext:
  * `:ok_hand:` / :ok_hand: for success
  * `:train:` / :train: for things that happened while loading
  * `:poop:` / :poop: for errors

### Making a Module

 * To make a module that goes in the `ext`(which is probably what you want), you need to copy the `ext/example_module.py` file into `ext/yourmodule.py`. this file already loads `joseauxiliar` and loads some useful methods like `self.say` and `self.is_admin`
 * Change `JoseExtension` to the name of yourmodule
 * Use the templates for `ext_load`, `ext_unload` and `c_command` to make your own things
 * After that, add `load_module('yourmodule', 'ModuleClass')` to `jose-bot.py`, before the event table declaration, after the declaration of `load_module`
 * Reboot josé to load the module on startup and wait.
 * If you have any problems and want to reload your module, edit it and then use the `!reload yourmodule` command, e.g `!reload josemath`

### What modules need to have
 * `ext_load` Method
  * This method is a *coroutine*
  * `ext_load` usually has the code for when a method is loading, gathering databases, etc
  * Returns a tuple(example, `t`):
    * `t[0]` is the result of the loading, `True` or `False`
    * `t[1]` is the message of error, this is only shown to the console if `t[0]` is `False`
 * `ext_unload` Method
  * This method is a *coroutine*
  * `ext_unload` usually has the code for when a method is unloading, saving databases, etc
  * Returns a tuple(example, `t`):
    * `t[0]` is the result of the loading, `True` or `False`
    * `t[1]` is the message of error, this is only shown to the console if `t[0]` is `False`
