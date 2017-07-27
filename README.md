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

and then install Python:
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

## Adapting TPF to SWEEP

TPF server and client on http://linkeddatafragments.org/software/ can be used to test SWEEP. But, some changes have to be done.

### TPF Server

SWEEP need the TPF Server log to process. So, changes have to be done on TPF Server code. First change concerns thne file ./bin/ldf-server. Just add the code () :
```nodejs
...
var configDefaults = JSON.parse(fs.readFileSync(path.join(__dirname, '../config/config-defaults.json'))),
    config = _.defaults(JSON.parse(fs.readFileSync(args[0])), configDefaults),
    port = parseInt(args[1], 10) || config.port,
    workers = parseInt(args[2], 10) || config.workers,
    constructors = {};

//------------------> Begin SWEEP <------------------------
var sweep = config.sweep || '' ;
config.sweep = sweep ;
//------------------> End SWEEP <------------------------

// Start up a cluster master
if (cluster.isMaster) {
...
```
Il allows to give the SWEEP URL to the TPF Sever.

## Running SWEEP

From `~/SWEEP` run the comand:
```bash
nohup python3.5 sweep-streamWS.py -g 0.250 -to 0.2 -l 20 --port 5000 &> resSWEEP &
```

```bash
nohup python3.5 qsim-WS.py --sweep http://sweep.priloo.univ-nantes.fr -s http://tpf-server-sweep.priloo.univ-nantes.fr -c /home/sweep/clientLDF/Client.js-master/bin/ldf-client -v -g 0.25 &> resQsim-WS &
```


#### Exemple
You can use any Triple Pattern Fragment client: 
to run SPARQL queries
