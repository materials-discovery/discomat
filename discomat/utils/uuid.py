import re
def uuid_from_string(s: str=None, length: int=None):
    """

    scan string, identify a UUID part and either return it in whole, or the last length chars.
    """

    # Regular expression pattern for UUID
    #uuid_pattern = re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')
    uuid_pattern = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')

    # Search for UUID in the string
    match = uuid_pattern.search(s)

    if match:
        # Extract the UUID
        uuid=match.group(0)
        return  uuid if length is None else  uuid[-5:]
    else:
        return None