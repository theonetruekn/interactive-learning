import requests
import json

class LLM:
    def __init__(self, model: str, url='http://localhost:11434/api/generate'):
        self.model = model
        self.url = url

    # check out `raw` parameter too
    def query_completion(self, prompt:str, stop_token="Observation") -> str:
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }

        json_data = json.dumps(data)
        response = requests.post(self.url, data=json_data, headers={'Content-Type': 'application/json'}, stream=True)

        partial_response = ""
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                chunk_data = json.loads(chunk.decode('utf-8'))
                if "response" in chunk_data:
                    partial_response += chunk_data["response"]
                    if stop_token in partial_response:
                        break
                if chunk_data.get("done"):
                    break
        
        if partial_response == "":
            raise ValueError

        return partial_response

if __name__ == "__main__":
    llm = LLM("phi3:latest")
    prompt = """You will be given `question` and you will respond with `answer`.

To do this, you will interleave Thought, Action, and Observation steps.

Thought can reason about the current situation, and Action can be the following types:
(1) CodeSearch[search_query], which searches the codebase for a class or a function, specified as search_query in CodeSearch[search_query]. Returns the source code.. Example use: CodeSearch[my_func(param1, param2)] for searching a function or CodeSearch[SomeClass()] for searching a class.
(2) Finish[answer], which returns the final `answer` and finishes the task. After calling this tool, you can stop generating.. Example use: Finish[The Answer is 42].
---

Follow the following format:

Thought: Reasoning which action to take to solve the task.
Action: Always either CodeSearch[search_query] or Finish[answer]
Observation: result of the previous Action
Thought: next steps to take based on the previous Observation
...
until Action is of type Finish.

---

Question:  Which are the methods in MyClass?"""
    response = llm.query_completion(prompt)
    print(response)