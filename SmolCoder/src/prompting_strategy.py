from abc import ABC, abstractmethod

from SmolCoder.src.llm_wrapper import LLM
from SmolCoder.src.toolkit import Toolkit

class PromptingStrategy(ABC):
    def __init__(self, name:str, lm: LLM, toolkit:Toolkit) -> None:
        self.name = name
        self.lm = lm
        self.toolkit = toolkit
        self._sysprompt = "Placeholder"

    @property
    def sysprompt(self):
        return self._sysprompt

    @abstractmethod
    def __call__(self, prompt:str) -> str:
        pass
    
    @staticmethod
    def create(model:LLM, toolkit:Toolkit, strategy="ReAct", mode:int = 2):
        if strategy == "ReAct":
            return ReAct(name=strategy, lm=model, toolkit=toolkit, mode=mode)
        else:
            raise ValueError

class ReAct(PromptingStrategy):

    THOUGHT_TOKEN = "Thought:"
    ACTION_TOKEN = "Action:"
    OBSERVATION_TOKEN = "Observation:"

    def __init__(self, name:str, lm: LLM, toolkit:Toolkit, mode:int = 2) -> None:
        """
        Args:
            mode (int): 0 for github_issue_mode, 1 for repoduce_error_mode, 2 for ReAct Mode
        """
        super().__init__(name, lm, toolkit)
        self._mode = mode 
        self._sysprompt = self._build_sysprompt()

    def _build_sysprompt(self) -> str:
        if self._mode == 0:
            prompt = "You will be given a description of a `github issue` and your task is, to solve this issue, first you should use tools to investiaget the repo to find the section where the error occurs and then you should replace this section with the correct code.\n\n"
        elif self._mode == 1:
            prompt = "You will be given a description of a `github issue` and your task is, to reproduce this issue by using the available tools to you.\n\n"
        elif self._mode == 2:
            prompt = "You will be given `question` and you will respond with `answer`.\n\n"
        else:
            raise ValueError("The Mode: " + str(self._mode) + " is not a valid mode for ReAct. ")

        sysprompt = prompt + (
            "Try to think step for step, do NOT do steps that are too big.\n"
            "To do this, you will interleave Thought, Action, and Observation steps.\n"
            "Thought can reason about the current situation.\n\n" 
            "Action can be the following types, \n"
        )

        sysprompt += self.toolkit.pretty_print_tools()
        sysprompt += "\n\nInput variables of the tools do not need quotation marks around them. In addition, do NOT use the `finish` tool before having made all changes to remedy the issue.\n\n"

        sysprompt += (
                "The following is an example on how you should act:\n"
                "--------------"
                f"{FEW_SHOT_EXAMPLE}"
                "--------------"
                "\n\n"
        )

        sysprompt += (
            "The Example is now finished, during your execution, "
            "follow the following format:\n\n"
            f"{self.THOUGHT_TOKEN} Reasoning which action to take to solve the task.\n"
            f"{self.ACTION_TOKEN} Always either "
        )

        sysprompt += self.toolkit.print_tool_short_descs()

        sysprompt += (
            f"\n{self.OBSERVATION_TOKEN} result of the previous Action\n"
            f"{self.THOUGHT_TOKEN} next steps to take based on the previous Observation\n"
            "...\n"
            "until Action is of type `Finish`.\n"
            "Do not use any special formatation such as markdown.\n"
            "The 'Observation' will automatically returned to you afetr you used an action, you do not need to generate it."
            "---\n\n"
        )

        return sysprompt

    def __call__(self, prompt: str, begin=False) -> str:
        if begin:
            prompt = self.sysprompt + prompt + "\n"
        
        prompt += self.lm.query_completion(prompt, stop_token=self.OBSERVATION_TOKEN)
        prompt += " " #adds whitespace after "Observation:"
       
        return prompt




NEW_METHOD = """
def get_system_call_names():
    psn_dir=os.path.dirname(os.path.realpath(__file__))
    kernel_ver=platform.release().split('-')[0]

    # this probably needds to be improved for better platform support
    if platform.machine() == 'aarch64':
        unistd_64_paths = ['/usr/include/asm-generic/unistd.h']
    else:
        unistd_64_paths = ['/usr/include/asm/unistd_64.h', '/usr/include/x86_64-linux-gnu/asm/unistd_64.h', '/usr/include/asm-x86_64/unistd.h', '/usr/include/asm/unistd.h', psn_dir+'/syscall_64_'+kernel_ver+'.h', psn_dir+'/syscall_64.h']

    for path in unistd_64_paths:
        try:
            with open(path) as f:
                return extract_system_call_ids(f)
        except IOError as e:
            pass

    raise Exception('unistd_64.h not found in' + ' or '.join(unistd_64_paths) + '.\n
"""

# Adaped from: https://github.com/tanelpoder/0xtools/issues/37
FEW_SHOT_EXAMPLE = f"""
StartFewShotExamples

Question: psn v1.2.3 release may show wrong syscall names on x86_64 due to looking them up from a wrong/template file, unistd.h files on ARM/aarch64 work somewhat differently from x86_64.

Thought: First, I need to locate the section in the repository that corresponds to the Issue where the wrong syscall names are displayed. For that I should list all the files.

Action: List_Files[.]

Observation: The entries in `repos/0xtools` are:
bin/
docs/licenses/
include/
lib/0xtools/
src/
.gitignore
0xtools.spec
CHANGELOG.md
LICENSE
Makefile
README.md
release.sh
(Current Working Directory: repos)

Thought: The section with the Issue will most likely be either in the `lib/0xtool` or the `src/` directory, since these two direcotires probably have the source code. I should move into the directory and then check the files in it.

Action: Move_to_Folder[lib/0xtools/]

Observation: Set the current working directory to `lib/0xtools/`.
(Current Working Directory: repos/lib/0xtools)

Thought: Since the current working directory shows that I am in the correct directory, I should now list all the files.

Action: List_Files[.]

Observation: The entries in `repos/0xtools/lib/0xtools/` are:
argparse.py
psnproc.py
psnereport.py
(Current Working Directory: repos/lib/0xtools)

Thought: Since the Issue was talking about psn we should check `psnproc.py` for problematic code.

Action: List_Classes[snproc.py]

Observation: The classes in `psnproc.py` are `ProcSource`
(Current Working Directory: repos/lib/0xtools)

Thought: We know now that there exist one class named `ProcSource`, we should look up which methods the class has.

Action: List_Methods[ProcSource]

Observation: 
Method `__init__(self, name, path, available_columns, stored_column_names, task_level=False, read_samples=lambda f: [f.read()], parse_sample=lambda self, sample: sample.split())` with docstring `{ None }`, 
Method `set_stored_columns(self, stored_column_n)` with docstring `{ None }`,
Method `hex_to_signed_int(self, hex_str, bit_length)` with docstring `{ None }`,
Method `get_system_call_names()` with docstring `{ None }`
(Current Working Directory: repos/lib/0xtools)

Thought: The Issue talks about displaying the wrong syscalls, thus we should check `get_system_call_names` for more information.

Action: List_Method_Body[ProcSource, get_system_call_names]

Observation:
```
def get_system_call_names():
    psn_dir=os.path.dirname(os.path.realpath(__file__))
    kernel_ver=platform.release().split('-')[0]

    unistd_64_paths = ['/usr/include/asm-generic/unistd.h', '/usr/include/asm/unistd_64.h', '/usr/include/x86_64-linux-gnu/asm/unistd_64.h', '/usr/include/asm-x86_64/unistd.h', '/usr/include/asm/unistd.h', psn_dir+'/syscall_64_'+kernel_ver+'.h', psn_dir+'/syscall_64.h']
```
(Current Working Directory: repos/lib/0xtools)

Thought: The Issue describes that syscalls are wrongly displayed on the x86_64 platform, we should check for the different platforms and based on the platform return the correct syscalls.

Action: Replace_Method[ProcSource, get_system_call_names, {NEW_METHOD}]

Observation: Method `get_system_call_names` in class `ProcSource` replaced successfully in file `snproc.py`.

Thought: Since we have successfully replaced the method with the new code, the Issue should now be fixed and we can finish the execution.

Action: Finish["The Issue is fixed"]

EndFewShotExamples
"""
