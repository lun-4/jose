# JoséCoin Implementation Spec

Set of functions or objects/structures
that a compliant implementation
must provide:

```py

enum AccountType:
  USER = 0
  TAXBANK = 1

class TransferError(Exception):
  pass

class TransferResult:
  attribute message: str
  attribute success: bool

class Account:
  attribute id: int
  methods[...]

# functions to be implemented
create_account(id: int, type: AccountType) -> bool

#: The implementation must create an account for the
#   bot user, which has infinite money, we call this the "sanity check" function
sane(ctx: Context) -> None

## raw operations over IDs
get_account(id: int) -> Account

#: A tip, implementations could use an async queue and
#   a background task that commits each transaction to the db
transfer(from: int, to: int, amount: decimal) -> TransferResult
zero(id: int) -> TransferResult
sink(id: int, amount: decimal) -> TransferResult

## operations that are db intensive should return
#   async iterators to work with
type AccountIterator AsyncIterator

#: Get all accounts that match a specific type
accounts_by_type(type: AccountType) -> AccountIterator[Account]

#: Get all accounts, ordered by the field
all_accounts(field: str='amount',
             type: AccountType=AccountType.USER,
	     order: int=pymongo.DESCENDING) -> AccountIterator[Account]

#: Get all accounts
guild_accounts(guild: discord.guild,
               field: str='amount') -> AccountIterator[Account]

#: This should be cached and updated with each transfer
get_gdp() -> decimal

#: get the ranking of a user(both global and local)
ranks(user_id: int, guild: discord.Guild) -> tuple(4)

## Misc functions

pricing(ctx: Context, base_tax: decimal) -> TransferResult

#: Probability of getting coins per message
get_probability(account: Account) -> float

```

Account object
```py
# For users, type 0
{}

# For taxbanks, type 1
{}
```
