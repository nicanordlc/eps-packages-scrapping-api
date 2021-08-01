# eps-packages-scrapping-api

Fetches your packages that are in the page `eps.com.do`

## Response example

```json
{
    "items": [
        {
            "condition": "NORMAL",
            "trackingNumber": "7492836162530948576612354785947412",
            "content": "puppy",
            "sender": "ebay",
            "weight": "20.00",
            "status": "status1",
            "statusLabel": "intransit",
            "statusFormatted": "customs",
        }
    ]
}
```

## Routes

### `/`

Fetches `eps.com.do` packages and caches the result for half hour
(be conscious, don't spam web pages <3)

### `/now`

Fetches `eps.com.do` every time you request this endpoint
(if you are nervious enough 😱)

## Start server

```bash
pipenv install && pipenv run dev
```

## `config.ini`

You will need to create this fille and set it up with these options in
order to start the server

```ini
[user]
user = ''
password = ''

[server]
cache = 60
```
