import sys
import subprocess
import operator
import os

import dimacs
import util

def node(n, p):
    return "n" + str(n)+ "_" + str(p)

def satify(file_graph, ofile_sat, ofile_cnf):
    util.silentremove(ofile_sat)
    util.silentremove(ofile_cnf)

    g = dimacs.load_file(file_graph)
    f = open(ofile_sat, "w")

    node_count = len(g.nodes())

    # Jeder Knoten mindestens einmal enthalten
    f.write("(")
    for n in xrange(1, node_count + 1):
        f.write("(")
        for p in xrange(1, node_count + 1):
            f.write(node(n, p))
            if p < node_count:
                f.write(" | ")
        f.write(")")
        if n < node_count:
            f.write(" & ")
    f.write(")\n")

    # Jeder Knoten maximal einmal enthalten
    f.write("& (")
    for n in xrange(1, node_count + 1):
        for p1 in xrange(1, node_count + 1):
            for p2 in xrange(p1 + 1, node_count + 1):
                f.write("!(" + node(n, p1) + " & " + node(n, p2) + ")")
                if not (n == node_count and p1 == node_count - 1 and p2 == node_count):
                    f.write(" & ")
    f.write(")\n")

    # Verbundenheit und Kreisbedingung

    for n in g.nodes():
        f.write("& (")
        neighbors = g.neighbors(n)
        if len(neighbors) == 0:
            continue;

        for p in xrange(1, node_count):
            if p > 1:
                f.write("\n& ")
            f.write("(" + node(n, p) + " -> (")
            if p == 1: #Kreisbedingung
                f.write("(")
                first = 1
                for neighbor in neighbors:
                    if first:
                        first = 0
                    else:
                        f.write(" | ")
                    f.write(node(neighbor, node_count))
                f.write(") & ")
            f.write("(")
            first = 1
            for neighbor in neighbors:
                if first:
                    first = 0
                else:
                    f.write(" | ")
                f.write(node(neighbor, p+1))
            f.write(")))")

        if node_count > 1:
            f.write("\n& (" + node(n, node_count) + " -> (")
            first = 1
            for neighbor in neighbors:
                if first:
                    first = 0
                else:
                    f.write(" | ")
                f.write(node(neighbor, 1))
            f.write("))")

        f.write(")\n")
    f.close()

    # In CNF konvertieren
    f_cnf = open(ofile_cnf, "w")
    subprocess.call(["./bool2cnf/bool2cnf", "-s", ofile_sat], stdout=f_cnf)

def minsat(file_cnf, ofile_res):
    util.silentremove(ofile_res)
    FNULL = open(os.devnull, 'w')
    subprocess.call(["minisat", file_cnf, ofile_res], stdout=FNULL, stderr=subprocess.STDOUT)

    signature = util.load_signature(file_cnf)
    position = {}
    with open(ofile_res) as fp:
        result = fp.readline().rstrip('\n')
        if(result == "UNSAT"):
            sys.exit(20)

        if(result == "SAT"):
            for literal in fp.readline().rstrip('\n').split():
                if literal[0] != '-' and signature.has_key(literal):
                    node_pos = signature[literal]
                    position[node_pos[0]] = int(node_pos[1])
            print tuple(x[0] for x in sorted(position.items(), key=operator.itemgetter(1)))
            sys.exit(10)

        sys.exit(15)



satify(sys.argv[1], "Temp.sat", "Temp.cnf")
minsat("Temp.cnf", "Temp.res")