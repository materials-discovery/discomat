# CUDS documentation

this is a prelimenary documentaiont

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
- session: the session it belongs to. 

Note a cuds, if it belongs to a session, is managed by the session and is a proxy cuds. 

There are also some utility methods, including, 

- print_graph
- serilise 


The main methods for cuds, besides init of course are: 

- `add`: add a predicate, relation `rel` to a object `obj`: `c.add(rel, obj)`
- remove: the opposite of ass 
- iter: iterate over relations

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

The ontology_type of a Proxy Cuds is a `CUDS.CudsProxy`

All methods and properties or attributes on a CUDS proxy are delegated to the session's specific proxy handler, check [session.py - session handler](./session.py)


The engine in turn, delegates the action to specific enginer methods, for example, the methods add, when called on a cuds proxy, is translated to a call to seld.proxy_add by the proxy handler. The proxy_add method does some checks and assignments, and then delegates the call to teh engine add_tiple method. Shee workflow below: 

```
graph LR
    add[Square Rect] -- call session --> proxy_handler((Circle))
    proxy_handler --engine --> add_triple{Rhombus}
```
