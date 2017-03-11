# José Modules: Events

### `on_message`
 * Called when any messages go into jose, but no commands
 * Receives a `discord.Message` object and a `josecommon.Context` object

### `any_message`
 * Called when any messages go into jose, including commands
 * Receives a `discord.Message` object and a `josecommon.Context` object

### `server_join`
 * Called when José joins a new server/guild.
 * Receives a `discord.Server` object and a `discord.Channel` representing the default channel for that server

### `client_ready`
 * Called the same way as `discord.Client.on_ready`
 * **Can be called more than one time**
 * Receives a `discord.Client` object

### `member_join`
 * Called the same way as `discord.Client.on_member_join`
 * Receives `discord.Member` object

### `member_remove`
 * Called the same way as `discord.Client.on_member_remove`
 * Receives `discord.Member` object
