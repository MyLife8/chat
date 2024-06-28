# llm_config.py

from anthropic import Anthropic
from groq import Groq

def anthropic_create_message(client, model, messages, max_tokens):
    response = client.messages.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )
    return {
        'content': response.content[0].text,
        'usage': {
            'prompt_tokens': response.usage.input_tokens,
            'completion_tokens': response.usage.output_tokens,
            'total_tokens': response.usage.input_tokens + response.usage.output_tokens
        }
    }

def groq_create_message(client, model, messages, max_tokens):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )
    return {
        'content': response.choices[0].message.content,
        'usage': {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
    }

# !!!!! ********************* CHOOSE YOUR MODEL ********************* !!!!!
# Choose LLM Model
MY_MODEL = "llm_model_1"

# ************************* CLAUDE ********************************
# pricing - https://www.anthropic.com/pricing#anthropic-api
# models - https://docs.anthropic.com/en/docs/about-claude/models
# 200K context window, Input $0.25 / MTok, Output $1.25 / MTok
# CHEAP, FASTEST
# model="claude-3-haiku-20240307"
# 200K context window, Input $3 / MTok, Output $15 / MTok
# SMART
# model="claude-3-5-sonnet-20240620"
# GROQ, model 3, is totally FREE
# ********************** END - CLAUDE *****************************

LLM_CONFIGS = {
    "llm_model_1": {
        "model": "claude-3-haiku-20240307",
        "api_key": "claude_api_key",
        "client_class": Anthropic,
        "create_message": anthropic_create_message
    },
    "llm_model_2": {
        "model": "claude-3-5-sonnet-20240620",
        "api_key": "claude_api_key",
        "client_class": Anthropic,
        "create_message": anthropic_create_message
    },
    "llm_model_3": {
        "model": "mixtral-8x7b-32768",
        "api_key": "groq_api_key",
        "client_class": Groq,
        "create_message": groq_create_message
    }
}

def get_llm_config():
    return LLM_CONFIGS[MY_MODEL]

def create_client(api_key):
    config = get_llm_config()
    return config['client_class'](api_key=api_key)

def create_message(client, model, messages, max_tokens):
    config = get_llm_config()
    return config['create_message'](client, model, messages, max_tokens)

# this gives display data to show us which model is being used, not for connectivity
def get_llm_info():
    config = get_llm_config()
    client_class_name = config['client_class'].__name__
    model_name = config['model']
    return client_class_name, model_name