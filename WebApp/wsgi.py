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

########### imports ################

from flask import Flask, request, render_template, url_for
from flask_mail import Mail, Message

from secret import password

import base64
import time
import os

import COMSOC.anonymous as theory  # We work with anonymous voting
from COMSOC.problems import JustificationProblem
from COMSOC.just import Symmetry, QuasiTiedWinner, QuasiTiedLoser

############ Preliminary definitions ###############

flask_app = Flask(__name__)

mail_settings = {
    "MAIL_SERVER": 'smtp.mail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "comsoc.justify@mail.com",
    "MAIL_PASSWORD": password  # inside secret.py
}

flask_app.config.update(mail_settings)
mail = Mail(flask_app)

# Celery backend
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

# Call all axioms with their default name, except for PositiveResponsiveness.
axiom_names = {axiom:axiom for axiom in axiom_description.keys()}
axiom_names["Responsiveness"] = "PositiveResponsiveness"

############ Helper functions ###############

# Check if a name contains special chars
def bad_input(string):
    return any(map(lambda x: not x.isalpha(), string))

# Given a profile string, return the Scenario it induces and the profile object itself.
def parse_profile(profile_name: str):
    voters = 0
    alternatives = None
    # In this loop, we deduce the number of voters and the alternatives.
    # values are comma-separated
    for c_ballot in profile_name.split(','):
        # each value is <count>:<preference>
        count, ballot = c_ballot.split(':')
        voters += int(count)
        # Deduce the alternatives from the first preference (they are >-sperated)
        if alternatives is None:
            alternatives = set(ballot.split('>'))

    # Now, we can create a scenario
    scenario = theory.Scenario(voters, alternatives)
    profile = scenario.get_profile(profile_name)

    return scenario, profile

# A celery task that (if possible) retrieves a justification and return an html page describing it
@celery.task(name='uwsgi_file_web.compute_justification')
def compute_justification(profile_name: str, axioms: list, outcome_names: list):

    # Get the scenario and the profile
    scenario, profile = parse_profile(profile_name)

    # Check input
    for a in scenario.alternatives:
        if bad_input(a):
            return "Bad input!"

    # Get the outcome
    outcome = scenario.get_outcome(','.join(outcome_names))
    # Get the relevant axioms
    corpus = theory.get_axioms(scenario, (axiom_names[axiom] for axiom in axioms))

    # Construct the justification problem
    problem = JustificationProblem(profile, outcome, corpus)

    # Derived axiom heuristics to use
    derived = {
        Symmetry(scenario),
        QuasiTiedWinner(scenario),
        QuasiTiedLoser(scenario)}

    shortest = None  # Shotest (cardinality of the explanation) justification will be stored here
    # Iterate over up to 5 justifications with a depth of 3, using heuristics
    for justification in problem.solve(extract = "SAT", nontriviality = ["from_folder", "known_faults"], depth = 3, heuristics = True, maximum = 5, \
                                      derivedAxioms = derived, nb_folder = 'knownbases'):
        # Memorise the shortest justification here
        if shortest is None:
            shortest = justification
        else:
            shortest = min((shortest, justification), key = lambda j : (len(j.involved_profiles), len(j)))

    # No justification found: present failure message
    if shortest is None:
        # the .prettify method takes a profile/outcome and converts it into a nice HTML format
        return render_template('failure.html', profile_text = profile.prettify(), outcome = outcome.prettify(),\
            axioms = axioms)
    else:
        # Return the HTML website for the justification
        data_pack = shortest.displayASP(display = 'website')
        return render_template("justification.html", **data_pack)

############ Web Pages ###############

# Index page
@flask_app.route('/')
def index():
    return render_template('index.html')

@flask_app.route('/buildprofile', methods=["POST"])
def buildprofile():
    for val in request.form.values():
        if bad_input(val):
            return "Bad input!"

    return render_template('buildprofile.html', candidates = list(request.form.values()))

@flask_app.route('/outcomes', methods=["POST"])
def outcomes():
    profile_name = request.form['profile']

    scenario, profile = parse_profile(profile_name)

    # Check input
    for a in scenario.alternatives:
        if bad_input(a):
            return "Bad input!"

    return render_template('outcomes.html', profile_name = profile_name, profile_text = profile.prettify(),\
        candidates = sorted(scenario.alternatives), axiom_names = sorted(axiom_description.keys()), axiom_description = axiom_description)

@flask_app.route('/result', methods=["POST"])
def result():
    profile_name = None
    axioms = []
    outcome_names = []

    for key, value in request.form.items():
        if key == "profile":
            profile_name = value
        elif key[:6] == "axiom_":
            # Check input
            if bad_input(value):
                return "Bad input!"
            axioms.append(value)
        elif key[:8] == "outcome_":
            # Check input
            if bad_input(value):
                return "Bad input!"
            outcome_names.append(value)

    try:
        result = compute_justification.delay(profile_name, axioms, outcome_names)
        result = result.get(timeout=30)
    except TimeoutError:
        scenario, profile = parse_profile(profile_name)

        # Check input
        for a in scenario.alternatives:
            if bad_input(a):
                return "Bad input!"

        outcome = scenario.get_outcome(','.join(outcome_names))
        return render_template('timeout.html', profile_text = profile.prettify(), outcome = outcome.prettify(),\
            axioms = axioms)

    return result

@flask_app.route('/feedback', methods=["POST"])
def feedback():
    message = f"understandability: {request.form['understandability']}\nconvincingess: {request.form['convincingness']}\n\n"
    if request.form['feedback'] != '':
        message += f"EXTRA FEEDBACK:\n\"{request.form['feedback']}\"\n\n"
    message += "Please find the justification file attached."

    html_justification = base64.b64decode(request.form["html_justification"]).decode()
    justification = base64.b64decode(request.form["justification"])

    # removed for security reasons

    """filename = f"feedbacks/justification_{int(time.time())}"

    os.mkdir(filename)

    with open(filename + "/justification.pickle", "wb") as f:
        f.write(justification)
    with open(filename + "/justification.html", "w") as f:
        f.write(html_justification)
    with open(filename + "/feedback.txt", "w") as f:
        f.write(message)""" 

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