import re

import os, errno

def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e: # this would be "except OSError, e:" before Python 2.6
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured

def load_signature(file_cnf):
    signature = {}
    re_variable = re.compile('c var n(\d+)_(\d+) (\d+)')
    with open(file_cnf) as fp:
        for line in fp:
            m_variable = re_variable.match(line)
            if m_variable:
                signature[m_variable.group(3)] = (m_variable.group(1), m_variable.group(2))
                continue

            break

    return signature

def load_node_count(file_cnf):
    with open(file_cnf) as fp:
        m_count = re.compile('c (\d+)').match(fp.readline())
        if m_count:
            return int(m_count.group(1))
    return -1