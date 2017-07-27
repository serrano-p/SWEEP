# Semantic WEb quEry Profiler (SWEEP) Project

SWEEP (Semantic WEb quEry Profiler) is a tool that allows data providers using a TPF server (see LDF @ linkeddatafragments.org/) to manage data usage.


# Testing SWEEP

SWEEP Monitor:
http://sweep.priloo.univ-nantes.fr 

SWEEP TPF Client:
http://tpf-client-sweep.priloo.univ-nantes.fr

SWEEP TPF Server:
http://tpf-server-sweep.priloo.univ-nantes.fr


# Installing SWEEP
## Prelude

#### macOS
You need to install [Homebrew](http://brew.sh/).

and then install Python 2.7:
```bash
brew install python
```
#### Ubuntu
```
sudo apt-get install python-dev python-setuptools
```

## Dependencies
You need to install dependencies with pip:
- lxml
- RDFLib
- networkx
- SPARQLWrapper
- iso8601

SWEEP was tested withn python3.5 and Python3.6.

## Running SWEEP

From `~/SWEEP` run the comand:
```bash
nohup python3.5 sweep-streamWS.py -g 0.250 -to 0.2 -l 20 --port 5000 &> resSWEEP &
```

```bash
nohup python3.5 qsim-WS.py --sweep http://sweep.priloo.univ-nantes.fr -s http://tpf-server-sweep.priloo.univ-nantes.fr -c /home/sweep/clientLDF/Client.js-master/bin/ldf-client -v -g 0.25 &> resQsim-WS &
```


#### Exemple
You can use any Triple Pattern Fragment client: http://linkeddatafragments.org/software/
to run SPARQL queries
