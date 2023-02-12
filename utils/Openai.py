# Openai.py

import openai

import os


openai.api_key = str(os.getenv('OPENAI_TOKEN'))

def prompt_openai(word):
    try:
        completion = openai.Completion.create(engine="text-davinci-003",temperature= 0.5, prompt=word,max_tokens=1024)
        return completion.choices[0].text
        
    except openai.error.InvalidRequestError:
        print("[*] Prompt to many words ..., Cutting down")
        return prompt_openai("\n".join(word.split('\n')[:-1]))



        