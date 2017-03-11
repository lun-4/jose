JoséCoin
====

JoséCoins(Abbreviated as JC) are the currency of José, used usually for paying taxes to use other commands.
JC Wallets aren't created automatically, this is a design & performance choice. To create, use `j!account`.

### JoséCoin Generation

Each message you send (to a server where José is, obviously), has a 1% random chance of receiving a reward.
That reward can be 0.2, 0.6, 1, 1.2 or 1.5 JC. José reacts with :moneybag: when you receive a reward.
The more tax you pay increases your probability of getting JoséCoins, with the maximum amount being 4.20%.

### Command list

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!account` | Creates a new JoséCoin account | |
`j!prices` | See current pricing for commands | |
`j!wallet [@someone]` | Shows your account's balance  | |
`j!write @someone amount` | Changes someone's wallet balance **[ONLY ADMINS]** | `j!write @José 42.69` |
`j!jcsend @someone amount` | Sends JoséCoins to someone | `j!jcsend @José 3` |
`j!top10 amount` | Shows the 10 people (or a different amount if a variable is put in as `amount`) that have the most JoséCoins | `j!top10 12` |
`j!ltop10 amount` | Shows the 10 people (or a different amount if a variable is put in as `amount`) that have the most JoséCoins in your server | `j!ltop10 13` |
`j!jcprob` | Shows your probability of getting JoséCoins per message | |

### Stealing System

Stealing System works by using `j!steal`, where you can steal an arbritary amount
of JC from someone's wallet. That comes with a cost though: You have a chance of getting
caught and when you're arrested, you receive an 8 hours cooldown, as well as paying the bank half of the JC you tried to steal.
If you don't have enough to pay the fine, your wallet goes down to 0 JC, and the amount you had gets converted to hours.

If you succeed, the victim has a grace period of 3 hours
where no one can steal from the victim again. Admins get a grace period of 6 hours, however.

 * If you try to steal from someone who is in :angel: grace period :angel:, they get notified
 * The victim gets notified when someone steals from them
 * You don't have a cooldown when you aren't arrested
 * You are arrested if you try to steal from José, or steal a higher amount than the victim's wallet
 * If you use `j!steal` 3 times in a row and succeed in all 3 of them, you'll then have to use `j!steal` again and wait 8 hours to get 3 more uses.

When you get arrested, you pay half the amount you want to steal to José,
and your chances of getting more JoséCoins per message halves.

`j!hsteal` for more details.

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!steal @mention amount` | Steals from someone | `j!steal @Jose 20` | `j!roubar`
`j!stealstat` | Your status in the stealing business | |
`j!stealreset userid` | Resets an user's status in stealdb **[ONLY ADMINS]** | |

### Bank System

The banking system has two main parts, the Taxbank and Storagebank.

The Taxbank holds any money that was spent on taxes from either commands that require spending JoséCoins,
or losing money because you attempted to steal from someone.
Taxbanks are by server, and therefore the amount of money in the Taxbank is determined by the taxes paid in that specific server.

The Storagebank holds money that users stored in the bank, normally so that others cannot steal it from them.
Storagebanks are tied to user accounts, if you store money in a Storagebank, you can retrieve it from any bank on any server.

There's also a feature that relates to both the Storagebank and Taxbank: loaning. You can ask for a loan from a Taxbank,
as long as it has the amount of JoséCoins you're asking for, and you don't already have a loan, or are storing money in a StorageBank.
There is a 25% tax on loans, therefore, if you ask for a loan of 1 JC, you'll have to pay back 1.25 JC.

Command | Description | Example | Alias
------------- | ------------- | ------------- | -------------
`j!bank` | Shows the amount of JC in the Taxbank, Storagebank, and what's stored in your personal bank | |
`j!store amount` | Stores the amount of JoséCoins you specify in the StorageBank | `j!store 22` |
`j!withdraw amount` | Withdraws the amount of JoséCoins you specify from the StorageBank | `j!withdraw 22` |
`j!loan amount|"pay"|"see"` | Requests a loan from the TaxBank according to amount, you can also see how much is being lent to you, and pay back your loan | `j!loan 10`, `j!loan see`, or `j!loan pay` |

### Coming Soon™

 * `j!heist`
 * `j!donate`