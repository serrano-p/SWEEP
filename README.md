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

SWEEP need the TPF Server log to process. So, changes have to be done on TPF Server code. First change concerns thne file ./bin/ldf-server. Just add the code (from 'Begin SWEEP' to 'End SWEEP') :
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

Next, install the Request' module and do next changes in ./lib/views/RdfView.js

```nodejs
...

var contentTypes = 'application/trig;q=0.9,application/n-quads;q=0.7,' +
                   'application/ld+json;q=0.8,application/json;q=0.8,' +
                   'text/turtle;q=0.6,application/n-triples;q=0.5,text/n3;q=0.6';

//------------------> Begin SWEEP <------------------------
var http = require('request');
var trace = "";
var cpt = 0;
//------------------> End SWEEP <------------------------


// Creates a new RDF view with the given name and settings
function RdfView(viewName, settings) {
  if (!(this instanceof RdfView))
...

  // Write the triples with a content-type-specific writer
  var self = this,
      writer = /json/.test(settings.contentType) ? this._createJsonLdWriter(settings, response, done)
                                                 : this._createN3Writer(settings, response, done);
  //------------------> Begin SWEEP <------------------------
  cpt += 1;
  settings.cpt =  'e'+process.pid+'-'+cpt ;
  settings.tpList = '';
  //------------------> End SWEEP <------------------------

  settings.writer = writer;

...

  function after()  {
self._renderViewExtensions('After',  settings, request, response, writer.end);

    //------------------> Begin SWEEP <------------------------
    settings.tpList = settings.tpList + '</l>';
    http({
      uri: settings.sweep+"/data",
      method: "POST",
      form: {
        data: settings.tpList,
        no : settings.cpt,
        ip : settings.sweep_ip,
        time : settings.sweep_time
      }
    }, function(error, response, body) {
       console.log('data:',body,error);
    });
    //------------------> End SWEEP <------------------------

}
  function before() {

  //------------------> Begin SWEEP <------------------------
  var ip =
     request.connection.remoteAddress ||
     request.socket.remoteAddress ||
     request.headers['x-forwarded-for'] || request.connection.socket.remoteAddress;

  now = new Date();
  settings.sweep_ip = ip
  settings.sweep_time = now.toJSON()
  trace = '<e>';
  q = settings.query.patternString;
  subject = settings.query.subject;
  predicate = settings.query.predicate;
  object = settings.query.object;
  var s= ( subject=== undefined ? '<s type="var"/>' : toIRI(subject,'s'));
  var p= ( predicate=== undefined ? '<p type="var"/>' : toIRI(predicate,'p'));
  var o= ( object=== undefined ? '<o type="var"/>' : toIRI(object,'o'));
  trace += s+p+o+'</e>';
  settings.tpList = '<l>'+trace;
  //------------------> End SWEEP <------------------------

...

    data: function (s, p, o, g) {
      writer.addTriple(s, p, o, supportsGraphs ? g : null);

      //------------------> Begin SWEEP <------------------------
      if (o === undefined)
        tp = '<d>'+toIRI(s.subject,'s')+''+toIRI(s.predicate,'p')+''+toIRI(s.object,'o')+'</d>';
        else tp = '<d>'+toIRI(s,'s')+' '+toIRI(p,'p')+' '+toIRI(o,'o')+'</d>';
      settings.tpList = settings.tpList + tp
      //------------------> End SWEEP <------------------------

    },
    // Adds the metadata triple to the output
    meta: function (s, p, o) {
      // Relate the metadata graph to the data
      if (supportsGraphs && !metadataGraph) {
        metadataGraph = settings.metadataGraph;
        writer.addTriple(metadataGraph, primaryTopic, settings.fragmentUrl, metadataGraph);
      }
      // Write the triple
      if (s && p && o && !N3.Util.isLiteral(s)) {
        writer.addTriple(s, p, o, metadataGraph);
        //------------------> Begin SWEEP <------------------------
        if (o === undefined)
          tp = '<m>'+toIRI(s.subject,'s')+''+toIRI(s.predicate,'p')+''+toIRI(s.object,'o')+'</m>';
          else tp = '<m>'+toIRI(s,'s')+' '+toIRI(p,'p')+' '+toIRI(o,'o')+'</m>';
        settings.tpList = settings.tpList + tp
        //------------------> End SWEEP <------------------------
      }
    },

...

//------------------> Begin SWEEP <------------------------
function toIRI(s,p) {return s[0]   !== '_' ? (!N3.Util.isLiteral(s) ? '<'+p+' type="iri" val="'+s.replace(/&/gi, "&amp;")+'"/>' : '<'+p+' type="lit"><![CDATA['+s+']]></'+p+'>') : '<'+p+' type="bkn" val="'+s+'"/>';}
//------------------> End SWEEP <------------------------

module.exports = RdfView;

```


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
