import pandas as pd
from pandas import Series
import git
import os
import validators
import shutil
from pathlib import Path
from datetime import datetime
import logging

from SmolCoder.src.agent import SmolCoder
from SmolCoder.src.llm_wrapper import LLM

# This class is a wrapper for the MolCoder Agent, it is responsible for setting up the required enviroment and cleaning up. 
# Its job is the following:
# - clone the repos, set the head to the correct commit.
# - Calls our internal Agent, which does the changes.
# - Stages our changes.
# - Calculates the git diff, which we return.
class AgentWrapper():
    # openai: if you want to use it set first element of tuple to true and second paremter to the openaikey
    # dummy_model: if actiavetd uses a stub instead of an model
    def __init__(self, agent_name, toolkit, mode, model : str, dummy_model: bool, working_directory="repos", logging_enabled=True, openai=(False, "")):
        self.name = agent_name
        self.working_directory = working_directory
        self.logging_enabled = logging_enabled # At the moment, not properly implemented
        self.toolkit = toolkit
        self.mode = mode
        self.dummy_model = dummy_model
        
        # For logging purpose
        #------
        # ensure logging folder exists
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # generate a logging file
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = log_dir / f'{model}_{current_time}.log'

        logging.basicConfig(filename=log_file, filemode='w', level=logging.DEBUG,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Only when the logger is enabled do we want to set it
        if self.logging_enabled:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = None
        
        if not self.dummy_model:
            self.model = LLM(model, self.logger, openai)

        if not os.path.isdir(working_directory):
            os.makedirs(working_directory)

    def predict(self, row_input: Series):   
        # clone the github repo, from which issue we want to solve
        repo_dir = self._clone_repo(row_input["repo"], row_input["base_commit"])

        # Creating our Agent
        if not self.dummy_model:
            agent = SmolCoder(model=self.model, 
                              codebase_dir=Path(repo_dir), 
                              toolkit=self.toolkit, 
                              mode=self.mode,
                              logger=self.logger
                              )
        else:
            agent = AgentStub(str(repo_dir))

        result = agent("[Question]" + str(row_input["problem_statement"]))
        
        if self.logging_enabled:
            print("LOGGING: Finished the Agent with the following as return: " + str(result))
        repo = git.Repo(repo_dir)
        repo.git.add("*")
        
        diff = repo.git.diff("--cached")
        
        if self.logging_enabled:
            print("LOGGING: Finished caculating the git diff.")
            if diff == '': print("LOGGING: Git Diff is empty.")
        
        return diff

    def _clone_repo(self, repo_name: str, base_commit: str, overwrite_cloned_repo : bool = True):
        repo_url = "https://github.com/" + repo_name
        repo_dir = os.path.join(self.working_directory, repo_name.split('/', 1)[1])
        
        if not validators.url(repo_url):
            raise Exception("The Repo url is not valid: " + repo_url)
                    
        if not (os.path.isdir(repo_dir)) or (overwrite_cloned_repo):
            if os.path.exists(repo_dir):
                shutil.rmtree(repo_dir)
            os.makedirs(repo_dir)

            # clones the repo on which llm will work
            git.Repo.clone_from(repo_url, repo_dir)

        if self.logging_enabled:
            print("LOGGING: Repo " + str(repo_url) + "downloaded in folder `" + str(repo_dir) + "`.")
            
        # we need to make sure we have the correct commit stage
        repo = git.Repo(repo_dir)
        repo.git.reset('--hard', base_commit)

        if self.logging_enabled:
            print("LOGGING: Reset Git repo to the commit " + str(base_commit))
        
        return repo_dir



# Used for testing purposes.
class AgentStub():
    def __init__(self,  start_cwd):
         self.start_cwd =  start_cwd

    def __call__(self, userprompt):
        new_file = os.path.join(self.start_cwd, 'test_file.md')
        
        fp = open(new_file, 'w+')
        fp.write('This is a test file, which test if the git diff gets caluclated correctly.')
        fp.close()
        
        return ""
