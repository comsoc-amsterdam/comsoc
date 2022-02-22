import clingo
from .tree import ProofTree
import re
from itertools import chain
from COMSOC.voting.encodings import ASPEncodingHandler

class ASPTree():
    'Encode a justification as an ASP program'

    def __init__(self, justification, limit = 0, verbose = False, prettify = False):
        self.justification = justification
        self.encoding = ASPEncodingHandler()
        self.encoding.encode_profile(justification.profile)  # by doing so, it sets it as "p0" (it's the first one)

        self.baseProgram = self.getBaseProgram()
        self.stepProgram = self.getStepProgram()
        self.checkProgram = self.getCheckProgram()

        # print('\n'.join((self.baseProgram, self.stepProgram, self.checkProgram)))

        # Minimum and maximum values for t
        # (grounding is done for all 1 <= t <= max_t,
        # and solving is done for min_t <= t <= max_t).
        self.min_t = 1
        self.max_t = self.getUpperBoundNumberNodes()

        # Time limit in seconds for each solving round (if incremental solving is used)
        # (if at any point the solving times out, the whole process is stopped)
        self.maxTimeLimit = 100

        self.limit = limit
        self.answerSets = []

        self._verbose = verbose
        self._prettify = prettify

    def getProofTrees(self):
        return (ProofTree(answerSet, self.encoding, self.fact2instance) for answerSet in self.getAnswerSets()), self.encoding

    def getAProofTree(self):
        for answerSet in self.getAnswerSets(): break
        return ProofTree(answerSet, self.encoding, self.fact2instance), self.encoding        

    def getTree(self, answerSet):
        tree = ProofTree(answerSet, self.encoding, self.fact2instance)
        return tree.getTreeFromAnswerSet(self._prettify)    

    def getTrees(self):
        for answerSet in self.getAnswerSets():
            yield self.getTree(answerSet)

    def getUpperBoundNumberNodes(self):
        """Return an upper bound on the maximal number of nodes that are necessary to represent the justification."""

        # Need to be refined (RESEARCH QUESTION, or take different approach)

        # Need to introduce all profiles
        up = len(self.justification.involved_profiles)

        # Need to use all instances
        up += len(self.justification.explanation)

        # Need to consider branching possibilities
        up += len(self.justification.scenario.outcomes) * len(self.justification.involved_profiles)

        up //= 2

        return 42 #up

    def on_model(self, model):
        """Add the newly found model (if optimal) to the list of models."""

        if not model.optimality_proven:
            return

        answerSet = []

        for atom in model.symbols(shown=True):
            answerSet.append(atom)

        #print("Answer Set: {%s}\n", ",".join([str(a) for a in answerSet]))
        self.answerSets.append(answerSet)

    def getAnswerSets(self):
        """Return the answer sets, if any, for the considered program."""

        step = 3
        previous_step = 0

        for k in range(step, self.max_t + 1, step):
            nodeFacts = str(previous_step) + " < {node(1.." + str(k) +")} <= " + str(k) + ".\n"
            previous_step = k

            if self._verbose:
                print("Step: " + nodeFacts)
            finalBaseProgram = self.baseProgram + nodeFacts

            control = clingo.Control();

            control.add("base", [], finalBaseProgram);

            # Ground the base program
            control.ground([("base", [])]);

            # Take optimisation statement into account
            control.configuration.solve.opt_mode = "optN"  # pylint: disable=no-member
            # Only retrieve limit answer sets
            control.configuration.solve.models = self.limit  # pylint: disable=no-member

            # Call the clingo solver, passing on the function on_model for when an answer set is found
            answer = control.solve(on_model=self.on_model)

            if answer.satisfiable == True:
                break

        return self.answerSets

    def getAnswerSetsIncremental(self):
        """Return the answer sets, if any, for the considered program using incremental solving."""

        #print("#####\n" + self.program + "\n#####")
        control = clingo.Control()

        control.add("base", [], self.baseProgram)
        control.add("step", ["t"], self.stepProgram)
        control.add("check", ["t"], self.checkProgram)

        control.ground([("base", [])])

        # Take optimisation statement into account
        control.configuration.solve.opt_mode = "optN"  # pylint: disable=no-member
        # Only retrieve limit answer sets
        control.configuration.solve.models = self.limit  # pylint: disable=no-member

        # The incremental (or multi-shot) solving process
        timed_out = False
        result, step = None, 0
        while (not timed_out and step <= self.max_t and (step == 0 or step <= self.min_t or not result.satisfiable)):
            parts = []
            # For subsequent steps t, add/ground the programs step(t) and check(t)
            # and update the external query atom so that only query(t) is true
            if step > 0:
                control.release_external(
                clingo.Function("query", [clingo.Number(step - 1)])
                )
                parts.append(("step", [clingo.Number(step)]))
                parts.append(("check", [clingo.Number(step)]))
                control.cleanup()
                control.ground(parts)
                print("Grounding [step {}]..".format(step))
                control.assign_external(clingo.Function(
                "query", [clingo.Number(step)]), True)

            # For steps that are beyond the minimum t, call the solver
            # (and give max_timelimit as time limit)
            if step >= self.min_t:
                print("Solving [step {}]..".format(step))
                handle = control.solve(
                on_model=self.on_model,
                async_=True
                )
                finished = handle.wait(self.maxTimeLimit)
                if not finished:
                    timed_out = False # Deactivated timed_out
                else:
                    result = handle.get()
            step += 1

        #answer = control.solve(on_model=self.on_model)

        """control = clingo.Control()
        control.add("base", [], self.baseProgram)
        control.add("step", ["t"], "node(t).")
        control.ground([("base", [])])

        # Take optimisation statement into account
        control.configuration.solve.opt_mode = "optN"
        # Only retrieve limit answer sets
        control.configuration.solve.models = self.limit

        for t in range(1, self.max_t +1):
            control.ground([("step", [clingo.Number(t)])])

            # Call the clingo solver, passing on the function on_model for when an answer set is found
            answer = control.solve(on_model=self.on_model)

            if answer.satisfiable == True:
                break

        return self.answerSets"""

    def getBaseProgram(self):
        """ Return the ASP base program, used for incremental solving."""

        # Flatten a list of list
        flatten = lambda t: [item for sublist in t for item in sublist]

        tupleList = []
        tupleList.append(self.getGuessingTreePart())
        tupleList.append(self.getVotingScenarioPart())
        tupleList.append(self.getTreeInformationPart())
        tupleList.append(self.getAuxilliaryPredicatesPart())
        tupleList.append(self.getProofProcedurePart())
        tupleList.append(self.getExpansionRulesPart())
        tupleList.append(self.getExplanationPart())

        # Unzip all tuples of size 3 to a list of 3 lists
        resList = [flatten(list(tuple)) for tuple in zip(*tupleList)]

        facts = resList[0]
        rules = resList[1]
        constraints = resList[2]

        statements = self.getSolvingPart()

        baseProgram = "#program base.\n"
        baseProgram +=  "\n".join([fact for fact in facts])
        baseProgram += "\n"
        baseProgram += "\n".join([rule for rule in rules])
        baseProgram += "\n"
        baseProgram += "\n".join([constraint for constraint in constraints])
        baseProgram += "\n"
        baseProgram += "\n".join([statement for statement in statements])
        baseProgram += "\n"

        return baseProgram

    def getGuessingTreePart(self):
        "Return the ASP facts, rules and constraints necessary to guess a tree."
        facts = []
        rules = []
        constraints = []

        # Determining min and max number of nodes now included in the solving process
        # Max number of nodes that can be created
        #k = self.justificationReaderInterface.getUpperBoundNumberNodes()

        #facts.append("#const k=" + str(k) +".")
        #facts.append("{node(1..k)} k.")

        # Used for incremental solving ( exactly numberNodes(t) at step t)
        #rules.append("numberNodes(D) :- D = #count {N: node(N)}.")

        # Root of the tree
        facts.append("node(1).")
        facts.append("root(1).")

        # Directed Graph
        rules.append("{ edge(N1,N2); edge(N2,N1) } 1 :- node(N1), node(N2), N1 < N2.")

        # In-degree of one, except for root
        rules.append("1 { edge(N1,N2) : node(N1), N1 < N2 } 1 :- node(N2), not root(N2).")

        # In-degree 0 for root
        constraints.append(":- edge(N,R), node(N), root(R).")

        # Acyclic Graph
        rules.append("path(N1,N2) :- edge(N1,N2).")
        rules.append("path(N1,N3) :- path(N1,N2), path(N2,N3).")
        constraints.append(":- path(N,N).")

        # Connected Graph
        constraints.append(":- not path(R,N), root(R), node(N), R != N.")

        # Extract leaves of the tree (root is not one, useless?)
        rules.append("leaf(L) :- node(L), not root(L), #count {N: node(N), edge(L,N)} = 0.")
        # Useless?
        facts.append("1 {leaf(N): node(N)}.")

        # Breaking symmetries up to a renaming of the nodes
        constraints.append(":- path(N1,N2), N2 < N1.")
        constraints.append(":- node(N), not node(N-1), N != 1.")

        return facts, rules, constraints

    def getVotingScenarioPart(self):
        "Return the ASP facts, rules and constraints necessary to define a voting scenario."
        facts = []
        rules = []
        constraints = []

        for profile in self.justification.involved_profiles:
            facts.append("profile(" + self.encoding.encode_profile(profile) + ").")

        # Profiles
        #for id in range(self.justificationReaderInterface.getNbProfiles()):
        #    facts.append("profile(p" + str(id) + ").")

        # Alternatives
        for alt in self.justification.scenario.alternatives:
            facts.append("alternative(" + self.encoding.encode_alternative(alt) + ").")

        # Possible Outcomes
        facts.append("outcome(oEmpty).")

        for outcome in self.justification.scenario.outcomes:
            facts.append("outcome(" + self.encoding.encode_outcome(outcome) + ").")
            if len(outcome) == len(self.justification.scenario.alternatives):
                facts.append("fullOutcome(" + self.encoding.encode_outcome(outcome) + ").")

        # Link alternatives to outcomes
        for outcome in self.justification.scenario.outcomes:
            for alt in outcome:
                facts.append("inOutcome(" + self.encoding.encode_alternative(alt) + ", " + self.encoding.encode_outcome(outcome) + ").")

        return facts, rules, constraints

    def getTreeInformationPart(self):
        """Return the ASP facts, rules and constraints necessary to turn a tree into a proof tree."""
        facts = []
        rules = []
        constraints = []

        # If a profile has been introduced it should stay
        rules.append("1 {statement(N2,P,O): outcome(O)} :- edge(N1,N2), node(N1), node(N2), statement(N1,P,_).")

        # Either some (non-empty) outcomes are still possible XOR only oEmpty is possible
        constraints.append(":- statement(N,P,oEmpty), statement(N,P,O), O != oEmpty, node(N), profile(P).")

        # An edge links two nodes via exactly one axiom instance that can be used
        rules.append("1 {step(I,N1,N2): instance(I), canBeUsed(I, N1, N2)} 1 :- edge(N1,N2).")
        # Can't use an instance not associated to an edge
        constraints.append(":- step(I,N1,N2), instance(I), node(N1), node(N2), not edge(N1,N2).")

        # Identify highest priority for rules applicable on a given node
        #rules.append("highestPriority(M,N1,N2) :- node(N1), node(N2), N1 < N2, edge(N1,N2), M = #max {W : priority(W,I), canBeUsed(I,N1,N2)}.")

        # Can't use a low priority instance
        #constraints.append(":- step(I,N1,N2), instance(I), node(N1), node(N2), priority(W,I), not highestPriority(W,N1,N2).")

        # Reading the tree in a depth-first way
        constraints.append(":- step(I,N1,N2), not rightBranch(I) , node(N1), node(N2), N2 != N1 + 1.")
        rules.append("rightBranch(I) :- instance(I), profile(P), outcome(O), I = branching(P,O,right).")

        return facts, rules, constraints

    def getAuxilliaryPredicatesPart(self):
        """Return the ASP facts, rules and constraints encoding auxilliary predicates re-used somewhere else."""
        facts = []
        rules = []
        constraints = []

        rules.append("alwaysWinIn(N,X,P) :- node(N), profile(P), alternative(X), C1 = #count {outcome(O) : statement(N, P, O)}, C2 = #count {outcome(O) : statement(N, P, O), inOutcome(X, O)}, C1 == C2.")

        # True iff P has a single (non empty) outcome available in node N
        rules.append("outcomeFixed(P,N) :- node(N), profile(P), #count {outcome(O): outcome(O), O != oEmpty, statement(N,P,O)} = 1.")

        # True iff O is the only outcome available for P in N
        rules.append("finaleOutcome(N,P,O) :- node(N), profile(P), outcome(O), outcomeFixed(P,N), statement(N,P,O).")

        # True iff O = O1 \cap O2
        rules.append("isIntersection(O,O1,O2) :- outcome(O), outcome(O1), outcome(O2), #count {alternative(Y): alternative(Y), inOutcome(Y,O), not inOutcome(Y,O1)} = 0, #count {alternative(Y): alternative(Y), inOutcome(Y,O), not inOutcome(Y,O2) } = 0, #count {alternative(Y): alternative(Y), inOutcome(Y,O1), inOutcome(Y,O2), not inOutcome(Y,O)} = 0.")

        # True iff profile P has been previously introduced and is known in N
        rules.append("isIntroduced(P,N) :- profile(P), node(N), statement(N,P,O), outcome(O).")



        return facts, rules, constraints


    def getProofProcedurePart(self):
        """Return the ASP facts, rules and constraints necessary to encode a sound proof procedure."""
        facts = []
        rules = []
        constraints = []

        ### Start

        # No statement in the root
        constraints.append(":- root(R), statement(R,P,O), profile(P), outcome(O).")

        ### Expanding the tree
        # Can't create a new statement out of the blue (except by using intro rule)
        constraints.append(":- step(I,N1,N2), instance(I), I != intro(P), node(N1), node(N2), N1 < N2, statement(N2,P,O), profile(P), outcome(O), O != oEmpty, not statement(N1,P,O).")

        # Instance can only be used once (on a given branch)
        #constraints.append(":- step(I,N1,N2), step(I,N3,N4), instance(I), node(N1), node(N2), node(N3), node(N4), (N1,N2) != (N3,N4), path(N1,N4).")

        # Can't use an instance to loop
        constraints.append(":- step(I,N1,N1), instance(I), node(N1).")

        ### Closing the tree
        # Proof ends if we have, in each leaf, for at least one profile, a contradictory statement
        rules.append("1 {profile(P): statement(L,P,oEmpty)} :- leaf(L).")

        return facts, rules, constraints

    def getBranchingRule(self):
        """Return the ASP facts, rules and constraints necessary to encode the branching rule."""
        facts = []
        rules = []
        constraints = []

        # Branching direction
        facts.append("direction(left).")
        facts.append("direction(right).")

        # Possible branching instances
        rules.append("instance(branching(P,O,D)) :- profile(P), outcome(O), O != oEmpty, direction(D).")

        # Setting priority (Second lowest)
        #rules.append("priority(1,branching(P,O,D)) :- instance(branching(P,O,D)), profile(P), outcome(O), direction(D).")

        # Retrieving used profiles
        rules.append("used(P,branching(P,O,D)) :- instance(branching(P,O,D)), profile(P), outcome(O), direction(D).")


        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if target profile is has more than one possible outcome, and O is one of them
        rules.append("localConditionsSatisfied(branching(P,O,D),N):- profile(P), outcome(O), direction(D), node(N), not outcomeFixed(P,N), statement(N,P,O).")

        ### Description of consequences


        # Can't fix O if O already impossible
        constraints.append(":- step(branching(P,O,left), N1, N2), profile(P), outcome(O), node(N1), node(N2), N1 < N2, not statement(N1,P,O).")
        constraints.append(":- step(branching(P,O,right), N1, N2), profile(P), outcome(O), node(N1), node(N2), N1 < N2, not statement(N1,P,O).")

        # Can't branch if outcome for P is fixed
        constraints.append(":- step(branching(P,O,D), N1, N2), profile(P), outcome(O), direction(D), node(N1), node(N2), N1 < N2, outcomeFixed(P,N1).")

        # Branching to the left fixes outcome O
        constraints.append(":- step(branching(P,O,left), N1, N2), profile(P), outcome(O), node(N1), node(N2), N1 < N2, statement(N2,P,O1), O1 != O.")

        # Branching to the right remove outcome O from remaining possible outcomes
        constraints.append(":- step(branching(P,O,right), N1, N2), profile(P), outcome(O), node(N1), node(N2), N1 < N2, statement(N2,P,O).")

        # But keep all other statements
        constraints.append(":- step(branching(P,O,right), N1, N2), profile(P), outcome(O), node(N1), node(N2), N1 < N2, statement(N1,P,O1), outcome(O1), O1 != O, not statement(N2,P,O1).")

        # Can't branch to the left if not branching to the right wrt the same outcome
        rules.append("1 {step(branching(P,O,right), N1, N3): node(N3), N3 != N2} 1 :- step(branching(P,O,left), N1, N2), profile(P), outcome(O), node(N1), node(N2), N1 < N2.")

        # Can't branch to the right is not branching to the left wrt the same outcome
        rules.append("1 {step(branching(P,O,left), N1, N2):  node(N2), N2 != N3} 1 :- step(branching(P,O,right), N1, N3), profile(P), outcome(O), node(N1), node(N3), N1 < N3.")

        # If we are branching (to the left), then that's all we do from N1
        constraints.append(":- step(branching(P,O,left), N1, N2), profile(P), outcome(O), node(N1), node(N2), N1 < N2, step(I,N1,N3), I != branching(P,O,right), node(N3), N3 > N2.")

        # If we are branching (to the right), then that's all we do from N1
        constraints.append(":- step(branching(P,O,right), N1, N3), profile(P), outcome(O), node(N1), node(N3), N1 < N3, step(I,N1,N2), I != branching(P,O,left), node(N2), N2 < N3.")


        # Can't take more than 2 branching steps overall
        facts.append("0 { step(branching(P,O,left)): profile(P), outcome(O) } 2.")

        return facts, rules, constraints


    def getIntroductionRule(self):
        """Return the ASP facts, rules and constraints necessary to encode the introduction rule."""
        facts = []
        rules = []
        constraints = []

        # One introduction rule for each profile
        rules.append("instance(intro(P)) :- profile(P).")

        # Setting rule priority (lowest)
        #rules.append("priority(0,intro(P)) :- instance(intro(P)), profile(P).")

        ### Instance might be usable if rule-specific conditions are met
        # Here, usable if target profile is unknown
        rules.append("localConditionsSatisfied(intro(P),N):- profile(P), node(N), not isIntroduced(P,N).")

        ### Description of consequences
        # Using it actually adds a new trivial statement for profile P (all outcomes are possible)
        rules.append("statement(N2,P,O) :- step(intro(P), N1, N2), instance(intro(P)), node(N1), node(N2), N1 < N2, outcome(O), O != oEmpty.")


        return facts, rules, constraints

    def getExpansionRulesPart(self):
        """Return the ASP facts, rules and constraints necessary to encode the considered expansion rules."""
        facts = []
        rules = []
        constraints = []

        ### Aucilliary predicates
        # True iff node I(N2) \subsetneq I(N1)
        rules.append("isMoreRestrictive(N2,N1) :- node(N1), node(N2), edge(N1,N2), #count {statement(N1,P,O) : statement(N1,P,O), profile(P), outcome(O), not statement(N2,P,O)} != 0. ")

        # True iff a profile has been introduced
        rules.append("talksAboutMoreProfiles(N2,N1) :- node(N1), node(N2), edge(N1,N2), profile(P), isIntroduced(P,N2), not isIntroduced(P,N1).")

        # Using an instance I will not be possible if some relevant profiles have not been introduced in N
        rules.append("relevantProfilesAreKnown(I, N) :- instance(I), node(N), #count {P : profile(P), used(P,I), not isIntroduced(P,N)} = 0.")

        ### Identifying allowed applications of rules
        # An instance I is triggered in node N iff N is internal, all relevant profiles are introduced and local conditions are satisfied
        rules.append("isTriggered(I, N) :- instance(I), node(N), not leaf(N), relevantProfilesAreKnown(I,N), localConditionsSatisfied(I,N).")

        # An instance I can be used to expand tree from N1 to N2 iff it is triggered in N1 and has some consequences on N2
        rules.append("canBeUsed(I, N1, N2) :- instance(I), node(N1), node(N2), N1 < N2, isTriggered(I,N1), #count {isMoreRestrictive(N2,N1) ; talksAboutMoreProfiles(N2,N1)} >= 1.")

        # Generating instances to work with
        for axiom in self.justification.normative:
            axiomFacts, axiomRules, axiomConstraints = axiom.tree_asp()
            facts += axiomFacts
            rules += axiomRules
            constraints += axiomConstraints

        goalFacts, goalRules, goalConstraints = self.justification.goal.tree_asp()
        facts += goalFacts
        rules += goalRules
        constraints += goalConstraints

        introductionFacts, introductionRules, introductionConstraints = self.getIntroductionRule()
        facts += introductionFacts
        rules += introductionRules
        constraints += introductionConstraints

        branchingFacts, branchingRules, branchingConstraints = self.getBranchingRule()
        facts += branchingFacts
        rules += branchingRules
        constraints += branchingConstraints

        # Sutor, ne ultra crepidam (with respect to profiles used in the instance)
        constraints.append(":- step(I, N1, N2), instance(I), node(N1), node(N2), N1 < N2, statement(N1, P, O), profile(P), outcome(O), not used(P,I), not statement(N2, P, O).")

        return facts, rules, constraints

    def getExplanationPart(self):
        """Return the ASP facts, rules and constraints necessary to encode the considered explanation."""
        facts = []
        rules = []
        constraints = []

        self.fact2instance = {}

        # Retrieving instances, and the goal instance
        for instance in chain(self.justification.explanation, [self.justification.goal]):
            for fact in instance.as_asp(self.encoding):
                facts.append("instance(" + fact + ").")
                self.fact2instance[fact] = instance
                # Identifying profiles mentionned in the instance
                for p in re.findall("p\d+", fact):
                    facts.append("used(" + p + "," + fact +").")

        return facts, rules, constraints

    def getSolvingPart(self):
        """Return the ASP statements necessary to encode the solving strategy."""
        statements = []

        statements.append("#minimize {1 @ 2,N: node(N)}.")
        statements.append("#maximize {N @ 1,N: step(intro(P),N,N1)}.")

        statements.append("#show node/1.")
        statements.append("#show edge/2.")
        statements.append("#show step/3.")
        statements.append("#show statement/3.")
        #statements.append("#show instance/1.")
        #statements.append("#show localConditionsSatisfied/2.")
        #statements.append("#show canBeUsed/3.")
        #statements.append("#show used/2.")
        #statements.append("#show priority/2.")
        #statements.append("#show highestPriority/3.")
        #statements.append("#show isMoreRestrictive/2.")
        #statements.append("#show talksAboutMoreProfiles/2.")
        #statements.append("#show isTriggered/2.")

        return statements

    def getStepProgram(self):
        """Return the ASP step program, used for incremental solving."""

        stepProgram = "#program step(t).\n"
        #stepProgram += "nodes(1..t).\n"

        return stepProgram

    def getCheckProgram(self):
        """Return the ASP checkProgram, used for incremental solving."""

        checkProgram = "#program check(t).\n"
        checkProgram += "#external query(t).\n"

        # If query(t) is true, require exactly t chosen nodes.
        #checkProgram += "node(1..t) :- query(t).\n"
        checkProgram += ":- not numberNodes(t), query(t).\n"

        return checkProgram