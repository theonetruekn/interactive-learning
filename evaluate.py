# This implementation uses checkpoints, this means if the program 
# is interuppted it can start again, where it left oft.

import tempfile
import json
from tqdm import tqdm
import argparse
import pandas as pd

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

checkpoint_file = 'checkpoint.txt'
resume_index = 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluation Pipeline for the SmolCoder Agent on the SWE-Benchmark.")

    # Arguments for the CLI
    parser.add_argument('--model_name', type=str, default='phi3:latest',
                        help='Name of the LLM model you want to use, as specified in ollama.')
    parser.add_argument('--dataset_location', type=str, default='Evaluation/swe-bench-lite.json', help='File path to the location of the SWE-Bench-Lite dataset.')
    parser.add_argument('--output_file', type=str, default="predictions.json", help="File path towards the output file, should be a '.json'.")
    parser.add_argument('--logging_enabled', type=bool, default=False, help="If logging for the agent should be enabled.")
    parser.add_argument('--working_directory', type=str, default="repos", help="Working directory of the Agent, here the github repository will be downloaded to.")

    args = parser.parse_args()

    df = pd.read_json(os.path.abspath(args.dataset_location))
    agent = AgentWrapper(
                     agent_name="SmolCoder",
                     toolkit=toolkit,
                     mode=0,
                     model=args.model_name,
                     working_directory=args.working_directory,
                     logging_enabled=args.logging_enabled
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
        with open(args.output_file, 'a', encoding="utf-8-sig") as json_file:
            if resume_index == 0:
                json_file.write('[')  # Start of JSON array
                json_file.write('\n')
            # Generating our solution
            for index, row in tqdm(df.iterrows()):
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
        print("All task are finished see 'predictions.json' for the results or delete 'checkpoint.txt' for a new run.")
