import openai
from util.openai import APIKEY
import logging


logging.basicConfig(level=logging.INFO)
client = openai.OpenAI(api_key=APIKEY)

def call_gpt(msg):
    '''
    Calls the OpenAI API and fetches a response from chatGPT 3.5 turbo.
    
    Returns the message response string from chatGPT
    '''
    try:
        output = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user',
                    'content': msg}]
        )

        return output.choices[0].message.content
    
    except Exception as e:
        logging.error(f'Failed to query chatGPT. Error: {e}')
        return None



if __name__ == '__main__':
    # print(APIKEY)
    msg = 'write me a haiku.'
    print(call_gpt(msg))