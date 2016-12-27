#!/usr/bin/env python

import subprocess
import re
import tempfile
import ConfigParser
import sys
from os import path

def main(repoPath):

    submodules = {}

    def gitCall(args, regexp=None):
        print ' '.join(args)
        p = subprocess.Popen(
            args, cwd=repoPath,
            stdout=subprocess.PIPE
        )
        (stdout, stderr) = p.communicate()

        if p.returncode != 0:
            print stderr
            raise Exception(p.returncode)

        if regexp:
            return re.findall(regexp, stdout, re.MULTILINE)

    def getSubmoduleCommit():
        submodule_commits = gitCall(['git', 'submodule'], r'[-+]?(\w+)\s+([\w\/\\\-\_\.\d]+)')
        for smc in submodule_commits:
            submodules[smc[1]]['commit'] = smc[0]

    def getSubmoduleBranch():
        for smn in submodules:

            sm = submodules[smn]

            refs = gitCall(
                ['git', 'ls-remote', sm['url']],
                r'(\w+)\s+refs\/\w+\/([\w+\-\_\.\d]+)'
            )
            # print refs

            for ref in refs:
                if ref[0] == sm['commit']:
                    sm['branch'] = ref[1]
                    #print sm['url'] + ' is on branch '+sm['branch']
                    break
            else:
                raise Exception('Could not find commit '+sm['commit']+' in refs of '+sm['url'])
                # print 'Could not find commit '+sm['commit']+' in refs of '+sm['url']

    def readSubmodules():
        gitmodules_text = open(path.join(repoPath,'.gitmodules'), 'r').read()
        gitmodules_text = re.sub(r'\t+', '', gitmodules_text, count=0, flags=re.MULTILINE)
        f, fname = tempfile.mkstemp(text=True)
        open(fname, 'w').write(gitmodules_text)
        Conf = ConfigParser.ConfigParser()
        Conf.read(fname)
        for section in Conf.sections():
            _path = Conf.get(section, 'path')
            _url = Conf.get(section, 'url')
            submodules[_path] = {
                'path': _path,
                'url': _url
            }

    def shallowClone():
        for smn in submodules:
            sm = submodules[smn]
            if 'url' in sm and 'path' in sm and 'branch' in sm:
                gitCall([
                    'git', 'clone',
                    '--single-branch', '--branch', sm['branch'],
                    '--depth', '1',
                    sm['url'],
                    sm['path']
                ])
                print sm['path']+' clonned successful on branch '+sm['branch']+' from '+sm['url']
            else:
                print sm['path']+' has not enough args'

    readSubmodules()
    getSubmoduleCommit()
    getSubmoduleBranch()
    shallowClone()

repoPath = '.'
if (len(sys.argv) > 1):
    repoPath = sys.argv[1]

main(repoPath)
