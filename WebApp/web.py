#!/usr/bin/python

from flask import Flask, request, render_template, url_for
from flask_socketio import SocketIO

import sys
sys.path.insert(0, "../")

import COMSOC.anonymous as theory
from COMSOC.problems import JustificationProblem

from COMSOC.just import Symmetry, QuasiTiedWinner, QuasiTiedLoser

app = Flask(__name__)
socketio = SocketIO(app)

figures = ['circle_alt', 'triangle_alt', 'square_alt']
# Uncomment this to have 4 alternatives.
figures = ['circle_alt', 'triangle_alt', 'square_alt', 'pentagon_alt']

@app.route('/')
def index():
    return render_template('index.html', voters = 1, figures = figures)

@app.route('/result', methods=['POST'])
def handle_data():
    prof_dict = {}
    for ballot_str in request.form['profile'].split(';'):
        ballot = theory.Preference(ballot_str.split(','))
        prof_dict[ballot] = prof_dict[ballot]+1 if ballot in prof_dict else 1

    profile = theory.Profile(prof_dict)
    scenario = theory.Scenario(len(profile), set(profile.alternatives))
    outcome = theory.Outcome(request.form['outcome'].split(','))

    corpus = {
        theory.axioms.Faithfulness(scenario),
        theory.axioms.Reinforcement(scenario),
        theory.axioms.Cancellation(scenario),
        theory.axioms.Pareto(scenario),
        theory.axioms.Neutrality(scenario),
        theory.axioms.PositiveResponsiveness(scenario)
    }

    problem = JustificationProblem(profile, outcome, corpus)

    derived = {Symmetry(scenario), QuasiTiedWinner(scenario),\
                                                      QuasiTiedLoser(scenario)}

    shortest = None
    for justification in problem.solve(extract = "SAT", nontriviality = ["from_folder", "ignore"], depth = 10, heuristics = True, maximum = 5, \
                                      derivedAxioms = derived, nb_folder = '../knownbases'):
        
        if shortest is None or len(justification) < len(shortest):
            shortest = justification
            
    if shortest is None:
        return render_template('failure.html')
    else:
        instances = set()
        for instance in shortest.explanation:
            text = str(instance)
            for figure in figures:
                text = text.replace(figure, f"<img class='inlineimg' src = {url_for('static', filename=figure + '.svg')} />")

            instances.add(text)

        return render_template('result.html', explanation = instances)

if __name__ == '__main__':
  socketio.run(app, host='127.0.0.1', port=5000)