### FOR MULTIPLE WORKERS... ###

from celery import Celery
from celery.exceptions import TimeoutError
import billiard

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

###############################

from flask import Flask, request, render_template, url_for
from flask_socketio import SocketIO

import sys
sys.path.append("..") 

import COMSOC.anonymous as theory
from COMSOC.problems import JustificationProblem
from COMSOC.just import Symmetry, QuasiTiedWinner, QuasiTiedLoser


flask_app = Flask(__name__)
flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(flask_app)

axiom_names = sorted("Pareto, Reinforcement, Faithfulness, Neutrality, Cancellation, PositiveResponsiveness".split(', '))

@flask_app.route('/')
def index():
    return render_template('index.html')

@flask_app.route('/buildprofile', methods=["POST"])
def buildprofile():
    return render_template('buildprofile.html', candidates = list(request.form.values()), axioms = axiom_names)

@celery.task(name='uwsgi_file_web.compute_justification')
def compute_justification(profile_name, axioms, outcome_names):

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

@flask_app.route('/result', methods=["POST"])
def result():
    profile_name = None
    axioms = []
    outcome_names = []

    for key, value in request.form.items():
        if key == "profile":
            profile_name = value
        elif key[:6] == "axiom_":
            axioms.append(value)
        elif key[:8] == "outcome_":
            outcome_names.append(value)

    try:
        result = compute_justification.delay(profile_name, axioms, outcome_names)
        result = result.get(timeout=60)
    except TimeoutError:
        return render_template('failure.html')

    return result