Admin Commands
===

Admin commands in josé can only be invoked by admin accounts, the list of those accounts is in the `ADMIN_IDS` array in `josecommon.py`, changing that will change the people that can issue those commands

When the user isn't on the `ADMIN_IDS` list, josé will throw a `joseerror.PermissionError` Exception

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!reload mod` | Reload a module(`mod` is the module name, not the module class) | `j!reload josespeak` |
`j!unload mod` | Unload a module(`mod` is the module name, not the module class) | `j!unload josespeak` |
`j!loadmod class@mod` | Load a module(`class` is the module class, `mod` is the module name) | `j!loadmod JoseHelp@josehelp` |
`j!shutdown` | Makes a safe shutdown of José. | |
`j!update` | Makes a `git pull` and then does `j!shutdown`. | |
`j!pstatus` | Change *Playing* status of José | `j!pstatus benis` |
`j!eval code` | Evaluates Python code | `j!eval 2+2` |
`j!tempadmin userid` | Makes an user a temporary admin(admin until josé shuts down). | |
`j!username name` | Changes José's username. | `j!username José` |
`j!announce stuff` | Announces `stuff` to all servers José is currently on | `j!announce dick` |
`j!gcollect` | Triggers Python's Garbage Collection | |
`j!listev` | Shows how many event handlers are there for each event | |
`j!logs num` | Shows `num` last lines from `José.log` | |
