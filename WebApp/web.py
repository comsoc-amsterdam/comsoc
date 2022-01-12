#!/usr/bin/python

from flask import Flask, request, render_template, url_for
from flask_socketio import SocketIO

import sys
sys.path.append("..") 

import COMSOC.anonymous as theory
from COMSOC.problems import JustificationProblem
from COMSOC.just import Symmetry, QuasiTiedWinner, QuasiTiedLoser


app = Flask(__name__)
socketio = SocketIO(app)

axiom_names = sorted("Pareto, Reinforcement, Faithfulness, Neutrality, Cancellation, PositiveResponsiveness".split(', '))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buildprofile', methods=["POST"])
def buildprofile():
    return render_template('buildprofile.html', candidates = list(request.form.values()), axioms = axiom_names)

@app.route('/result', methods=["POST"])
def result():
    profile_name = None
    axioms = []
    outcome_names = set()

    for key, value in request.form.items():
        if key == "profile":
            profile_name = value
        elif key[:6] == "axiom_":
            axioms.append(value)
        elif key[:8] == "outcome_":
            outcome_names.add(value)

    voters = 0
    candidates = None
    for c_ballot in profile_name.split(','):
        count, ballot = c_ballot.split(':')
        voters += int(count)
        if candidates is None:
            candidates = set(ballot.split('>'))

    scenario = theory.Scenario(voters, candidates)

    profile = scenario.get_profile(profile_name)
    outcome = scenario.get_outcome(','.join(outcome_names))
    corpus = eval(f"{{{', '.join(f'theory.axioms.{axiom}(scenario)' for axiom in axioms)}}}")

    problem = JustificationProblem(profile, outcome, corpus)

    derived = {Symmetry(scenario), QuasiTiedWinner(scenario),\
                                                      QuasiTiedLoser(scenario)}

    shortest = None
    for justification in problem.solve(extract = "SAT", nontriviality = ["from_folder", "ignore"], depth = 3, heuristics = True, maximum = 100, \
                                      derivedAxioms = derived, nb_folder = '../knownbases'):
        
        if shortest is None:
            shortest = justification
        else:
            shortest = min((shortest, justification), key = lambda j : (len(j.involved_profiles), len(j)))
            
    if shortest is None:
        return render_template('failure.html')
    else:
        return shortest.display()


if __name__ == '__main__':
    ip, port = '127.0.0.1', 5000
    print(f"Go to http://{ip}:{port}/")
    socketio.run(app, host=ip, port=port)