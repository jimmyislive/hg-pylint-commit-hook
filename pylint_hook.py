import os
import re
import tempfile
import subprocess
from hgapi import hgapi

__doc__ = """This allows some rudimentary checking of python files against pylint.

          Ensure you have pylint and hgapi installed:

              sudo pip install pylint
              sudo pip install hgapi

          Update your .hgrc file as such:

          [hooks]
          pretxncommit.pylint = python:/<path>/<to>/pylint_hook.py:pylint_hook

          [pylint_hook]
          #whats the minimum pylint score that is acceptable
          threshold = 5

          """

def _write_file(err, out, return_code, out_file):
    """Helper function to buffer up all pylint output."""

    out_file.write('\n\nStderr: %s' % err)
    out_file.write('Stdout: %s' % out)
    out_file.write('Exit: %s\n\n' % return_code)

def pylint_hook(ui, repo, **kwargs):
    """The hook function for pylint checking.

    This hook runs when a commit command is issued. It then does a 'hg status' to finad all python files
    in the changeset with status as A/M. Pylint is run on these file. Pylint prints out a summary score,
    it looks something like:

        Global evaluation
        -----------------
       Your code has been rated at 0.00/10 (previous run: X.XX/10) 

    The function then extracts that score and compares it against the threadhold specified in the config. 
    If it is lesser, the commit is aborted.

    """

    base_repo_path = os.path.dirname(repo.path)

    #pattern of interest
    PATTERN = 'Your code has been rated at -*(\d+\.\d*)/10'
    #file into which all pylint output will be dumped for inspection
    temp_dir = tempfile.gettempdir()
    pylint_output = open(os.path.join(temp_dir, 'hg_commit_pylint_hook.txt'), 'w')

    failed = False

    hgrepo = hgapi.Repo(os.path.abspath(os.curdir))
    threshold = float(hgrepo.config('pylint_hook', 'threshold'))
   
    #find out files with 'A'/'M' status in the changeset being comitted 
    hg_status = hgrepo.hg_status()

    candidate_files = []
    candidate_files.extend(hg_status['A'])
    candidate_files.extend(hg_status['M'])

    for item in candidate_files:

        #get the absolute path of changed files
        changed_file = os.path.join(base_repo_path, item)

        #we are interested only in .py files
        if changed_file.endswith('.py'):
            p = subprocess.Popen(['pylint', changed_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdoutdata, stderrdata = p.communicate()

            _write_file(stderrdata, stdoutdata, p.returncode, pylint_output)

            #Unfortunately pylint returns non-zero exit code even on success
            match = re.search(PATTERN, stdoutdata, re.I|re.M)
            if match and len(match.groups()):
                if float(match.group(1)) >= threshold:
                    print 'Awesome!!! File %s passed with a pylint score of %s/10' % (changed_file, float(match.group(1)))
                    continue
                else:
                    failed = True
                    print '**** For file %s, PyLint returned a score of %s which is lesser than the threshold of %s' \
                          % (changed_file, float(match.group(1)), threshold)
            else:
                failed = True
                print '**** PyLint did not output data in the correct format.'
                #no point continuing
                break
        
    pylint_output.close()
    
    if failed:            
        print '**** PyLint Checks Failed: Error details stored in file %s' % pylint_output.name
        return True
    else:
        print 'PyLint Checks Passed, details stored in file %s' % pylint_output.name
        return False


