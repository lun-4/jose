# Contributing to José

Thank you for taking your time to contribute to this ~~awesome~~ bot! :ok_hand:

## Important stuff
 * [Documentation](https://github.com/lkmnds/jose/blob/master/doc/)
 * [Issue Tracker](https://github.com/lkmnds/jose/issues)
 * [Discord Server / José Testing Enviroment / JTE](https://discord.gg/5ASwg4C)

## [Installing](#installing)

 * Install José using the [Manual](https://github.com/lkmnds/jose/issues).

## [Reporting Bugs](#reporting-bugs)

First you need to see if it is an actual bug **and** it is reproducible. It is
recommended to ask in the Discord Server if the "bug" is actually supposed to happen or not.

If it is a bug you need to define the severity of it when issuing.
 * **Minor** bugs:
   * Usually they don't need an actual issue, use the JTE's `#support` channel for that
   * Example:
    * A command that didn't work when given nothing as argument
    * An alias that didn't work.

 * **Normal** bugs:
  * Anything that causes Exceptions that are thrown to the user/logs
  * Examples:
    - [Exception thrown then `!fw` was made without any text](https://a.desu.sh/rsahgm.png)
    - Performance issues(Things taking longer than expected)
      * [#3 - Handle commands in an asynchronous way](https://github.com/lkmnds/jose/issues/3)

 * **Major** bugs: Security vulnerabilities, Database integrity,
  * They **shouldn't** be issued while no fixes have been done. **Report Major bugs through a private/more direct channel.**
    * My Discord ID is `Luna#4677`. Feel free to talk about it.
    * You can send emails to `jose.lkmnds@mailhero.io` if that's more your thing.
  * Examples:
    - SQL Injections
    - Accessing what you aren't supposed to access(admin commands mostly)

### How to make (:ok_hand: good shit :ok_hand:) Bug Reports

 * [Report in the Issue Tracker](https://github.com/lkmnds/jose/issues)
 * Use a **good** title.
 * Show steps made to **reproduce** the bug

Fill this example with your issue and you are on track :joy: :ok_hand:

```markdown
## Context
[provide details on the issue]

## Steps
[list the steps to recreate the issue, example below]
1. Command: `!fw`
2. Exception happened.

## Expected Result
[what you would expect from the steps provided]

## Possible fixes
[optional, but suggest fixes or reasons for the bug, example below]
 * `!fw` didn't check for the arguments provided

## Screenshot
[if relevant, include screenshots!]
```

## Submitting Changes

[TODO]
