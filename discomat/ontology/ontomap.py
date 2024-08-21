from discomat.ontology.namespaces import CUDS

"""
ideally we would have an automatic way to get from python attribute/property to ontology

example: CUDS.description could be 

c.cuds.description 
c.rdfs.class --> RDFS.Class etc 
here is an example:


"""
ONTOMAP = {
    'uuid': CUDS.uuid,
    'description': CUDS.description,
    'pid': CUDS.PID,
    'label': CUDS.label,
    'create_time': CUDS.CreationTime,

    # Add more mappings as needed
}
