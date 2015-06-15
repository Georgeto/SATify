SATify transforms the Hamiltonian circle problem into a SAT problem, and solves it using the MiniSat solver.

# Setup
1. Build bool2cnf: run `make all` inside the bool2cnf directory
2. Install python prerequisites: run `pip install networkx`
3. Install the SAT solver MiniSat

# Usage
    python satgen.py <DIMACS graph file>