# JoséCoin

JoséCoins(Abbreviated as JC) are the currency of José, used usually for paying taxes to use other commands.
JC Wallets aren't created automatically, this is a design & performance choice. To create, use `j!account`.

## JoséCoin Generation

Each message you send(to a server where José is, obviously), has a 1% random chance of receiving a reward.
That reward can be 0.2, 0.6, 1, 1.2 or 1.5 JC. José reacts with :moneybag: when you receive a reward.

## Command list

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!account` | Creates a new JoséCoin account | |
`j!prices` | See current pricing for commands | |
`j!wallet [@someone]` | Shows your account's balance  | |
`j!write @someone amount` | Changes someone's wallet balance **[ONLY ADMINS]** | |
`j!jcsend @someone amount` | Sends JoséCoins to someone | `j!jcsend @José 3` |
`j!top10` | Shows the 10 people that have the most JoséCoins | |
`j!ltop10` | Shows the 10 people that have the most JoséCoins in your server | |

## Stealing System

Stealing System works by using `j!steal`, where you can steal an arbritary amount
of JC from someone's wallet. That comes with a cost though: You have a chance of getting
caught and when you're arrested, you receive an 8 hours cooldown.

If you succeed, the victim has a grace period of 3 hours
where no one can steal from the victim again.

 * If you try to steal from someone who is in :angel: grace period :angel:, they get notified
 * The victim gets notified when someone steals from them
 * You don't have a cooldown when you aren't arrested
 * You are arrested if you try to steal from José, or steal a higher amount than the victim's wallet
 * If you use `j!steal` 3 times in a row and succeed in all 3 of them, you'll then have to use `j!steal` again and wait 8 hours to get 3 more uses.

`j!hsteal` for more details.

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!steal @mention amount` | Steals from someone | `j!steal @Jose 20` | `j!roubar`
`j!stealstat` | Your status in the stealing business | |
