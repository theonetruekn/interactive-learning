import pandas as pd
from pandas import Series
import git
import os
import validators
import shutil
from pathlib import Path
from SmolCoder.src.agent import SmolCoder


# This class is a wrapper for the MolCoder Agent, it is responsible for setting up the required enviroment and cleaning up. 
# Its job is the following:
# - clone the repos, set the head to the correct commit.
# - Calls our internal Agent, which does the changes.
# - Stages our changes.
# - Calculates the git diff, which we return.
class AgentWrapper():
    def __init__(self, name, toolkit, mode, model, working_directory="repos", logging=True):
        self.name = name
        self.working_directory = working_directory
        self.logging_enabled = logging
        self.toolkit = toolkit
        self.mode = mode
        self.model = model

        if not os.path.isdir(working_directory):
            os.makedirs(working_directory)

    def predict(self, row_input: Series):   
        # clone the github repo, from which issue we want to solve
        repo_dir = self._clone_repo(row_input["repo"], row_input["base_commit"])

        # Creating our Agent
        smol_coder = SmolCoder(model=self.model, 
                               codebase_dir=Path(repo_dir), 
                               toolkit=self.toolkit, 
                               mode=self.mode
                              )
        
        result = smol_coder("[Question]" + str(row_input["problem_statement"]))
        
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




# DEPCREATED
class AgentStub():
    def __init__(self,  start_cwd):
         self.start_cwd =  start_cwd

    def __call__(self, userprompt):
        new_file = os.path.join(self.start_cwd, 'test_file.md')
        
        fp = open(new_file, 'w+')
        fp.write('This is a test file, which test if the git diff gets caluclated correctly.')
        fp.close()
        
        return ""
