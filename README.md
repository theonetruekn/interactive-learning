# SWE-Benchmark

## SWE Bench Setup 

This uses [SWE-bench-docker](https://github.com/aorwall/SWE-bench-docker) which is a docker wrapper for [SWE-bench](https://github.com/princeton-nlp/SWE-bench).

Python version needs to be at least 3.11 and docker needs to be [installed](https://docs.docker.com/engine/install/), [alternative](https://get.docker.com/) and needs to run as [daemon](https://www.geeksforgeeks.org/how-to-install-and-configure-docker-on-arch-based-linux-distributionsmanjaro/):
1. `cd SWE-bench-docker`
2. `pip install -r requirements.txt`
3. `pip install swebench`

## Test SWE-Bench is working

1. Edit the paths(log_dir in particular) and run:
```
python run_evaluation.py \
    --predictions_path  ../swe-bench-example-predictions.json \
    --swe_bench_tasks ../swe-bench.json \
    --log_dir /home/lupos/interactive-learning/SWEBench/logs/ \
    --skip_existing \
    --timeout 900
```

2. Edit the path and get the report:
```
python generate_report.py \ 
    --predictions_path  ../swe-bench-example-predictions.json \
    --swe_bench_tasks ../swe-bench.json \
    --log_dir /home/lupos/interactive-learning/SWEBench/logs \
    --output_dir /home/lupos/interactive-learning/SWEBench/out 
```

## Evaluating Model


