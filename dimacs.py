import re

import networkx as nx

def load(s):
    lines = s.split('\n')

    re_comment = re.compile('c.*')
    re_stats = re.compile('p\s*edge\s*(\d*)\s*(\d*)')
    re_edge = re.compile('e\s*(\d*)\s*(\d*)')

    g = nx.Graph()

    while len(lines) > 0:
        line = lines.pop(0)

        if re_comment.match(line):
            continue

        m_stats = re_stats.match(line)
        if m_stats:
            g.add_nodes_from(range(1, int(m_stats.group(1)) + 1))
            continue;

        m_edge = re_edge.match(line)
        if m_edge:
            g.add_edge(int(m_edge.group(1)), int(m_edge.group(2)))


    return g


def load_file(location):
    """Loads a boolean expression from a file."""
    with open(location) as f:
        s = f.read()

    return load(s)