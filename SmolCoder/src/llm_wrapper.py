import requests
import json

class LLM:
    def __init__(self, model: str, logger, url='http://localhost:11434/api/generate', raw : bool = False):
        self.logger = logger
        self.model = model
        self.url = url
        self.raw = raw # if enabled will not return markdown, this hsouldb e set to true when using llam3 and to false if using phi3

    def query_completion(self, prompt, stop_token=None, seed=42):
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "raw": self.raw, # needs to be off for phi3
            "options": {"cache_prompt": True, "seed": seed}
        }

        json_data = json.dumps(data)

        try:
            response = requests.post(self.url, data=json_data, headers={'Content-Type': 'application/json'})
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request failed: {e}")

        response_text = ""
        token_count = 0
        try:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    res_json = json.loads(decoded_line)
                    response_text += res_json.get("response", "")
                    # Check if the streaming is done and we received the final response object
                    if res_json.get("done", False):
                        token_count = res_json.get("eval_count", 0)
                        break

                    # for DEBUG
                    if stop_token and stop_token in response_text:
                        stop_index = response_text.find(stop_token)
                        response_text = response_text[:stop_index + len(stop_token)]
                        break
        except json.JSONDecodeError as e:
            print(f"JSON decoding failed: {e}")
            print(f"Response content: {response.content}")
            raise ValueError

        self.logger.info(f"Number of tokens in reponse: {str(token_count)}")
        return response_text


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
    import time
    start_time = time.time()
    response1 = llm.query_completion(prompt, stop_token="Observation:")
    end_time = time.time()
    duration1 = end_time - start_time
    print(response1)
    print(f"First API call duration: {duration1} seconds")

    # Timing the second API call
    start_time = time.time()
    response2 = llm.query_completion(prompt, stop_token="Observation:")
    end_time = time.time()
    duration2 = end_time - start_time
    print(response2)
    print(f"Second API call duration: {duration2} seconds")
