hg-pylint-commit-hook
=====================

Code to run pylint on any python file on a commit in mercurial

This allows some rudimentary checking of python files against pylint.

Ensure you have __pylint__ and __hgapi__ installed:

    sudo pip install pylint
    sudo pip install hgapi

Update your .hgrc file as such:

    [ui]
    username = Your Name <your.name@somedomain.com>

    [hooks]
    pretxncommit.pylint = python:/<path>/<to>/pylint_hook.py:pylint_hook

    [pylint_hook]
    #whats the minimum pylint score that is acceptable
    threshold = 5

