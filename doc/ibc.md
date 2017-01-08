Inter Bot Communication
========================

Jose *is going to* have system calls to communicate with other bots on the same channel
The basis is the `!syscall` command that recieves JSON data and based on that it makes another command and returns the result(in JSON as well)

## General syscall request

```javascript
{
    'whoami': discord_id, //str
    "callnumber": number_of_syscall, //int
    "arguments": [ // parameters to the call
        arg1,
        arg2,
        arg3,
        ...,
        argn
    ]
}
```

### Example
```javascript
// Should return "OK"
{
    "callnumber": 2,
    "arguments": ["a", 2]
}


// Should return 2
{
    "callnumber": 3,
    "arguments": ["a"]
}
```

## General syscall numbers

| Number | Description   |
| ------ | ------------- |
| 0   | send ping |
| 1   | send message      |
