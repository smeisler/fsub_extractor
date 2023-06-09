import os.path as op
import os
import subprocess


def overwrite_check(file):
    """Checks whether a file exists. If so, aborts the function.
    Parameters
    ==========
    file: str
            name of file to look for

    Outputs
    =======
    None
    """
    if op.exists(file):
        raise Exception(
            f"Output file {file} already exists. Aborting program. Specify --overwrite if you would like to overwrite files."
        )

    return None


def find_program(program):
    """Checks that a command line tools is executable on path.
    Parameters
    ==========
    program: str
            name of command to look for

    Outputs
    =======
    program: str
            returns the program if found, and errors out if not found
    """

    #  Simple function for checking if a program is executable
    def is_exe(fpath):
        return op.exists(fpath) and os.access(fpath, os.X_OK)

    path_split = os.environ["PATH"].split(os.pathsep)
    if len(path_split) == 0:
        raise Exception("PATH environment variable is empty.")

    for path in path_split:
        path = path.strip('"')
        exe_file = op.join(path, program)
        if is_exe(exe_file):
            return program
    raise Exception(f"Command {program} could not be found in PATH.")


def run_command(cmd_list, verbose=True):
    """Interface for running CLI commands in Python. Crashes if command returns an error.
    Parameters
    ==========
    cmd_list: list
            List containing arguments for the function, e.g. ['CommandName', '--argName1', 'arg1']

    Outputs
    =======
    None
    """

    function_name = cmd_list[0]

    if verbose:
        # Print command run to the output
        print(
            "\n######## Running Shell Command: ########",
        )
        print(*cmd_list, sep=" ")
        print("########################################\n")

    return_code = subprocess.run(cmd_list).returncode
    if return_code != 0:
        raise Exception(
            f"Command {function_name} exited with errors. See message above for more information."
        )

    return None
