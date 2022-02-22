from COMSOC.anonymous.model import AnonymousScenario as Scenario
from COMSOC.anonymous.model import AnonymousOutcome as Outcome
from COMSOC.anonymous.model import AnonymousPreference as Preference
from COMSOC.anonymous.model import AnonymousProfile as Profile

import COMSOC.anonymous.rules as rules
import COMSOC.anonymous.axioms as axioms

def get_axioms(scenario: Scenario, axiom_list: list) -> set:
    """ Return a set of axioms """
    result = set()
    for axiom in axiom_list:
        result.add({
            "Faithfulness": axioms.Faithfulness(scenario),
            "Reinforcement": axioms.Reinforcement(scenario),
            "Cancellation": axioms.Cancellation(scenario),
            "Pareto": axioms.Pareto(scenario),
            "Neutrality": axioms.Neutrality(scenario),
            "Condorcet": axioms.Condorcet(scenario),
            "PositiveResponsiveness": axioms.PositiveResponsiveness(scenario)
        }[axiom])

    return result