- creating a cuds from within a session
currently a cuds is created when adding it to a session, but how to create one starting from a session? 

    - solution 1: 
 

    simply create method that first uses Cuds to create the Cuds, then add
it to the session. This method however, will need to have a different name for
this yet again, or some sort of a catch method to know whether the new cUDS is
a proxy or not. 

    - solution 2: 

        basically same as 1, except the user has to create teh cuds and then add it to the session, i.e., no cuds is created directly or implicitly in a sesson. A Cuds is always added to a session. 
