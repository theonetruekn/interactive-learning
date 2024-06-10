import requests
import json

class LLM:
    def __init__(self, model: str, url='http://localhost:11434/api/generate'):
        self.model = model
        self.url = url

    def query_completions(self, prompt, stream=False, options=None):
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": stream
            }

            if options is not None:
                data['options'] = options

            json_data = json.dumps(data)

            response = requests.post(self.url, data=json_data, headers={'Content-Type': 'application/json'})

            return response.json()["response"]