# Cuds
Each cuds has the following properties:

- `iri`:
- `ontology_type`: 
- `PID`:
- `Description`:
- `Label`:
- `_graph` (rdflib graph):
properties in graph, i.e., given as true triplets:
- 'type: (rdf type)'
- `uuid`
- `creation time`:

There are also some utility methods, including, 

- print_graph
- serilise 


The main methods for cuds, besides init of course are: 

- `add`: add a predicate, relation `rel` to a object `obj`: `c.add(rel, obj)`

# Proxy Cuds

The proxy CUDS takes a local CUDS, or any other CUDS, and returns a proxy to it. 

The Proxy is managed by a session through a session handler. 


calling 

```
cp=ProxyCuds(lc) 
```
where `lc` is a local CUDS instance, and `cp` is a cuds proxy, means that we take the session lc is belonging to, and create a cp.

This is engagged automatically when adding a cuds to a session, in other words, normally a user should not call this method directly. 

In future versions, the proxy cuds would become a private or hidden class of session. 


