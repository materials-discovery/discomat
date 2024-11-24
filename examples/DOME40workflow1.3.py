from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis, gvis2
from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.plugins.sparql import prepareQuery
from dataclasses import dataclass
from discomat.ontology.namespaces import CUDS, MIO

# Define Namespace
PROV = Namespace("http://www.w3.org/ns/prov#")
DOME40 = Namespace("https://nextgen.dome40.io/")
ACTIVITY = Namespace("https://nextgen.dome40.io/activity/")
USER = Namespace("http://nextgen.dome40.io/user/")
SHOWCASE = Namespace("https://nextgen.dome40.io/showcase/")

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
    user = Cuds(ontology_type=PROV.Agent, label=user_data.name[:20], description=f"User with email {user_data.email}")
    user.add(MIO.hasName, user_data.name)
    user.add(MIO.hasEmail, user_data.email)
    all_cuds.append(user)
    user_entities[user_data.name] = user

# David was associated with Search
search_activity = Cuds(ontology_type=ACTIVITY.Search, label="Search")
search_activity.add(PROV.wasAssociatedWith, user_entities["David"])
all_cuds.append(search_activity)

# Search used Connector, generated Search Record, hasKey Vehicle, used Dataset1, generated Access Request
connector = Cuds(ontology_type=DOME40.Connector, label="Connector")
search_record = Cuds(ontology_type=DOME40.SearchRecord, label="Search Record")
vehicle = Cuds(ontology_type=DOME40.Vehicle, label="Vehicle")
dataset1 = Cuds(ontology_type=DOME40.DataSet, label="DataSet1")
access_request = Cuds(ontology_type=ACTIVITY.AccessRequest, label="Access Request")
search_activity.add(PROV.used, connector)
search_activity.add(PROV.generated, search_record)
search_activity.add(DOME40.hasKey, vehicle)
search_activity.add(PROV.used, dataset1)
search_activity.add(PROV.generated, access_request)
all_cuds.extend([connector, search_record, vehicle, dataset1, access_request])

# Marie was associated with Upload
upload_activity = Cuds(ontology_type=ACTIVITY.Upload, label="Marie Upload")
upload_activity.add(PROV.wasAssociatedWith, user_entities["Marie"])
all_cuds.append(upload_activity)

# Upload generated Upload Record and Dataset2
upload_record = Cuds(ontology_type=DOME40.UploadRecord, label="Upload Record")
dataset2 = Cuds(ontology_type=DOME40.DataSet, label="DataSet2")
upload_activity.add(PROV.generated, upload_record)
upload_activity.add(PROV.generated, dataset2)
all_cuds.extend([upload_record, dataset2])

# Connector used External Platform
external_platform = Cuds(ontology_type=DOME40.ExternalPlatform, label="External Platform")
connector.add(PROV.used, external_platform)
all_cuds.append(external_platform)

# AccessRequest used Dataset1
access_request.add(PROV.used, dataset1)

# ClearingHouseService generated TransactionRecord, generated Contract
clearing_service = Cuds(ontology_type=DOME40.ClearingService, label="ClearingHouseService")
transaction_record_access = Cuds(ontology_type=DOME40.TransactionRecord, label="Transaction Record")
contract = Cuds(ontology_type=DOME40.Contract, label="Contract")
clearing_service.add(PROV.generated, transaction_record_access)
clearing_service.add(PROV.generated, contract)
all_cuds.extend([clearing_service, transaction_record_access, contract])

# Contract has NDA, duration, access, generated Payment, isDerivedFrom AccessGranted
nda = Cuds(ontology_type=DOME40.NDA, label="NDA")
duration = Cuds(ontology_type=DOME40.Duration, label="Duration")
access = Cuds(ontology_type=DOME40.Access, label="Access")
payment = Cuds(ontology_type=DOME40.Payment, label="Payment")
contract.add(DOME40.has, nda)
contract.add(DOME40.has, duration)
contract.add(DOME40.has, access)
contract.add(PROV.generated, payment)
all_cuds.extend([nda, duration, access, payment])

# Payment hasPayee DOME (legal person), generated MonetaryTransaction, hasPayer David
legal_person = Cuds(ontology_type=DOME40.LegalPerson, label="DOME")
monetary_transaction = Cuds(ontology_type=DOME40.MonetaryTransaction, label="Monetary Transaction")
payment.add(DOME40.hasPayee, legal_person)
payment.add(PROV.generated, monetary_transaction)
payment.add(DOME40.hasPayer, user_entities["David"])
all_cuds.extend([legal_person, monetary_transaction])

# MonetaryTransaction enables AccessGranted
access_granted = Cuds(ontology_type=ACTIVITY.AccessGranted, label="Access Granted")
monetary_transaction.add(DOME40.enables, access_granted)
all_cuds.append(access_granted)

# AccessGranted used Dataset1, was associated with David
access_granted.add(PROV.used, dataset1)
access_granted.add(PROV.wasAssociatedWith, user_entities["David"])

# Adding all CUDS to RDF Graph
cuds_graph = Cuds()

# Create RDF Graph and add Triples
gall = Graph()
gall.bind("MIO", MIO)
gall.bind("CUDS", CUDS)

# Adding triples from CUDS to RDF Graph
for cuds_instance in all_cuds:
    for s, p, o in cuds_instance.graph:
        gall.add((s, p, o))

gall.serialize(destination="dome40_workflow1.3.ttl")

# Visualize the Graph
gvis2(gall, "dome40_workflow1.3.html")

# Count the number of CUDS instances created
print(f"Total number of CUDS instances created: {len(all_cuds)}")




# Query 1: Retrieve all activities associated with David
query1 = """
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX dome40: <https://nextgen.dome40.io#>
    SELECT ?activity
    WHERE {
        ?activity prov:wasAssociatedWith ?user .
        ?user dome40:hasName ?name .
        FILTER (CONTAINS(lcase(str(?name)), "david"))
    }
"""

qres1 = gall.query(query1)
print("\nActivities associated with David:")
if not qres1:
    print("No activities found for David.")
for row in qres1:
    print(f"- {row.activity}")


# Query 2: Check if David is associated with any activity
query2 = """
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX dome40: <https://nextgen.dome40.io#>
    ASK {
        ?activity prov:wasAssociatedWith ?user .
        ?user dome40:hasName "David" .
    }
"""

qres2 = gall.query(query2)
print(f"Is David associated with any activity? {qres2.askAnswer}")

# Query 3: Count the number of activities each user is associated with
query3 = """
    PREFIX prov: <http://www.w3.org/ns/prov#>
    SELECT ?user (COUNT(?activity) AS ?activityCount)
    WHERE {
        ?activity prov:wasAssociatedWith ?user .
    }
    GROUP BY ?user
"""

qres3 = gall.query(query3)
print("Number of activities each user is associated with:")
for row in qres3:
    print(f"- User: {row.user}, Activities: {row.activityCount}")

iii = row.user

query_full = f"""
PREFIX mio: <http://www.ddmd.io/mio#>
SELECT DISTINCT ?s ?p ?o
WHERE {{
  {{
    <{iii}> ?p ?o .  # Outgoing triples
  }}
  UNION
  {{
    ?s ?p <{iii}> .  # Incoming triples
  }}
    FILTER(?p = mio:hasName)

}}
"""
res3_5=gall.query(query_full)
for r in res3_5:
    print("row", r)


# query4="""
# PREFIX prov: <http://www.w3.org/ns/prov#>
# PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# PREFIX miodome: <http://www.ddmd.io/mio#>
# PREFIX dome: <https://nextgen.dome40.io/>
#
# SELECT DISTINCT ?activity
# WHERE {
#   # Find all activities or instances of subclasses of prov:Activity
#   ?activity a ?activityType .
#   ?activityType rdfs:subClassOf* dome:Search .
#
#   # Ensure the activity is associated with a user
#   ?activity prov:wasAssociatedWith ?user .
#
#   # Ensure the user has the name "David"
#   ?user miodome:hasName "David" .
# }
#
# """
query4="""
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dome: <https://nextgen.dome40.io/>

SELECT  ?activity
WHERE {
  # Find all instances of prov:Activity or its subclasses
  ?activity a ?activityType .
  ?activityType rdfs:subClassOf* dome:Search .
}
"""
qres4 = gall.query(query4)
print("query 4")
for row in qres4:
    print(f"- User: {row}")

