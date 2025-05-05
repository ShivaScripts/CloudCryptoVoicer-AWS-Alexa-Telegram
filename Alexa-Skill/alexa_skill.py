import json
import requests

def lambda_handler(event, context):
    if event['request']['type'] == 'IntentRequest':
        intent_name = event['request']['intent']['name']

        # Top Gainer Intent
        if intent_name == 'TopGainerIntent':
            resp = requests.get(
                'https://api.coingecko.com/api/v3/coins/markets',
                params={'vs_currency': 'usd', 'order': 'percent_change_24h', 'per_page': 10, 'page': 1}
            )
            data = resp.json()
            data.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)
            top = data[0]
            name = top['name']
            change = top['price_change_percentage_24h']

            speech = f"<speak>The top gainer in the last 24 hours is {name}, up {abs(change):.2f} percent.</speak>"

        # Top Loser Intent
        elif intent_name == 'TopLoserIntent':
            resp = requests.get(
                'https://api.coingecko.com/api/v3/coins/markets',
                params={'vs_currency': 'usd', 'order': 'percent_change_24h', 'per_page': 10, 'page': 1}
            )
            data = resp.json()
            data.sort(key=lambda x: x['price_change_percentage_24h'])  # Ascending = loser first
            top = data[0]
            name = top['name']
            change = top['price_change_percentage_24h']

            speech = f"<speak>The top loser in the last 24 hours is {name}, down {abs(change):.2f} percent.</speak>"

        # GetCryptoPriceIntent (NEW)
        elif intent_name == 'GetCryptoPriceIntent':
            crypto_name = event['request']['intent']['slots']['CryptoName']['value']
            resp = requests.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={'ids': crypto_name.lower(), 'vs_currencies': 'usd'}
            )
            data = resp.json()
            if crypto_name.lower() in data:
                price = data[crypto_name.lower()]['usd']
                speech = f"<speak>The current price of {crypto_name} is {price} U.S. dollars.</speak>"
            else:
                speech = f"<speak>I'm sorry, I couldn't find the price for {crypto_name}.</speak>"

        # Unknown Intent
        else:
            speech = "<speak>Sorry, I didn't understand that.</speak>"

        return {
            'version': '1.0',
            'response': {
                'outputSpeech': {
                    'type': 'SSML',
                    'ssml': speech
                },
                'shouldEndSession': True
            }
        }

    # Non-Intent Requests
    return {
        'version': '1.0',
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': "Sorry, I didn't understand that."
            },
            'shouldEndSession': True
        }
    }
