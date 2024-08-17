from typing import Union
from rdflib import URIRef

from rdflib import URIRef
from typing import Union
import re


def to_iri(e: Union[str, URIRef]):
    try:
        # first, we assume it is a CUds (we do not want to import it to avoid circular import).
        e = to_iri(e.iri)
    except AttributeError:
        if isinstance(e, str):
            e = URIRef(e)
        elif isinstance(e, URIRef):
            pass
        else:
            raise TypeError(f"in to_iri: Wrong, unsupported type {type(e)}")
    return e


def uuid_from_string(s: str = None, length: int = None):
    """

    scan string, identify a UUID part and either return it in whole, or the last length chars.
    """

    # Regular expression pattern for UUID
    # uuid_pattern = re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')
    uuid_pattern = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')

    # Search for UUID in the string
    match = uuid_pattern.search(s)

    if match:
        # Extract the UUID
        uuid = match.group(0)
        return uuid if length is None else uuid[-5:]
    else:
        return None


def extract_fragment(iri):  # we have this in so many versions and incarnations, should fixme move to utils
    """extract the fragment or the last part of an IRI."""
    return iri.split('#')[-1].split('/')[-1]
