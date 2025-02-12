import json
from channels.generic.websocket import AsyncWebsocketConsumer

# Global dictionary to track users in rooms
ROOM_USERS = {}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = f"chat_{self.room_name}"

        # Extract username from query string
        query_params = self.scope['query_string'].decode('utf-8')
        self.username = query_params.split('=')[1] if 'username=' in query_params else 'Anonymous'

        # Add the room to the global user tracking dictionary
        if self.room_name not in ROOM_USERS:
            ROOM_USERS[self.room_name] = []
        ROOM_USERS[self.room_name].append(self.username)

        # Add the user to the group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Notify the room that a user has joined and send the updated user list
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'user_list',
                'message': f"{self.username} has joined the room.",
                'user_list': ROOM_USERS[self.room_name],
                'username': "System"
            }
        )

    async def disconnect(self, close_code):
        # Remove the user from the room in the global tracking dictionary
        if self.room_name in ROOM_USERS and self.username in ROOM_USERS[self.room_name]:
            ROOM_USERS[self.room_name].remove(self.username)

            # Notify the room that a user has left and send the updated user list
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'user_list',
                    'message': f"{self.username} has left the room.",
                    'user_list': ROOM_USERS[self.room_name],
                    'username': "System"
                }
            )

        # Remove the user from the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json['username']

        # Broadcast the message to the group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': sender,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event['username']

        # Send the message to the WebSocket
        await self.send(text_data=json.dumps({
            'username': sender,
            'message': message
        }))

    async def user_list(self, event):
        message = event['message']
        user_list = event['user_list']
        sender = event['username']

        # Send the updated user list and the message to the WebSocket
        await self.send(text_data=json.dumps({
            'username': sender,
            'message': message,
            'user_list': user_list
        }))







