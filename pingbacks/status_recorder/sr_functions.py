import json
import datetime


def clear_entity_state_store(entity_state_store):
    with open(entity_state_store, 'w') as f:
        f.write(json.dumps([], indent=4, sort_keys=True))


def create_entity_status(entity_state_store, entity_uri):
    new_entity_status = {
        'uri': entity_uri,
        'strategies': [0],
        'first_attempt': datetime.datetime.now().isoformat(),
        'last_attempt': None,
        'dereferencable': False,
        'rdf_metadata': False,
        'pingback_endpoints': None,
        'provenance_endpoints': None,
        'pingback_received': False,
        'provenance_bundle_received': False
    }
    with open(entity_state_store, 'r') as f:
        entities = json.load(f)
    entities.append(new_entity_status)
    with open(entity_state_store, 'w') as f:
        f.write(json.dumps(entities, indent=4, sort_keys=True))

    return new_entity_status


def load_entity_status(entity_state_store, entity_uri):
    # check for existing entities with this URI
    with open(entity_state_store, 'r') as f:
        entities = json.load(f)

    for entity in entities:
        if entity['uri'] == entity_uri:
            return entity

    # entity not in store so create a new one, write to store and return
    return create_entity_status(entity_state_store, entity_uri)


def update_entity_status(entity_state_store, entity_uri, updated_fields):
    with open(entity_state_store, 'r') as f:
        entities = json.load(f)

    for entity in entities:
        if entity['uri'] == entity_uri:
            for field in updated_fields.iteritems():
                entity[field[0]] = field[1]

    with open(entity_state_store, 'w') as f:
        f.write(json.dumps(entities, indent=4, sort_keys=True))

    return True