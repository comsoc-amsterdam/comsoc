# DEMO: Displaying Justifications of Collective Decisions

This repository contains the code for the [web-app demo](https://demo.illc.uva.nl/justify) for the automated justification of collective decisions. The demo allows users to search for axiomatic justifications of voting outcomes in small-scale scenarios [1,2,6]. A more detailed description of the demo is available [3].

The code was developed with reusability in mind and therefore also provides a broader Python framework for research in Computational Social Choice [4]. In particular, it includes tools for SAT-based reasoning about voting rules and axioms [5], together with functionality used by the justification algorithms underlying the demo. For a more in-depth introduction to the general framework and examples of its use, see [`Example.ipynb`](https://github.com/comsoc-amsterdam/comsoc/blob/main/Example.ipynb).

The code was mainly developed by Oliviero Nardi and Arthur Boixel. 

## Installation

Install the required Python packages with:

    pip install -r requirements.txt

For tasks that require the enumeration of MUSes (including the demo), compile `MARCO`. Inside `COMSOC/MARCO/src/pyminisolvers`, run

    make
    make test

Consult [`COMSOC/MARCO/README.md`](https://github.com/comsoc-amsterdam/comsoc/blob/main/COMSOC/MARCO/README.md) for more information. Finally, some code (in particular the demo) requires `graphviz`. On Ubuntu:

	sudo apt install graphviz

On Arch linux:

	sudo pacman -S graphviz

## Running the demo locally

First, make sure to install all the Python dependencies, `graphviz`, and to compile `MARCO`. 

Then, run the following commands (in the folder where `wsgi.py` is located) on **two different** shells:

    python wsgi.py

and

    celery -A wsgi.celery worker --pool=solo --loglevel=INFO

Then, the demo will be available locally at [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

### Troubleshooting for the demo

If you get an error message saying "Error 111 connecting to localhost:6379. Connection refused.", you might have to install `redis-server`. How to do so might depend on your system.

On Ubuntu:

    sudo apt-get install redis-server

On Arch linux:

    sudo pacman -S valkey
    sudo systemctl enable --now redis.service

For instructions on how to run the web-app demo locally, see `WebApp/README.md`.

## Included Solvers

This code includes the `MARCO` MUS enumeration tool by Mark Liffiton and Wenting Zhao, which in turn includes the following solvers:
* `MUSer2`: Anton Belov, Norbert Manthey, and Joao Marques-Silva
* `MiniSAT`: Niklas Een and Niklas Sörensson
* `MiniCARD`: Mark Liffiton and Jordyn Maglalang

## References

[1] Arthur Boixel and Ulle Endriss. Automated Justification of Collective Decisions via Constraint Solving. In *Proceedings of the 19th International Conference on Autonomous Agents and Multiagent Systems (AAMAS-2020)*, IFAAMAS, 2020.

[2] Arthur Boixel, Ulle Endriss, and Ronald de Haan. A Calculus for Computing Structured Justifications for Election Outcomes. In *Proceedings of the 36th AAAI Conference on Artificial Intelligence (AAAI-2022)*, AAAI Press, 2022.

[3] Arthur Boixel, Ulle Endriss, and Oliviero Nardi. Displaying Justifications for Collective Decisions. In *Proceedings of the 31st International Joint Conference on Artificial Intelligence (IJCAI-2022)*, 2022. Demo Paper.

[4] Felix Brandt, Vincent Conitzer, Ulle Endriss, Jérôme Lang, and Ariel D. Procaccia, editors. *Handbook of Computational Social Choice*. Cambridge University Press, 2016.

[5] Christian Geist and Dominik Peters. Computer-Aided Methods for Social Choice Theory. In: Ulle Endriss, editor, *Trends in Computational Social Choice*. AI Access, 2017.

[6] Oliviero Nardi, Arthur Boixel, and Ulle Endriss. A Graph-Based Algorithm for the Automated Justification of Collective Decisions. In *Proceedings of the 21st International Conference on Autonomous Agents and Multiagent Systems (AAMAS-2022)*, IFAAMAS, 2022.
