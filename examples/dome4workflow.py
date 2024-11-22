from orca.guilabels import ACTIVATE

from discomat.cuds.cuds import Cuds
from discomat.visualisation.cuds_vis import gvis, gvis2
from rdflib  import Graph, Namespace, RDF, URIRef
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
    DomeUser("John Doe", "john.doe@example.com"),
]

# List all CUDS
all_cuds = []

# Create User Entities and Registration Workflow
for user_data in users_data:
    # Create User Entity
    user = Cuds(ontology_type=PROV.Agent, label=user_data.name, description=f"this is a user wih email={user_data.email}")
    user.add(MIO.hasName, user_data.name)
    user.add(MIO.hasEmail, user_data.email)
    all_cuds.append(user)

    # User Registration Process
    register_activity = Cuds(ontology_type=ACTIVITY.Register, label="User Registration")
    register_activity.add(PROV.startedAtTime, "2024-11-21T09:00:00")
    register_activity.add(PROV.wasAssociatedWith, user)
    all_cuds.append(register_activity)


    # Transaction Record for Registration
    transaction_record = Cuds(ontology_type=DOME40.TransactionRecord, label="Registration Record")
    register_activity.add(PROV.generated, transaction_record)
    all_cuds.append(transaction_record)

    # User Login Activity
    login_activity = Cuds(ontology_type=ACTIVITY.Login, label="User Login")
    login_activity.add(PROV.startedAtTime, "2024-11-21T10:00:00")
    login_activity.add(PROV.wasAssociatedWith, user)
    all_cuds.append(login_activity)


    # Create Showcase Visit Activity
    showcase = Cuds(ontology_type=SHOWCASE.Showcase, label="Showcase1",
                    description="Showcase about ship positioning.")
    all_cuds.append(showcase)

    visit_activity = Cuds(ontology_type=ACTIVITY.Visit, label="Visit Showcase1")
    visit_activity.add(PROV.startedAtTime, "2024-11-21T10:10:00")
    visit_activity.add(PROV.wasAssociatedWith, user)
    visit_activity.add(PROV.used, showcase)
    all_cuds.append(visit_activity)


    # Data Download Request
    access_request = Cuds(ontology_type=ACTIVITY.AccessRequest, label="Access Request")
    access_request.add(PROV.startedAtTime, "2024-11-21T10:20:00")
    access_request.add(PROV.wasAssociatedWith, user)
    access_request.add(PROV.used, showcase)
    all_cuds.append(access_request)

    # Clearing Service Response and Access Granted
    clearing_service = Cuds(ontology_type=DOME40.ClearingService, label="Clearing Service")
    all_cuds.append(clearing_service)

    access_granted = Cuds(ontology_type=ACTIVITY.AccessGranted, label="Access Granted")
    access_granted.add(PROV.startedAtTime, "2024-11-21T10:30:00")
    access_granted.add(PROV.wasInformedBy, clearing_service)
    access_granted.add(PROV.wasAssociatedWith, user)
    access_granted.add(PROV.used, showcase)
    all_cuds.append(access_granted)

    # Transaction Record for Access Granted
    download_transaction_record = Cuds(ontology_type=DOME40.TransactionRecord, label="Download Record")
    access_granted.add(PROV.generated, download_transaction_record)
    all_cuds.append(download_transaction_record)

# Create RDF Graph and add Triples
gall = Graph()
# gall.parse("/home/qihanhu/Downloads/provenance_clearing_4.1.ttl", format="ttl")

gall.bind("MIO", MIO)
gall.bind("CUDS", CUDS)

# Adding triples from CUDS to RDF Graph
for cuds_instance in all_cuds:
    for s, p, o in cuds_instance.graph:
        gall.add((s, p, o))


gall.serialize(destination="dome40_workflow.ttl")

# Visualize the Graph
gvis2(gall, "dome40_workflow.html")


# Count the number of cuds
print(f"Total number of CUDS instances created: {len(all_cuds)}")