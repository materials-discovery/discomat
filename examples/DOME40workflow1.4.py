from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis, gvis2
from rdflib import Graph, Namespace, RDF, URIRef
from rdflib.plugins.sparql import prepareQuery
from dataclasses import dataclass
from discomat.ontology.namespaces import CUDS, MIO


# Define Namespace
PROV = Namespace("http://www.w3.org/ns/prov#")
PC = Namespace("http://dome40.eu/semantics/pc#")
DOME = Namespace("http://dome40.eu/semantics/dome4.0_core#")
ADE = Namespace("http://dome40.eu/semantics/reasoned/ade_reasoned#")
PL = Namespace("https://dome40.eu/semantics/scenario/platforms#")
MIO = Namespace("http//materials-discovery.org/semantics/mio#")


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

# Add DOME as an Agent
dome_entity = Cuds(ontology_type=PROV.Agent, label="DOME Entity")
all_cuds.append(dome_entity)

# Create Service as a superclass
service_class = Cuds(ontology_type=DOME.Service, label="Service Class")
all_cuds.append(service_class)

# Create Search as a subclass of Service
search_class = Cuds(ontology_type=DOME.Search, label="Search Class")
search_class.add(PROV.subClassOf, service_class)  # Define Search as a subclass of Service
all_cuds.append(search_class)

# Create ClearingService as another subclass of Service
clearing_service_class = Cuds(ontology_type=DOME.ClearingService, label="ClearingServiceClass")
clearing_service_class.add(PROV.subClassOf, service_class)  # Define Clearing Service as a subclass of Service
all_cuds.append(clearing_service_class)

# Create Dataset Instances
dataset1 = Cuds(ontology_type=PC.DataSet, label="Dataset 1")
dataset2 = Cuds(ontology_type=PC.DataSet, label="Dataset 2")
all_cuds.extend([dataset1, dataset2])

# Create Connector and External Platform
connector = Cuds(ontology_type=PL.Connector, label="Search Connector")
external_platform = Cuds(ontology_type=PL.ExternalPlatform, label="External Platform")
connector.add(PROV.used, external_platform)
all_cuds.extend([connector, external_platform])

# David associated with Search Activity
search_activity = Cuds(ontology_type=ADE.SearchActivity, label="DavidSearchActivity")
search_activity.add(PROV.wasAssociatedWith, user_entities["David"])
search_activity.add(PROV.subClassOf, search_class)  # Link Search Activity to Search Class
search_activity.add(PROV.used, connector)
all_cuds.append(search_activity)

# Search generated Search Record
search_record = Cuds(ontology_type=PC.SearchRecord, label="SearchRecforVehicle")
search_record.add(PC.keyword, Literal("Vehicle"))  # Vehicle as a data property
search_record.add(PROV.wasGeneratedBy, search_activity)
search_record.add(PROV.wasAssociatedWith, user_entities["David"])
search_record.add(PC.result, dataset1)  # Link to search result
all_cuds.append(search_record)

# Create Upload Service as a subclass of Service
upload_service = Cuds(ontology_type=DOME.Upload, label="Upload Class")
upload_service.add(PROV.subClassOf, service_class)  # Define Upload as a subclass of Service
all_cuds.append(upload_service)

# Marie associated with Upload Activity
upload_activity = Cuds(ontology_type=ADE.UploadActivity, label="MarieUploadActivity")
upload_activity.add(PROV.wasAssociatedWith, user_entities["Marie"])
upload_activity.add(PROV.subClassOf, upload_service)  # Link Upload Activity to Upload Service
upload_record = Cuds(ontology_type=PC.UploadRecord, label="Upload Record")
upload_activity.add(PROV.generated, upload_record)
upload_activity.add(PROV.generated, dataset2)  # Dataset2 from upload
all_cuds.extend([upload_activity, upload_record])

# Access Request using Clearing Service
access_request = Cuds(ontology_type=ADE.AccessRequestActivity, label="AccessReqActivity")
access_request.add(PROV.used, clearing_service_class)
access_request.add(PROV.used, dataset1)
all_cuds.append(access_request)

# Contract, Payment, and Transaction Record
contract = Cuds(ontology_type=PC.Contract, label="ContractDavidandDOME")
nda = Cuds(ontology_type=PC.NDA, label="NDA")
duration = Cuds(ontology_type=PC.Duration, label="Access Duration")
access = Cuds(ontology_type=PC.Access, label="Access to Dataset")
contract.add(PC.has, nda)
contract.add(PC.has, duration)
contract.add(PC.has, access)

payment = Cuds(ontology_type=PC.Payment, label="Payment by David")
contract.add(PROV.generated, payment)

transaction_record = Cuds(ontology_type=PC.TransactionRecord, label="Transaction Record")
transaction_record.add(PROV.wasGeneratedBy, payment)
transaction_record.add(PC.relatedContract, contract)
payment.add(PC.hasPayer, user_entities["David"])
payment.add(PROV.wasAssociatedWith, dome_entity)
payment.add(PC.grantsAccessTo, dataset1)
all_cuds.extend([contract, nda, duration, access, payment, transaction_record])

# Monetary Transaction and Access Granted
monetary_transaction = Cuds(ontology_type=PC.MonetaryTransaction, label="Monetary Transaction")
monetary_transaction.add(PC.enables, access_request)
payment.add(PROV.generated, monetary_transaction)

access_granted = Cuds(ontology_type=ADE.AccessGranted, label="Access Granted")
access_granted.add(PROV.used, dataset1)
access_granted.add(PROV.wasAssociatedWith, user_entities["David"])
monetary_transaction.add(PC.enables, access_granted)
all_cuds.extend([monetary_transaction, access_granted])

# Serialize and visualize
gall = Graph()
gall.bind("MIO", MIO)
gall.bind("DOME", DOME)
gall.bind("PC", PC)
gall.bind("ADE", ADE)
gall.bind("PL", PL)

for cuds_instance in all_cuds:
    for s, p, o in cuds_instance.graph:
        gall.add((s, p, o))

gall.serialize(destination="dome40_workflow1.3.ttl")

# Visualize the graph using gvis2
gvis2(gall, "DOME40Workflow1.4.html")

print(f"Total number of CUDS instances created: {len(all_cuds)}")







