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
from flask_mail import Mail, Message

from secret import password

import base64
import re
import time
import os

import sys
sys.path.append("..") 

import COMSOC.anonymous as theory
from COMSOC.problems import JustificationProblem
from COMSOC.just import Symmetry, QuasiTiedWinner, QuasiTiedLoser


flask_app = Flask(__name__)


mail_settings = {
    "MAIL_SERVER": 'smtp.mail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "comsoc.justify@mail.com",
    "MAIL_PASSWORD": password
}

flask_app.config.update(mail_settings)
mail = Mail(flask_app)

flask_app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(flask_app)

axiom_description = {
    "Neutrality": "Treat all alternatives the same.",
    "Faithfulness": "When there is only a single voter, select only that voter's top alternative.",
    "Pareto": "If everyone agrees that one given alternative is dominated by some other given alternative, then do not select the dominated alternative.",
    "Condorcet": "If there is an alternative that wins in pairwise majority contests against all others, then select only that alternative.",
    "Cancellation": "If all alternatives tie in pairwise majority contests, then select all alternatives.",
    "Reinforcement": "When joining two groups of voters, select the intersection of the sets of alternatives you would select for those two groups (unless that intersection is empty).",
    "Responsiveness": "When one of the alternatives you would select for a given profile moves up in the ranking of a voter, select only that alternative in the new profile.",
}

axiom_names = {axiom:axiom for axiom in axiom_description.keys()}
axiom_names["Responsiveness"] = "PositiveResponsiveness"

def parse_profile(profile_name):
    voters = 0
    candidates = None
    for c_ballot in profile_name.split(','):
        count, ballot = c_ballot.split(':')
        voters += int(count)
        if candidates is None:
            candidates = set(ballot.split('>'))

    scenario = theory.Scenario(voters, candidates)
    profile = scenario.get_profile(profile_name)

    return scenario, profile

@flask_app.route('/')
def index():
    return render_template('index.html')

@flask_app.route('/buildprofile', methods=["POST"])
def buildprofile():
    return render_template('buildprofile.html', candidates = list(request.form.values()))

@flask_app.route('/feedback', methods=["POST"])
def feedback():
    message = f"understandability: {request.form['understandability']}\nconvincingess: {request.form['convincingness']}\n\n"
    if request.form['feedback'] != '':
        message += f"EXTRA FEEDBACK:\n\"{request.form['feedback']}\"\n\n"
    message += "Please find the justification file attached."

    html_justification = base64.b64decode(request.form["html_justification"]).decode()
    justification = base64.b64decode(request.form["justification"])

    filename = f"feedbacks/justification_{int(time.time())}"

    os.mkdir(filename)

    with open(filename + "/justification.pickle", "wb") as f:
        f.write(justification)
    with open(filename + "/justification.html", "w") as f:
        f.write(html_justification)
    with open(filename + "/feedback.txt", "w") as f:
        f.write(message)

    try:
        with flask_app.app_context():
            msg = Message(subject="Justification Feedback",
                          sender=flask_app.config.get("MAIL_USERNAME"),
                          recipients=["comsoc.justify@mail.com"],
                          body=message)
            msg.attach("justification.html", "text/html", html_justification)
            msg.attach("justification.pickle", "application/octet-stream", justification)
            mail.send(msg)
    except Exception as e:
        print(e)

    return render_template("message_sent.html")

@flask_app.route('/outcomes', methods=["POST"])
def outcomes():
    profile_name = request.form['profile']

    scenario, profile = parse_profile(profile_name)

    return render_template('outcomes.html', profile_name = profile_name, profile_text = profile.prettify(),\
        candidates = sorted(scenario.alternatives), axiom_names = sorted(axiom_description.keys()), axiom_description = axiom_description)

def make_tables(nodes, all_outcomes, profiles, profile_texts, outcomes, target_outcome):
    tables = {}
    pretty_outcomes = []
    for outcome in all_outcomes:
        pretty_outcomes.append(outcome.prettify().replace('{', '').replace('}', '').replace(', ', '<br>'))  # one above the others

    all_profiles = sorted(profile_texts.keys())
    all_profiles.remove('<i>R</i><sup>*</sup>')
    all_profiles = ['<i>R</i><sup>*</sup>'] + all_profiles

    for node in nodes:
        contradictions = {profile for profile in profiles[node] if "{}" in outcomes[node][profile]}

        greenify = False
        if all_profiles[0] in outcomes[node].keys():
            if len(outcomes[node][all_profiles[0]]) == 1 and target_outcome in outcomes[node][all_profiles[0]]:
                greenify = True

        tables[node] = render_template("tables.html", all_outcomes=all_outcomes,\
            current_profiles=profiles[node], node=node, outcomes=outcomes[node], contradictions=contradictions,\
            pretty_outcomes=pretty_outcomes, pretty_profiles=profile_texts,\
            all_profiles = all_profiles, greenify = greenify).replace('\n', '   ').replace("\"", "\\\"")

    return tables

@celery.task(name='uwsgi_file_web.compute_justification')
def compute_justification(profile_name, axioms, outcome_names):

    scenario, profile = parse_profile(profile_name)

    outcome = scenario.get_outcome(','.join(outcome_names))
    corpus = eval(f"{{{', '.join(f'theory.axioms.{axiom_names[axiom]}(scenario)' for axiom in axioms)}}}")

    problem = JustificationProblem(profile, outcome, corpus)

    derived = {Symmetry(scenario), QuasiTiedWinner(scenario),\
                                                      QuasiTiedLoser(scenario)}

    shortest = None
    for justification in problem.solve(extract = "SAT", nontriviality = ["from_folder", "known_faults"], depth = 3, heuristics = True, maximum = 5, \
                                      derivedAxioms = derived, nb_folder = 'knownbases'):
        
        if shortest is None:
            shortest = justification
        else:
            shortest = min((shortest, justification), key = lambda j : (len(j.involved_profiles), len(j)))

    if shortest is None:
        return render_template('failure.html', profile_text = profile.prettify(), outcome = outcome.prettify(),\
            axioms = axioms)
    else:
        pngs, cmap, outcomes, labels, profiles, profile_texts,\
            sorted_nodes, target_outcome, html, pickled_just = shortest.display(display = 'website')
        all_outcomes = sorted(scenario.outcomes, key = lambda out: (len(out), str(out)))
        tables = make_tables(sorted_nodes, all_outcomes, profiles, profile_texts, outcomes, target_outcome)

        html_encoded = base64.b64encode(html.encode()).decode()
        justif_encoded = base64.b64encode(pickled_just).decode()

        return render_template('justification.html', len_nodes = len(sorted_nodes), outcomes=outcomes,\
            labels=labels, profiles=profiles, nodes=sorted_nodes, pngs=pngs,\
            map=cmap, all_outcomes=all_outcomes, tables=tables, html_justification = html_encoded, justification = justif_encoded)

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
        result = result.get(timeout=30)
    except TimeoutError:
        scenario, profile = parse_profile(profile_name)
        outcome = scenario.get_outcome(','.join(outcome_names))
        return render_template('timeout.html', profile_text = profile.prettify(), outcome = outcome.prettify(),\
            axioms = axioms)

    return result