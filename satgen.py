import sys
import subprocess
import operator
import os

import dimacs
import util

def node(n, p):
    return "n" + str(n)+ "_" + str(p)

def node_alias(n, p, c):
    return str((n-1) * c + p)

def from_node_alias(v, c):
    n = (v // c) + 1
    p = v % c
    if p == 0:
        n -= 1
        p = c
    return (n, p)

def end_cnf_line(f):
    f.write("0\n")

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

def satify_cnf(file_graph, ofile_cnf):
    util.silentremove(ofile_cnf)

    g = dimacs.load_file(file_graph)
    with open(ofile_cnf, "w") as f:
        node_count = len(g.nodes())
        f.write("c " + str(node_count) + "\n")

        # Zeile fuer DIMACS Header reservieren
        offset_header = f.tell()
        f.write(' ' * 100 + "\n")

        clause_count = 0

        # Jeder Knoten mindestens einmal enthalten
        # (n1_1 | ... | n1_6) & (n2_1 | ... | n2_6) & ...
        for n in xrange(1, node_count + 1):
            for p in xrange(1, node_count + 1):
                f.write(node_alias(n, p, node_count) + " ")
            end_cnf_line(f)
            clause_count += 1

        # Jeder Knoten maximal einmal enthalten
        # !(n1_1 & n1_2) & !(n1_1 & n1_3) & ... = (!n1_1 | !n1_2) & (!n1_1 | !n1_3) & ...
        for n in xrange(1, node_count + 1):
            for p1 in xrange(1, node_count + 1):
                for p2 in xrange(p1 + 1, node_count + 1):
                    f.write("-" + node_alias(n, p1, node_count) + " -" + node_alias(n, p2, node_count) + " ")
                    end_cnf_line(f)
                    clause_count += 1
        # Jede Position einmal belegt       
        for p in xrange(1, node_count + 1):
            for n in xrange(1, node_count + 1):
                f.write(node_alias(n, p, node_count) + " ")
            end_cnf_line(f)
            clause_count += 1
        
        # Verbundenheit und Kreisbedingung
        # n1_2 -> (n2_3 | n5_3 | n6_3) = !n1_2 | n2_3 | n5_3 | n6_3
        #
        for n in g.nodes():
            for p in xrange(1, node_count):
                if p == 1: #Kreisbedingung
                    f.write("-" + node_alias(n, p, node_count) + " ")
                    for predecessor in g.predecessors(n):
                        f.write(node_alias(predecessor, node_count, node_count) + " ")
                    end_cnf_line(f)
                    clause_count += 1

                f.write("-" + node_alias(n, p, node_count) + " ")
                for successor in g.successors(n):
                    f.write(node_alias(successor, p+1, node_count) + " ")
                end_cnf_line(f)
                clause_count += 1

            if node_count > 1:
                f.write("-" + node_alias(n, node_count, node_count) + " ")
                for successor in g.successors(n):
                    f.write(node_alias(successor, 1, node_count) + " ")
                end_cnf_line(f)
                clause_count += 1

        #DIMACS Header schreiben
        f.seek(offset_header)
        f.write("p cnf " + node_alias(node_count, node_count, node_count) + " " + str(clause_count))

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

def minsat_cnf(file_cnf, ofile_res):
    util.silentremove(ofile_res)
    FNULL = open(os.devnull, 'w')
    subprocess.call(["minisat", file_cnf, ofile_res], stdout=FNULL, stderr=subprocess.STDOUT)

    position = {}
    node_count = util.load_node_count(file_cnf)
    with open(ofile_res) as fp:
        result = fp.readline().rstrip('\n')
        if(result == "UNSAT"):
            sys.exit(20)

        if(result == "SAT"):
            for literal in fp.readline().rstrip('\n').split():
                if literal[0] != '-' and literal != '0':
                    node_pos = from_node_alias(int(literal), node_count)
                    position[node_pos[0]] = node_pos[1]
            print ' '.join(map(str, list(x[0] for x in sorted(position.items(), key=operator.itemgetter(1)))))
            sys.exit(10)

        sys.exit(15)



# satify(sys.argv[1], "Temp.sat", "Temp.cnf")
# minsat("Temp.cnf", "Temp.res")

satify_cnf(sys.argv[1], "Temp2.cnf")
minsat_cnf("Temp2.cnf", "Temp2.res")
