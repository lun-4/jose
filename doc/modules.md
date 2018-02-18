José's Modules
============

José's code is separated in 3 parts:
 * `main`, located at `jose-bot.py`, which has some commands and the discord.py events
 * `ext`, located at `ext/`, jose's extensions, most of the functionality is there
 * `jcoin`, located at `jcoin/josecoin.py`, just for JoséCoin

Some code is in `/contrib`, these are just tools to help with some stuff like:
 * Reading the JoséCoin journals
 * Backing up the meme database
 * Applying filters to the global text database

Each module is described in the form `class@file`.

### List of Modules
 * `Jose` is the main module, which can load the others.
 * `JoseDatamosh@josedatamosh`
  * Implements datamosh capabilities using the `j!datamosh <photo_url>` command.
 * `JoseGambling@josegambling`
  * Implements the gambling game, `j!ap`.
 * `JoseIBC@joseibc`
  * Implements Inter-Bot Communication, a project I've been working on from time to time.
 * `JoseMath@josemath`
  * Things related to math! `j!wolframalpha` lives there.
 * `JoseMemes@josememes`
  * Implements the `!meme` command and other things meme-like `j!fullwidth`.
 * `JoseNSFW@josensfw`
  * Just NSFW commands.
 * `JoseSpeak@josespeak`
  * It has the Markov Chain Text Generator code in it and it handles the `on_message` event to generate texts per server.
 * `JoseStats@josestats`
  * Statistics module, number of messages, commands, etc.
 * `JoseXtra@josextra`
  * Extra stuff.

### Process of loading modules(`jose.load_ext`)
 * To load a module, you need the file of that module and the class that represents it.
  * Call it as `await jose.load_ext(name, classname)`.
  * `name` comes from `ext/name.py`
 * If that module was already loaded, its `ext_unload` method is called and it is deleted.
 * `load_ext` makes an instance of the class and puts that in the module dictionary in the form `self.modules[module_name]['inst']`.

 * When instantiated, its `ext_load` method is called.
 * After that, `load_ext` goes through all methods of that instance.
  * If the method starts with `c_`, this method becomes a command:

```python
    async def c_ping(self, message, args, cxt):
        await cxt.say("pong")
```

  * If the method starts with `e_`, it becomes an [event handler](https://github.com/lkmnds/jose/blob/master/doc/events.md)

```python
    async def e_any_message(self, message, cxt):
        await cxt.say("I received a message: %s" % message)

    async def e_on_message(self, message, cxt):
        await cxt.say("I received a message that is not a command: %s" % message)
```

 * If any errors happen before any connection to Discord is made (before login), it exits.
 * ELSE, if it's already connected to Discord, it sends emoji based on the status of load_ext:
  * `:ok_hand:` / :ok_hand: for success
  * `:train:` / :train: for things that happened while loading
  * `:poop:` / :poop: for errors

### Making a Module

**RECOMMENDED READING: (Extension API)[https://github.com/lkmnds/jose/blob/master/doc/extension_api.md]**

 * To make a module that goes in the `ext` (which is probably what you want), you need to copy the `ext/example_module.py` file into `ext/yourmodule.py`. This file already loads `joseauxiliar` and loads some useful methods like `self.say` and `self.is_admin`.
 * Change `JoseExtension` to the name of `yourmodule`.
 * Use the templates for `ext_load`, `ext_unload` and `c_command` to make your own things.
 * After that, add `load_module('yourmodule', 'ModuleClass')` to `jose-bot.py`, `load_all_modules` function.
 * Reboot José to load the module on startup and wait.
  * You can also do `j!loadmod ModuleClass@yourmodule` if you don't want to restart.
 * If you have any problems and want to reload your module, edit it and then use the `j!reload yourmodule` command, e.g `j!reload josemath`.

### What modules need to have
 * An `__init__` Method.
  * Receives a `discord.Client` object.
    * `ext/example_module.py` has the right way to do that.

 * An `ext_load` Method.
  * This method is a *coroutine*.
  * `ext_load` usually has the code for when a method is loading, gathering databases, etc.
  * Returns a tuple(example, `t`):
    * `t[0]` is the result of the loading, `True` or `False`
    * `t[1]` is the message of error, this is only shown to the console if `t[0]` is `False`

 * An `ext_unload` Method.
  * This method is a *coroutine*.
  * `ext_unload` usually has the code for when a method is unloading, saving databases, etc.
  * Returns a tuple(example, `t`):
    * `t[0]` is the result of the loading, `True` or `False`
    * `t[1]` is the message of error, this is only shown to the console if `t[0]` is `False`
