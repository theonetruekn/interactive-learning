# This implementation uses checkpoints, this means if the program 
# is interuppted it can start again, where it left oft.

import tempfile
import json
from tqdm import tqdm
import argparse
import pandas as pd
from datetime import datetime

# So that it recognizes the SmolCoder libary
import sys
import os
sys.path.append(str(os.path.abspath('/SmolCoder/')))

from SmolCoder.src.agent_wrapper import AgentWrapper
from SmolCoder.src.toolkit import Toolkit

from SmolCoder.src.tools.list_methods import ListMethods
from SmolCoder.src.tools.list_classes import ListClasses
from SmolCoder.src.tools.list_files import ListFiles
from SmolCoder.src.tools.replace_method import ReplaceMethod
from SmolCoder.src.tools.finish import Finish
from SmolCoder.src.tools.execute_python import ExecutePythonCode
from SmolCoder.src.tools.show_method import ShowMethodBody
from SmolCoder.src.tools.move_folder import MoveFolder
from SmolCoder.src.tools.human_interaction import HumanInteraction


# Tool Definition
class_sumary = ListMethods()
list_classes = ListClasses()
list_files = ListFiles()
replace_method = ReplaceMethod()
finish = Finish()
execute_python = ExecutePythonCode()
show_method = ShowMethodBody()
move_folder = MoveFolder()
human_interaction = HumanInteraction()

toolkit = Toolkit([list_classes, list_files, replace_method, show_method, move_folder, finish])

resume_index = 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluation Pipeline for the SmolCoder Agent on the SWE-Benchmark.")

    # Arguments for the CLI
    parser.add_argument('--model_name', type=str, default='phi3:latest',
                        help='Name of the LLM model you want to use, as specified in ollama.')
    parser.add_argument('--dataset_location', type=str, default='Evaluation/test-00000-of-00001.parquet', help='File path to the location of the SWE-Bench-Lite dataset.')
    parser.add_argument('--output_directory', type=str, default="output", help="File path towards the output folder.")
    parser.add_argument('--logging_enabled', type=bool, default=False, help="If logging for the agent should be enabled.")
    parser.add_argument('--working_directory', type=str, default="repos", help="Working directory of the Agent, here the github repository will be downloaded to.")
    parser.add_argument('--openai_key', type=str, default=None, help="Set it to your openai key, if you want to use it.")
    parser.add_argument('--dummy_model', type=bool, default=False, help="If this is activated runs the script with a stub/dummy as Model.")
    parser.add_argument('--n_samples', type=int, default=500, help="Number of Samples the program should be tested on, if not set uses the whole dataset.")

    args = parser.parse_args()

    # df = pd.read_json(os.path.abspath(args.dataset_location))
    df = pd.read_parquet(os.path.abspath(args.dataset_location))


    # If we use the dummy_model we want to ignore 'model_name' parameter
    if args.dummy_model:
        model_name = "dummy_model"
    else:
        model_name = args.model_name

    # We need to give the file a distinct names, if we run multiple instances at once
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    checkpoint_file = f"{args.output_directory}/checkpoint_{model_name}_{current_time}.txt"

    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)


    if not args.openai_key:
        agent = AgentWrapper(
                         agent_name="SmolCoder",
                         toolkit=toolkit,
                         mode=0,
                         model=args.model_name,
                         working_directory=args.working_directory,
                         logging_enabled=args.logging_enabled,
                         dummy_model=args.dummy_model,
                        )
    else:       
        agent = AgentWrapper(
                         agent_name="SmolCoder",
                         toolkit=toolkit,
                         mode=0,
                         model="gpt4-o-mini",
                         dummy_model=False,
                         working_directory=args.working_directory,
                         logging_enabled=args.logging_enabled,
                         openai=(True, args.openai_key),
                        )


    # Check if checkpoint file exists and read the last processed index
    try:
        with open(checkpoint_file, 'r') as f:
            resume_index = int(f.read().strip())
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error reading checkpoint file: {e}")

    if resume_index < len(df) - 1:
        # Open a file to save predictions
        with open(f"{args.output_directory}/predictions_{model_name}_{current_time}.json", 'a', encoding="utf-8-sig") as json_file:
            if resume_index == 0:
                json_file.write('[')  # Start of JSON array
                json_file.write('\n')
            # Generating our solution
            
            if args.n_samples > df.shape[0]:
                number_samples = df.shape[0]
            else:
                number_samples = args.n_samples

            for index, row in tqdm(df.iterrows(), total=number_samples):
                if index > args.n_samples:
                    break

                if index % 10 == 0: print("Current idx: " + str(index))
                # Skip rows that were already processed
                if index < resume_index:
                    continue
        
                predictions = {
                    "instance_id": row["instance_id"],
                    "model_patch": agent.predict(row),
                    "model_name_or_path": agent.name
                }
                # Convert the dictionary to a JSON formatted string and write to file
                json_data = json.dumps(predictions, indent=4)
                json_file.write(json_data)
                if index < len(df) - 1:
                    json_file.write(',')
                json_file.write('\n')
        
                with open(checkpoint_file, 'w') as f:
                    f.write(str(index))
                    
            if index == len(df) - 1:
                json_file.write(']')
    else:
        print(f"All task are finished see '{args.output_directory}/predictions_{args.model_name}_{current_time}.json' for the results or delete 'checkpoint.txt' for a new run.")
