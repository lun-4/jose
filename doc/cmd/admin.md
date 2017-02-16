Admin Commands
===

Admin commands in josé can only be invoked by admin accounts, the list of those accounts is in the `ADMIN_IDS` array in `josecommon.py`, changing that will change the people that can issue those commands

When the user isn't on the `ADMIN_IDS` list, josé will throw a `joseerror.PermissionError` Exception

 * `j!reload modpath`
  * Reloads a module, usually used when minor updates happen
 * `j!unload modpath`
  * Completly unloads a module
 * `j!loadmod class@modpath`
  * Loads a module in `/ext/modpath.py` with the class representing it


 * `j!shutdown`
  * Pretty self explanatory
 * `j!pstatus`
  * Change *Playing* status
 * `j!distatus`
  * Shows pings to the `discordapp.com` server, and some additional checking
   for latency
 * `j!eval code`
  * Evaluates Python code
 * `j!rplaying`
  * Rotates the playing status
 * `j!tempadmin userid`
  * Makes a user a temporary admin
  * Temporary admins have all admin permissions until josé restarts.
