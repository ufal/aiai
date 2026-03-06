#!/usr/bin/env python

from openai import OpenAI
import base64
import io
import sys

import logging
logging.basicConfig(
    format='%(levelname)s %(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)

# OpenAI key
KEY_PATH = 'apikey.txt'

# OpenRouter key
OR_KEY_PATH = 'apikey_or.txt'

def generate_with_openai(messages, model="gpt-4o-mini", max_tokens=5000, temperature=0):
    # OPENAI or OPENROUTER?
    # OPENROUTER model name always has '/' in it
    use_or = '/' in model

    # Gemini 3 Pro uses reasoning
    extra_body = {}
    if 'gemini-3-pro' in model:
        extra_body = {"reasoning": {"enabled": True}}

    # OPENAI SETUP
    # path to file with authentication key
    key_path = OR_KEY_PATH if use_or else KEY_PATH
    with open(key_path) as infile:
        apikey = infile.read().rstrip()
    try:
        if use_or:
            client = OpenAI(api_key=apikey, base_url="https://openrouter.ai/api/v1")
        else:
            client = OpenAI(api_key=apikey)
    except:
        logging.exception("EXCEPTION Neúspěšná inicializace OpenAI.")

    # https://platform.openai.com/docs/guides/chat/introduction
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=1,
            stop=[],  # can be e.g. stop = ['\n']
            presence_penalty=0,
            frequency_penalty=0,
            logit_bias={},
            extra_headers={ "X-Title": "AIAI" },
            extra_body=extra_body,
        )
        logging.debug(response)
        return response.choices[0].message.content

    except:
        logging.exception("EXCEPTION Neúspěšné generování pomocí OpenAI.")
        return None

def generate_with_openai_responses(prompt, system="You are a helpful assistant.", model="gpt-5-mini", max_tokens=5000):
    # OPENAI SETUP
    # path to file with authentication key
    with open(KEY_PATH) as infile:
        apikey = infile.read().rstrip()
    try:
        client = OpenAI(api_key=apikey)
    except:
        logging.exception("EXCEPTION Neúspěšná inicializace OpenAI.")

    try:
        response = client.responses.create(
            model=model,
            instructions=system,
            input=prompt,
            reasoning={"effort": "low"},
            # reasoning={"effort": "low", "summary": "auto"}, TODO should return reasoning summary but does not
            text={"verbosity": "low"},
            max_output_tokens=max_tokens,
            extra_headers={ "X-Title": "EduPo" },
        )
        logging.debug(response)
        return response.output_text

    except:
        logging.exception("EXCEPTION Neúspěšné generování pomocí OpenAI.")
        return None

def generate_with_openai_simple(prompt, system="You are a helpful assistant.", model="gpt-4o-mini", max_tokens=500):
    logging.info('TEXTGEN Prompt: ' + show_short(prompt) + ' SYSTEM: ' + show_short(system))
    if 'gpt-5' in model:
        # reasoning models
        # add reasoning tokens
        max_tokens += 4000
        # use responses API
        return generate_with_openai_responses(prompt, system, model, max_tokens)
    else:
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        return generate_with_openai(messages, model, max_tokens)

def sanitize_prompt(prompt):
    return generate_with_openai_simple(f"Uprav prompt od uživatele pro generování obrázku tak, aby byl v souladu se všemi zásadami. Na výstup vydej pouze upravený prompt. Prompt: {prompt}")

def show_short(text, maxlen=100):
    if len(text) < maxlen:
        return repr(text)
    else:
        return repr(text[:maxlen-20] + '...' + text[-20:])

# https://platform.openai.com/docs/guides/images/usage?context=python
# https://platform.openai.com/docs/api-reference/images/create
def generate_image_with_openai(prompt, filename):
    with open(KEY_PATH) as infile:
        apikey = infile.read().rstrip()
    try:
        client = OpenAI(api_key=apikey)
    except:
        logging.exception("EXCEPTION Neúspěšná inicializace OpenAI.")
    
    logging.info('IMGGEN Prompt: ' + show_short(prompt))
    sanitized_prompt = sanitize_prompt(prompt)
    logging.info('IMGGEN Sanitized: ' + show_short(sanitized_prompt))

    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=sanitized_prompt,
            size="1024x1024",
            quality="standard",
            n=1,
            response_format="b64_json",
        )
    except:
        logging.exception("EXCEPTION Neúspěšné generování obrázku pomocí OpenAI.")
        return None

    imgdata = response.data[0].b64_json
    store_image(imgdata, filename)

    return response.data[0].revised_prompt

def store_image(imgdata, filename):
    bytestream = io.BytesIO(base64.b64decode(imgdata))
    
    with open(filename, "wb") as outfile:
        outfile.write(bytestream.getbuffer())

creativity_system = "Assume the role of a demanding editor at a prestigious literary publication. This story aims for the highest echelon of literary quality, intended for publication where only flawless work succeeds."
creativity_tasks = None
with open('creativity_test_prompt.txt') as infile:
    creativity_tasks = infile.read()


def score_creativity(story_text):
    prompt = f"Story\n{story_text}\n\n{creativity_tasks}"
    model = "google/gemini-3-pro-preview"
    result = generate_with_openai_simple(prompt, creativity_system, model, 5000)
    return result


if __name__=="__main__":
    with open(sys.argv[1]) as infile:
        story_text = infile.read()
        print(score_creativity(story_text))



