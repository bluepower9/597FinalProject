import openai 
from util.openai import APIKEY
import logging


logging.basicConfig(level=logging.INFO)
client = openai.OpenAI(api_key=APIKEY)

def call_gpt(msg, excerpts):
    '''
    Calls the OpenAI API and fetches a response from chatGPT 3.5 turbo.
    
    Returns the message response string from chatGPT
    '''

    context = ' '.join(excerpts)

    try:
        output = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': f'Using only this information, answer the user\'s question: {context}'},
                {'role': 'user', 'content': msg}
            ]
        )

        return output.choices[0].message.content
    
    except Exception as e:
        logging.error(f'Failed to query chatGPT. Error: {e}')
        return None


def get_embeddings(s:str) -> list:
    client.embeddings.create(s)


if __name__ == '__main__':
    # print(APIKEY)
    msg = 'write me a haiku.'
    print(call_gpt(msg))