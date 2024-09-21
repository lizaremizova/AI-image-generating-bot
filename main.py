import json
import time
import telebot
import requests
from PIL import Image
from io import BytesIO
import base64
import os
from config import SECRET_KEY, API_KEY, API_TOKEN


class Text2ImageAPI:

    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            time.sleep(delay)

    def save_image(self, base64_string, file_path):
        decoded_data = base64.b64decode(base64_string)
        image = Image.open(BytesIO(decoded_data))
        image.save(file_path)



if __name__ == '__main__':
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', API_KEY, SECRET_KEY)
    model_id = api.get_model()
    uuid = api.generate("Mark- RVT student", model_id)
    images = api.check_generation(uuid)[0]

    api.save_image(images, 'result.jpg')

    # with open('result.txt', 'w') as file:
    #     file.write(str(images))



bot = telebot.TeleBot(API_TOKEN)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi there, I am a bot that generates images based on your prompt, describe what would you like me to generate, it will take less than a minute
""")


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def text_to_image(message):
    prompt = message.text
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', API_KEY, SECRET_KEY)
    model_id = api.get_model()
    uuid = api.generate(prompt, model_id)
    images = api.check_generation(uuid)[0]

    api.save_image(images, 'result.jpg')

    with open('result.jpg', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)



bot.infinity_polling()