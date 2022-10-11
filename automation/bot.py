import slack
from settings import SLACK_AUTH_TOKEN, SLACK_SIGNING_SECRET
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from automation.WelcomeMessage import WelcomeMessage
from datetime import datetime, timedelta


app = Flask(__name__)

slack_event_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, '/slack/events', app
)

client = slack.WebClient(token=SLACK_AUTH_TOKEN)

BOT_ID = client.api_call("auth.test")['user_id']

message_counts = {}
welcome_messages = {}


# @slack_event_adapter.on('message')
# def message(payload):
#     event = payload.get('event', {})
#     channel_id = event.get('channel')
#     user_id = event.get('user')
#     text = event.get('text')
#     # message_count = message_counts.get('user_id', 0) + 1
#     if BOT_ID != user_id:
#         message_counts['user_id'] = message_counts.get('user_id', 0) + 1
#         client.chat_postMessage(channel=channel_id, text=text)

def send_welcome_message(channel, user):
    welcome = WelcomeMessage(channel, user)
    new_message = welcome.get_message()
    response = client.chat_postMessage(**new_message)
    welcome.timestamp = response['ts']

    if channel not in welcome_messages:
        welcome_messages[channel] = {}
    welcome_messages[channel][user] = welcome


@slack_event_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = event.get('text')

    if user_id is not None and BOT_ID != user_id:
        message_counts['user_id'] = message_counts.get('user_id', 0) + 1

    if text.lower() == 'start':
        send_welcome_message(channel_id, user_id)
        send_welcome_message(f'@{user_id}', user_id)
        pass


@slack_event_adapter.on('reaction_added')
def reaction(payload):
    event = payload.get('event', {})
    channel_id = event.get('item', {}).get('channel')
    user_id = event.get('user')

    if f'@{user_id}' not in welcome_messages:
        return

    welcome = welcome_messages[f'@{user_id}'][user_id]
    welcome.completed = True
    welcome.channel = channel_id
    new_message = welcome.get_message()
    update_message = client.chat_update(**new_message)
    welcome.timestamp = update_message['ts']


@app.route('/count-message', methods=['POST'])
def count_message():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    message_count = message_counts.get('user_id', 0)
    client.chat_postMessage(channel=channel_id, text=f"Message: {message_count}")
    return Response("I got the command"), 200
    pass


SCHEDULED_MESSAGES = [
    {'text': 'First message', 'post_at': (
            datetime.now() + timedelta(seconds=20)).timestamp(), 'channel': 'C01BXQNT598'},
    {'text': 'Second Message!', 'post_at': (
            datetime.now() + timedelta(seconds=30)).timestamp(), 'channel': 'C01BXQNT598'}
]


def list_scheduled_messages(channel):
    response = client.chat_scheduledMessages_list(channel=channel)
    messages = response.data.get('scheduled_messages')
    ids = []
    for msg in messages:
        ids.append(msg.get('id'))

    return ids


def schedule_messages(messages):
    ids = []
    for msg in messages:
        response = client.chat_scheduleMessage(
            channel=msg['channel'], text=msg['text'], post_at=msg['post_at']).data
        id_ = response.get('scheduled_message_id')
        ids.append(id_)

    return ids


if __name__ == "__main__":
    # schedule_messages(SCHEDULED_MESSAGES)
    app.run(debug=True, port=5000)
    pass
