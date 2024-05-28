# Interactive Learning
 
 > This project was developed as part of the research-lab "Interactive Learning" at the Karlsruhe Institute of Technology (KIT) in the summer of 2024.

## Description

The scope of this project is to develop an autonomous coding agent similar to [Devin](https://www.cognition.ai/blog/introducing-devin), [Amazon Q](https://aws.amazon.com/q/) and [AutoCodeRover](https://github.com/nus-apr/auto-code-rover).

All these agents have in common that they are using GPT4 or other high-end (and thus expensive) LLMs as a backbone. In this project, we want to test the feasibility of using smaller models as agents.

The ambitious goal of this project is to get onto the leaderboard of [SWEBench](https://www.swebench.com/) - a by-now well-established benchmark for coding agents.

## Roadmap

We will test the following configuations:

- Phi3 as a baseline
- Phi3 as coding agent
- Phi3 finetuned on code
- Phi3 as coding agent, finetuned on code/tool-use
- Phi3 as coding agent, finetuned on code/tool-use with human interaction

- maybe some other stuff too like MoEs

## Ressources

Very Relevant Papers:
- [ReAct](https://arxiv.org/abs/2210.03629)
- [Toolformer](https://arxiv.org/abs/2302.04761)
- [SWE Agent](https://swe-agent.com/paper.pdf)
- [AutoCodeRover](https://arxiv.org/abs/2404.05427)
- [TextBooks Are all you need](https://arxiv.org/abs/2306.11644)
- [SWE-Bench](https://arxiv.org/abs/2310.06770)
- [LoRA](https://arxiv.org/abs/2106.09685)
- [Phi3](https://arxiv.org/abs/2404.14219)

Less Relevant Papers:
- [FireAct](https://arxiv.org/abs/2310.05915)
- [KAN](https://arxiv.org/abs/2404.19756)
- [LoRa vs Finetune](https://arxiv.org/abs/2405.09673)
- [BranchTrainMix](https://arxiv.org/abs/2403.07816)

Misc:
- [SWE Agent](https://swe-agent.com)
- [SWE-Bench](https://www.swebench.com)
- [DSPy](https://github.com/stanfordnlp/dspy)
- [MoE](https://huggingface.co/blog/moe)
- [TorchTune](https://github.com/pytorch/torchtune)
- [Efficient KAN](https://github.com/Blealtan/efficient-kan/tree/master)
- [Llama3](https://llama.meta.com/llama3/)
- [Ollama](https://ollama.com/)
- [QLora Llama3](https://www.philschmid.de/fsdp-qlora-llama3)
