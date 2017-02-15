Admin Commands
===

Admin commands in josé can only be invoked by admin accounts, the list of those accounts is in the `ADMIN_IDS` array in `josecommon.py`, changing that will change the people that can issue those commands

When the user isn't on the `ADMIN_IDS` list, josé will throw a `joseerror.PermissionError` Exception

 * `!reload modpath`
  * Reloads a module, usually used when minor updates happen
 * `!unload modpath`
  * Completly unloads a module
 * `!loadmod class@modpath`
  * Loads a module in `/ext/modpath.py` with the class representing it


 * `!shutdown`
  * Pretty self explanatory
 * `!pstatus`
  * Change *Playing* status
 * `!distatus`
  * Shows pings to the `discordapp.com` server, and some additional checking
   for latency
 * `!eval code`
  * Evaluates Python code
 * `!rplaying`
  * Rotates the playing status
 * `!tempadmin userid`
  * Makes a user a temporary admin
  * Temporary admins have all admin permissions until josé restarts.
