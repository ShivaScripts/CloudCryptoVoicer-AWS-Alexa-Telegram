import json
import requests
import boto3
from datetime import datetime

# AWS config
BUCKET_NAME = 'crypto-price-data-shivam-s3'
FROM_EMAIL = 'shivamdeore160@gmail.com'
TO_EMAIL = 'shivamdeore161@gmail.com'

# Telegram Bot config
TELEGRAM_BOT_TOKEN = '7711424238:AAGjml36h45JsP-W2GgsI81KOOi7ECf-Q-Y'
CHAT_ID = '1081928215'

# AWS clients
ses_client = boto3.client('ses', region_name='us-east-1')
s3_client = boto3.client('s3')
dynamodb_client = boto3.client('dynamodb')


def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'percent_change_24h',
        'per_page': 10,
        'page': 1,
    }
    response = requests.get(url, params=params)
    data = response.json()
    data.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)
    return data


def send_email(subject, body):
    response = ses_client.send_email(
        Source=FROM_EMAIL,
        Destination={'ToAddresses': [TO_EMAIL]},
        Message={
            'Subject': {'Data': subject},
            'Body': {'Text': {'Data': body}}
        }
    )
    return response


def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    response = requests.post(url, data=payload)
    return response


def upload_to_s3(data):
    now = datetime.now()
    file_name = f'crypto/hourly/{now.year}/{now.month}/{now.day}/{now.hour}.json'
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=json.dumps(data),
        ContentType='application/json'
    )


def log_to_dynamodb(status, message):
    timestamp = datetime.now().isoformat()
    dynamodb_client.put_item(
        TableName='CryptoNotificationStatus',
        Item={
            'timestamp': {'S': timestamp},
            'status': {'S': status},
            'message': {'S': message}
        }
    )


def lambda_handler(event, context):
    crypto_data = get_crypto_data()

    # Extract top 5 gainers and losers
    top_gainers = crypto_data[:5]
    top_losers = crypto_data[-5:][::-1]

    # Prepare email body
    subject = "Hourly Crypto Report: Top 5 Gainers and Losers"
    body = "Top 5 Gainers:\n"
    for coin in top_gainers:
        body += f"- {coin['name']} ({coin['price_change_percentage_24h']:.2f}%)\n"

    body += "\nTop 5 Losers:\n"
    for coin in top_losers:
        body += f"- {coin['name']} ({coin['price_change_percentage_24h']:.2f}%)\n"

    # Send Email and Log Status
    email_response = send_email(subject, body)
    log_to_dynamodb('Email Sent', json.dumps(email_response))

    # Upload full data to S3
    upload_to_s3({
        'top_gainers': top_gainers,
        'top_losers': top_losers
    })

    # 🚨 Send Telegram Alert if Bitcoin moved ±2% and Log Status
    for coin in crypto_data:
        if coin['id'] == 'bitcoin':
            change = coin['price_change_percentage_24h']
            if abs(change) >= 2:
                message = f"🚨 Bitcoin Alert: {change:.2f}% change in last 24h!"
                telegram_response = send_telegram_alert(message)
                log_to_dynamodb('Telegram Alert Sent', json.dumps(telegram_response))
            break

    return {
        'statusCode': 200,
        'body': json.dumps('Email sent, data stored in S3, and Telegram alert (if triggered) sent!')
    }
