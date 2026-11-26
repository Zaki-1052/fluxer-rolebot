# fluxer-rolebot

A reaction role bot for [Fluxer](https://fluxer.app). Administrators configure one or more messages and associate emojis with roles on each. When users react, they automatically receive or lose the corresponding role.

Want to use this without hosting?

[Invite Here](https://web.fluxer.app/oauth2/authorize?client_id=1472276231307042825&scope=bot&permissions=1342377024)

[Support Server](https://fluxer.gg/kOPptC9Q)

## Setup

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

1. Copy `.env.example` to `.env` and fill in your bot token:

   ```
   cp .env.example .env
   ```

2. Install dependencies:

   ```
   uv sync
   ```

3. Run the bot:
   ```
   uv run main.py
   ```

### Docker

```
make build
make run
```

The bot stores data in a `data/` directory mounted as a volume. See the [Makefile](Makefile) for details.

## Commands

All commands currently require administrator permissions. The default prefix is `!` (configurable via `COMMAND_PREFIX`).

| Command                                | Description                                                             |
| -------------------------------------- | ----------------------------------------------------------------------- |
| `!sendmessage <text>`                  | Send a message as the bot and configure it as a role react message      |
| `!setmessage <message_link>`           | Set an existing message as a role react message                         |
| `!editmessage [message_link] <text>`   | Edit the text of a configured role react message                        |
| `!listmessages`                        | List all configured role react messages                                 |
| `!removemessage [link or ID]`          | Remove a role react message and its associations (defaults to latest)   |
| `!add @Role <emoji>`                   | Add an emoji-role association to the most recently configured message   |
| `!remove <emoji>`                      | Remove an emoji-role association from the most recently configured message |

## Environment Variables

| Variable         | Default      | Description                                                                                                                            |
| ---------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| `FLUXER_TOKEN`   | _(required)_ | Bot token from Fluxer                                                                                                                  |
| `PREFIX_TYPE`    | `default`    | Can be `spaced` or `default`. Default has the format `<prefix>setmessage` for example, and Spaced has the format `<prefix> setmessage` |
| `COMMAND_PREFIX` | `!`          | Prefix for bot commands                                                                                                                |
| `DB_PATH`        | `db.json`    | Path to the TinyDB database file                                                                                                       |
