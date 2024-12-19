from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis2
import rdflib
from rdflib import Graph, Namespace, Literal
from dataclasses import dataclass


PROV = Namespace("http://www.w3.org/ns/prov#")
PC = Namespace("http://dome40.eu/semantics/pc#")
DOME = Namespace("http://dome40.eu/semantics/dome4.0_core#")
ADE = Namespace("http://dome40.eu/semantics/reasoned/ade_reasoned#")
PL = Namespace("https://dome40.eu/semantics/scenario/platforms#")
MIO = Namespace("http://materials-discovery.org/semantics/mio#")


# Define user data
@dataclass
class DomeUser:
    name: str
    email: str

# User Information
users_data = [
    DomeUser("David", "david@example.com"),
    DomeUser("Marie", "marie@example.com")
]

# List all CUDS
all_cuds = []

# Create User Entities
user_entities = {}
for user_data in users_data:
    user = Cuds(ontology_type=PROV.Agent,description=f"User with email {user_data.email}")
    user.add(MIO.hasName, user_data.name)
    user.add(MIO.hasEmail, user_data.email)
    all_cuds.append(user)
    user_entities[user_data.name] = user

# Create Dataset Instances
dataset1 = Cuds(ontology_type=PC.DataSet1)
dataset2 = Cuds(ontology_type=PC.DataSet2)
all_cuds.extend([dataset1, dataset2])

# Create Connector and External Platform
connector = Cuds(ontology_type=PL.Connector)
external_platform = Cuds(ontology_type=PL.ExternalPlatform)
connector.add(PROV.used, external_platform)
all_cuds.extend([connector, external_platform])

# David associated with Search Activity
search_activity = Cuds(ontology_type=ADE.SearchActivity)
search_activity.add(PROV.subClassOf, DOME.Search)
search_activity.add(PROV.wasAssociatedWith, user_entities["David"])
search_activity.add(PROV.used, connector)
all_cuds.append(search_activity)

# Search generated Search Record
search_record = Cuds(ontology_type=PC.SearchRecord)
search_record.add(PC.keyword, Literal("Vehicle"))
search_record.add(PROV.wasGeneratedBy, search_activity)
search_record.add(PROV.wasAssociatedWith, user_entities["David"])
search_record.add(PC.result, dataset1)
all_cuds.append(search_record)

# Upload Activity and Upload Record
upload_activity = Cuds(ontology_type=ADE.UploadActivity)
upload_activity.add(PROV.wasAssociatedWith, user_entities["Marie"])
upload_record = Cuds(ontology_type=PC.UploadRecord)
upload_activity.add(PROV.generated, upload_record)
upload_activity.add(PROV.generated, dataset2)
all_cuds.extend([upload_activity, upload_record])

# Access Request
access_request = Cuds(ontology_type=ADE.AccessRequestActivity)
access_request.add(PROV.used, dataset1)
access_request.add(PROV.used, DOME.ClearingHouse)
all_cuds.append(access_request)

# Contract, Payment, and Transaction Record
contract = Cuds(ontology_type=PC.Contract)
nda = Cuds(ontology_type=PC.NDA)
duration = Cuds(ontology_type=PC.Duration)
access = Cuds(ontology_type=PC.Access)
contract.add(PC.has, nda)
contract.add(PC.has, duration)
contract.add(PC.has, access)

payment = Cuds(ontology_type=PC.Payment)
contract.add(PROV.generated, payment)

transaction_record = Cuds(ontology_type=PC.TransactionRecord)
transaction_record.add(PROV.wasGeneratedBy, payment)
transaction_record.add(PC.relatedContract, contract)
payment.add(PC.hasPayer, user_entities["David"])
payment.add(PC.grantsAccessTo, dataset1)
all_cuds.extend([contract, nda, duration, access, payment, transaction_record])

# Monetary Transaction and Access Granted
monetary_transaction = Cuds(ontology_type=PC.MonetaryTransaction)
monetary_transaction.add(PC.enables, access_request)
payment.add(PROV.generated, monetary_transaction)

access_granted = Cuds(ontology_type=ADE.AccessGranted)
access_granted.add(PROV.used, dataset1)
access_granted.add(PROV.wasAssociatedWith, user_entities["David"])
monetary_transaction.add(PC.enables, access_granted)
all_cuds.extend([monetary_transaction, access_granted])

# Serialize and visualize the graph
gall = Graph()
gall.bind("MIO", MIO)
gall.bind("DOME", DOME)
gall.bind("PC", PC)
gall.bind("ADE", ADE)
gall.bind("PL", PL)

for cuds_instance in all_cuds:
    for s, p, o in cuds_instance.graph:
        gall.add((s, p, o))

gall.serialize(destination="Dome40_workflow1.5.ttl")

# Visualize the graph using gvis2
gvis2(gall, "Dome40_workflow1.5.html")

print(f"Total number of CUDS instances created: {len(all_cuds)}")




# for s, p, o in graph:
#    print(f"Subject: {s}, Predicate: {p}, Object: {o}")
#
# graph = rdflib.Graph()
#
# graph.parse("Dome40_workflow1.5.ttl", format="turtle")
#
# # search for this
# david_name = rdflib.Literal("David")
#
# user_in_KB = False
#
# # Search for the subject where 'hasName' is 'David'
# for s, p, o in graph.triples((None, rdflib.URIRef("http://materials-discovery.org/semantics/mio#hasName"), david_name)):
#     print(f"found: {s}, {p}, {o}")
#
#     user_in_KB = True
#
#
# if user_in_KB:
#     print(f"User with name 'David' is in the knowledge base.")
# else:
#     print(f"User with name 'David' is not found in the knowledge base.")





#Query
from SPARQLWrapper import SPARQLWrapper, JSON

# Fuseki endpoint URL
sparql_endpoint = ""


sparql = SPARQLWrapper(sparql_endpoint)


query = """
PREFIX mio: <http://materials-discovery.org/semantics/mio#>

SELECT ?subject WHERE {
  ?subject mio:hasName "David" .
}
"""


sparql.setQuery(query)
sparql.setReturnFormat(JSON)


results = sparql.query().convert()


if results["results"]["bindings"]:
    for result in results["results"]["bindings"]:
        print(f"Found subject: {result['subject']['value']}")
else:
    print("User with name 'David' is not found in the knowledge base.")
