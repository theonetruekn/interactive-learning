# Problems SWE Agent faces
- Agents are bad at editing files
- line numbers seem confusing for the agent
=> why not just tell them to rewrite entire function and paste it in? seems simpler

# Human Interaction
- human interaction could be "edit this for me" and let the human paste it

- implementation of the reproduction of the bug should be its own trajectory and not clutter the context window, imo
- also, can we summarize the previous stuff to reduce the length?

# Misc
- adding DSPy support would probably be worth it

- is scrolling really that important? if we dont wanna paste the code of the whole class, mayb we should only paste method names and a docstring? typehinting and expressive names for methods, params etc may also help the llm

- different tools for each use case or same tool with different input

- Fuzzy Matching / Fuzzy Tokenizing for Actions

- Ollama should stop after giving an action.