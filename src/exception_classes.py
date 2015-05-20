# Self-defined exceptions
class NoConceptException(Exception):
    # In case the concept couldn't be found
    pass

class NoPropertyException(Exception):
    # In case the property couldn't be found
    pass


class NoPropertyRelationException(Exception):
    # In case there is no relation found for the property
    pass


class NoResultException(Exception):
    # In case there are no results found
    pass