MAX_TIME = 30  # maximum 30 seconds
SHORTEST_OUT_OF = 15 # Find shortest justification (explanation-cardinality wise) among the first 15 you find

### FOR MULTIPLE WORKERS... (see flask documentation for celery) ###

from celery import Celery
from celery.exceptions import SoftTimeLimitExceeded
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

from flask import Flask, request, render_template, redirect
from flask_mail import Mail, Message

from secret import password, privkey, pubkey

import base64
import time
import os
import rsa

import sys
sys.path.append('..')

import COMSOC.anonymous as theory  # We work with anonymous voting
from COMSOC.problems import JustificationProblem
from COMSOC.just import Symmetry, QuasiTiedWinner, QuasiTiedLoser

############ Preliminary definitions ###############

# Regular url_for is buggy, so I do this manually
BASE_URL = "https://demo.illc.uva.nl/justify"

flask_app = Flask(__name__)

"""mail_settings = {
    "MAIL_SERVER": 'smtp.mail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "comsoc.justify@mail.com",
    "MAIL_PASSWORD": password  # inside secret.py
}"""

"""flask_app.config.update(mail_settings)
mail = Mail(flask_app)"""

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
# (see celery documentation)
@celery.task(name='uwsgi_file_web.compute_justification', time_limit = MAX_TIME*2, soft_time_limit = MAX_TIME)
def compute_justification(profile_name: str, axioms: list, outcome_names: list):

    try: 
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
        for justification in problem.solve(extract = "SAT", nontriviality = ["from_folder", "known_faults"], depth = 3, heuristics = True, maximum = SHORTEST_OUT_OF, \
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
                axioms = axioms, base_url = BASE_URL)
        else:
            # Return the HTML website for the justification
            # this "datapack" is a dictionary containing all the data needed to display the website
            data_pack = shortest.displayASP(display = 'website')

            # we need an extra field, however: a signature for the html and pickled justification
            # (these will be sent from this page to an email in case of feedback: we sign them
            # so we can make sure that the feedback we receive is from us and us only)

            # concatenate the sensible data
            sensible = (data_pack["justification_html"]+data_pack["justification_pickle"])
            # sign it
            signature = rsa.sign(sensible.encode(), privkey, 'SHA-1')
            # base64-encode the signature so we can store it into the html page and send it later
            signature = base64.b64encode(signature).decode()
            # add it to the datapack
            data_pack["signature"] = signature

            # unroll the dictionary and display the justification!
            return render_template("justification.html", base_url = BASE_URL, **data_pack)
    except SoftTimeLimitExceeded:
        return None

############ Web Pages ###############

# Index page
@flask_app.route('/')
def index():
    return render_template('index.html', base_url = BASE_URL)

@flask_app.route('/buildprofile', methods=["POST", "GET"])
def buildprofile():

    # If we reach this page by GET, return home
    if request.method == "GET":
        return redirect(BASE_URL)

    # Input sanitisation: the alternatives are in the keys of this dictionary
    for val in request.form.values():
        if bad_input(val):
            return "Bad input!"

    # in this request, we have the alternatives (the keys don't matter)
    return render_template('buildprofile.html', alternatives = list(request.form.values()), base_url = BASE_URL)

@flask_app.route('/outcomes', methods=["POST", "GET"])
def outcomes():

    # If we reach this page by GET, return home
    if request.method == "GET":
        return redirect(BASE_URL)

    # in this request, we have the profile
    profile_name = request.form['profile']
    scenario, profile = parse_profile(profile_name)

    # Input sanitisation
    for a in scenario.alternatives:
        if bad_input(a):
            return "Bad input!"

    return render_template('outcomes.html', profile_name = profile_name, profile_text = profile.prettify(),\
        alternatives = sorted(scenario.alternatives), axiom_names = sorted(axiom_description.keys()), axiom_description = axiom_description,\
        base_url = BASE_URL)

@flask_app.route('/result', methods=["POST", "GET"])
def result():

    # If we reach this page by GET, return home
    if request.method == "GET":
        return redirect(BASE_URL)

    profile_name = None
    axioms = []
    outcome_names = []

    # In this request we have:
    # profile --> the profile
    # outcome_x if x is among the selected winners
    # axiom_A if A is among the chosen axioms
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

    # We try to compute the results.
    result = compute_justification.delay(profile_name, axioms, outcome_names)
    result = result.get()

    if result is None:
        # If we have a timeout, return an error message

        scenario, profile = parse_profile(profile_name)

        # Check input
        for a in scenario.alternatives:
            if bad_input(a):
                return "Bad input!"

        outcome = scenario.get_outcome(','.join(outcome_names))
        # prettify presents profile/outcome in HTML nicely
        return render_template('timeout.html', profile_text = profile.prettify(), outcome = outcome.prettify(),\
            axioms = axioms, base_url = BASE_URL)
    else:
        return result

@flask_app.route('/feedback', methods=["POST", "GET"])
def feedback():

    # If we reach this page by GET, return home
    if request.method == "GET":
        return redirect(BASE_URL)

    # Handle a feedback request
    # request fields: understandability (int), convincingess (int), feedback (a string ot text),
    # justification_html (a base64 encoded html file describing the justification we saw) 
    # justification_pickle (a base64 encoded pickle object encoding the justification we saw)
    # (to see why they are in base64, check the compute_justification function)
    # signature (a RSA signature of the two the html/pickle files (for security reasons))

    # Compose the email message
    message = f"understandability: {request.form['understandability']}\nconvincingess: {request.form['convincingness']}\n\n"
    if request.form['feedback'] != '':
        message += f"EXTRA FEEDBACK:\n\"{request.form['feedback']}\"\n\n"
    message += "Please find the justification files attached."

    b64_html_justification = request.form["justification_html"]
    b64_pickle_justification = request.form["justification_pickle"]

    signature = base64.b64decode(request.form["signature"])

    # Integrity check (we do this because, in theory, some one could fabricate these objects)
    # This signature is procuded when the justification is computed, see the compute_justification function
    try:
        # rsa verification
        rsa.verify((b64_html_justification + b64_pickle_justification).encode(), signature, pubkey)
    except rsa.pkcs1.VerificationError:
        return "Bad input!"

    # Ok, we passed the check. Decode the files from base64 (this returns a bytes object)
    # (the html file is also decoded from the bytes object, as we want a string here)
    justification_html = base64.b64decode(b64_html_justification).decode()
    # (the pickle file is not decoded, we need it in bytes)
    justification_pickle = base64.b64decode(b64_pickle_justification)

    # Save these things to disk
    filename = f"feedbacks/justification_{int(time.time())}"
    os.mkdir(filename)

    with open(filename + "/justification.pickle", "wb") as f:
        f.write(justification_pickle)
    with open(filename + "/justification.html", "w") as f:
        f.write(justification_html)
    with open(filename + "/feedback.txt", "w") as f:
        f.write(message)

    # Try sending an email
    """
    try:
        with flask_app.app_context():
            msg = Message(subject="Justification Feedback",
                          sender=flask_app.config.get("MAIL_USERNAME"),
                          recipients=["comsoc.justify@mail.com"],
                          body=message)
            msg.attach("justification.html", "text/html", justification_html)
            msg.attach("justification.pickle", "application/octet-stream", justification_pickle)
            mail.send(msg)
    except Exception as e:
        print(e)
    """

    # Ok!
    return render_template("message_sent.html", base_url = BASE_URL)


if __name__ == '__main__':
    BASE_URL = "http://127.0.0.1:5000" # for testing purposes...
    flask_app.run(host="127.0.0.1", port=5000)