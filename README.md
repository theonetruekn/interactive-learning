# SmolCoder: An Open Source LLM-based coding agent that works with human interaction (WIP)
 
 > This project was developed as part of the research-lab "Interactive Learning" at the Karlsruhe Institute of Technology (KIT) in the summer of 2024.
<p align="center">
<img src="https://github.com/theonetruekn/interactive-learning/blob/master/smolcoder.webp?raw=true" width=300 height =300/>
</p>

## Description

The scope of this project is to develop an autonomous coding agent similar to [Devin](https://www.cognition.ai/blog/introducing-devin), [SWE-Agent](https://swe-agent.com/) and [AutoCodeRover](https://github.com/nus-apr/auto-code-rover).

All these agents have in common that they are using GPT4 or some other high-end (and thus expensive) LLMs as a backbone. In this project, we want to test the feasibility of using smaller models as agents.

The ambitious goal of this project is to get onto the leaderboard of [SWEBench](https://www.swebench.com/) - a by-now well-established benchmark for coding agents.

This project is a work-in-progress.

## Roadmap
- Writing an Eval Pipeline for SWEBench ✅
- Creating the Coding Agent Framework ✅
- Definining and programming the Tools that the Agent will use ✅
- Creating an interface between the Agent and the Computer ✅

**Evaluating:**
 - Phi3 out-of-the-box
 - Phi3 as coding agent
 - Phi3 finetuned on code
 - Phi3 as coding agent, finetuned on code/tool-use
 - Phi3 as coding agent, finetuned on code/tool-use with human interaction

## Run the SWE-Bench Evaluation

Python version needs to be at least `3.11` and docker needs to be [installed](https://docs.docker.com/engine/install/) ([alternative](https://get.docker.com/)) and docker needs to run as [daemon](https://www.geeksforgeeks.org/how-to-install-and-configure-docker-on-arch-based-linux-distributionsmanjaro/).

**Test the SWE-Bench installation**
1. Navigate inside the folder and make sure the requirements are installed:
```
cd Evaluation
cd SWE-bench
pip install -e .
```

2. Test the installation:
```
python -m swebench.harness.run_evaluation \
    --predictions_path gold \
    --max_workers 1 \
    --instance_ids sympy__sympy-20590 \
    --run_id validate-gold
```


**Run the SWE-Bench evaluation**
1. Get your predictions by running the appropiate part of the `Evaluation.ipynb`, make sure to choose the correct dataset (either `swe-bench.json` for the full dataset or `swe-bench-lite.json` for a smaller version).
Alternatively you can also run the `evaluation.py` inside the `Evaluation` folder.
2. To evaluate the predictions, navigate to the SWE-Bench folder
```
cd Evaluation
cd SWE-bench
```
3. Run the evaluation with the following command, you may need to customize the command:
```
python -m swebench.harness.run_evaluation \
 --predictions_path ../prediction.json \
 --max_workers 1 \
 --dataset_name ../swe-bench-lite.json \
 --run_id YOUR_ID
```
4. Your should find a `json` report, listing the evaluation result of your predictions,with `YOUR_ID` inside the `SWE-bench` directory.

## Resources

**Very Relevant Papers:**
- [ReAct](https://arxiv.org/abs/2210.03629)
- [Toolformer](https://arxiv.org/abs/2302.04761)
- [SWE Agent](https://swe-agent.com/paper.pdf)
- [AutoCodeRover](https://arxiv.org/abs/2404.05427)
- [TextBooks Are all you need](https://arxiv.org/abs/2306.11644)
- [SWE-Bench](https://arxiv.org/abs/2310.06770)
- [LoRA](https://arxiv.org/abs/2106.09685)
- [Phi3](https://arxiv.org/abs/2404.14219)
___
**Less Relevant Papers:**
- [FireAct](https://arxiv.org/abs/2310.05915)
- [KAN](https://arxiv.org/abs/2404.19756)
- [LoRa vs Finetune](https://arxiv.org/abs/2405.09673)
- [BranchTrainMix](https://arxiv.org/abs/2403.07816)
___
**Misc:**
- [DSPy](https://github.com/stanfordnlp/dspy)
- [MoE](https://huggingface.co/blog/moe)
- [TorchTune](https://github.com/pytorch/torchtune)
- [Efficient KAN](https://github.com/Blealtan/efficient-kan/tree/master)
- [Llama3](https://llama.meta.com/llama3/)
- [Ollama](https://ollama.com/)
- [QLora Llama3](https://www.philschmid.de/fsdp-qlora-llama3)
