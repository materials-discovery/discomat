from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis, gvis2
from rdflib import Graph, Namespace, RDF, URIRef
from dataclasses import dataclass
from discomat.ontology.namespaces import CUDS, MIO

# Define Namespace
PROV = Namespace("http://www.w3.org/ns/prov#")
DOME40 = Namespace("https://nextgen.dome40.io/")
ACTIVITY = Namespace("https://nextgen.dome40.io/activity/")
USER = Namespace("https://nextgen.dome40.io/user/")
SHOWCASE = Namespace("https://nextgen.dome40.io/showcase/")

# Define user data
@dataclass
class DomeUser:
    name: str
    email: str

# User Information
users_data = [
    DomeUser("David", "david@example.com"),
    DomeUser("Mary", "mary@example.com")
]

# List all CUDS
all_cuds = []

# Create User Entities and Registration Workflow
user_entities = {}
for user_data in users_data:
    # Create User Entity if not already created
    user = Cuds(ontology_type=PROV.Agent, label=user_data.name, description=f"this is a user wih email={user_data.email}")
    user.add(MIO.hasName, user_data.name)
    user.add(MIO.hasEmail, user_data.email)
    all_cuds.append(user)
    user_entities[user_data.name] = user

    # User Registration Process
    register_activity = Cuds(ontology_type=ACTIVITY.Register, label=f"{user_data.name} Registration")
    register_activity.add(PROV.startedAtTime, "2024-11-21T09:00:00")
    register_activity.add(PROV.wasAssociatedWith, user)
    all_cuds.append(register_activity)

    # Transaction Record for Registration
    transaction_record = Cuds(ontology_type=DOME40.TransactionRecord, label=f"{user_data.name} RegiRecord")
    register_activity.add(PROV.generated, transaction_record)
    all_cuds.append(transaction_record)

    # User Login Activity
    login_activity = Cuds(ontology_type=ACTIVITY.Login, label=f"{user_data.name} Login")
    login_activity.add(PROV.startedAtTime, "2024-11-21T10:00:00")
    login_activity.add(PROV.wasAssociatedWith, user)
    all_cuds.append(login_activity)

# Create Showcase Visit Activity
showcase = Cuds(ontology_type=SHOWCASE.Showcase, label="Showcase1",
                description="Showcase about ship positioning.")
all_cuds.append(showcase)

# David visits the showcase
visit_activity = Cuds(ontology_type=ACTIVITY.Visit, label="DavidVisitShowcase1")
visit_activity.add(PROV.startedAtTime, "2024-11-21T10:10:00")
visit_activity.add(PROV.wasAssociatedWith, user_entities["David"])  # David visits the showcase
visit_activity.add(PROV.used, showcase)
all_cuds.append(visit_activity)

# Data Download Request by David
access_request = Cuds(ontology_type=ACTIVITY.AccessRequest, label="David Access Request")
access_request.add(PROV.startedAtTime, "2024-11-21T10:20:00")
access_request.add(PROV.wasAssociatedWith, user_entities["David"])  # David
access_request.add(PROV.used, showcase)
all_cuds.append(access_request)

# Clearing Service Response and Access Granted
clearing_service = Cuds(ontology_type=DOME40.ClearingService, label="Clearing Service")
all_cuds.append(clearing_service)

access_granted = Cuds(ontology_type=ACTIVITY.AccessGranted, label="AccessGrantedtoDavid")
access_granted.add(PROV.startedAtTime, "2024-11-21T10:30:00")
access_granted.add(PROV.wasInformedBy, clearing_service)
access_granted.add(PROV.wasAssociatedWith, user_entities["David"])  # David
access_granted.add(PROV.used, showcase)
all_cuds.append(access_granted)

# Transaction Record for Access Granted
download_transaction_record = Cuds(ontology_type=DOME40.TransactionRecord, label="DownloadRecDavid")
access_granted.add(PROV.generated, download_transaction_record)
all_cuds.append(download_transaction_record)

# Adding additional entities and relationships
# Vehicles, Ships, and Contracts
vehicle = Cuds(ontology_type=DOME40.Vehicle, label="Vehicle")
ship1 = Cuds(ontology_type=DOME40.Ship, label="Ship1")
ship2 = Cuds(ontology_type=DOME40.Ship, label="Ship2")
contract = Cuds(ontology_type=DOME40.Contract, label="Contract")
payment = Cuds(ontology_type=DOME40.Payment, label="Payment")
monetary_transaction = Cuds(ontology_type=DOME40.MonetaryTransaction, label="Monetary Transaction")
all_cuds.extend([vehicle, ship1, ship2, contract, payment, monetary_transaction])

# Showcase1 contains Vehicle and Ship
showcase.add(DOME40.contains, vehicle)
showcase.add(DOME40.contains, ship1)
showcase.add(DOME40.contains, ship2)

# Search Activity by David hasKey Vehicle
search_activity = Cuds(ontology_type=ACTIVITY.Search, label="David Search Vehicle")
search_activity.add(DOME40.hasKey, vehicle)
search_activity.add(PROV.wasAssociatedWith, user_entities["David"])  # David
all_cuds.append(search_activity)

# Contract has NDA, duration, access
nda = Cuds(ontology_type=DOME40.NDA, label="NDA")
duration = Cuds(ontology_type=DOME40.Duration, label="duration")
access = Cuds(ontology_type=DOME40.Access, label="access")
contract.add(DOME40.has, nda)
contract.add(DOME40.has, duration)
contract.add(DOME40.has, access)
all_cuds.extend([nda, duration, access])

# Contract generated Payment
contract.add(PROV.generated, payment)

# Payment has Payer and Payee
payer = Cuds(ontology_type=DOME40.Payer, label="Payer")
payee = Cuds(ontology_type=DOME40.Payee, label="Payee")
all_cuds.extend([payer, payee])

# Adding Mary explicitly to ensure existence in user_entities
mary = user_entities.get("Mary")
if not mary:
    mary = Cuds(ontology_type=PROV.Agent, label="Mary", description="this is a user wih email=mary@example.com")
    mary.add(MIO.hasName, "Mary")
    mary.add(MIO.hasEmail, "mary@example.com")
    all_cuds.append(mary)
    user_entities["Mary"] = mary

# Associate Mary with Payee
payee.add(PROV.wasAssociatedWith, user_entities["Mary"])

payment.add(DOME40.has, payer)
payment.add(DOME40.has, payee)

# Payment generated MonetaryTransaction
payment.add(PROV.generated, monetary_transaction)

# MonetaryTransaction enables AccessGranted
monetary_transaction.add(DOME40.enables, access_granted)

# AccessGranted isDerivedFrom Contract
access_granted.add(DOME40.isDerivedFrom, contract)

# Adding Upload Activity for Mary
upload_activity = Cuds(ontology_type=ACTIVITY.Upload, label="Mary Upload")
upload_activity.add(PROV.wasAssociatedWith, user_entities["Mary"])
all_cuds.append(upload_activity)

cuds_graph = Cuds()

# Create RDF Graph and add Triples
gall = Graph()
# gall.parse("/home/qihanhu/Downloads/provenance_clearing_4.1.ttl", format="ttl")

gall.bind("MIO", MIO)
gall.bind("CUDS", CUDS)

# Adding triples from CUDS to RDF Graph, filtering out default entities
for cuds_instance in all_cuds:
    if "default" not in cuds_instance.label.lower():
        for s, p, o in cuds_instance.graph:
            gall.add((s, p, o))

gall.serialize(destination="dome40_workflow1.2.ttl")

# Visualize the Graph
gvis2(gall, "dome40_workflow1.2.html")

# Count the number of cuds
print(f"Total number of CUDS instances created: {len(all_cuds)}")
