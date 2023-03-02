from rdflib import Dataset, URIRef
from rdflib.namespace import Namespace, NamespaceManager
from rdflib.plugins.stores.sparqlstore import SPARQLStore
from pathlib import Path
import yaml
import logging

__version__ = '1.2'

# flavors
RESEARCHSPACE = 1
METAPHACTS = 2

##
## namespaces
##
rdfNs = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
rdfsNs = Namespace('http://www.w3.org/2000/01/rdf-schema#')
ldpNs = Namespace('http://www.w3.org/ns/ldp#')
xsdNs = Namespace('http://www.w3.org/2001/XMLSchema#')
provNs = Namespace('http://www.w3.org/ns/prov#')
spNs = Namespace('http://spinrdf.org/sp#')
crmNs = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
rsFieldDefNs = Namespace('http://www.researchspace.org/resource/system/fields/')
rsFieldConNs = Namespace('http://www.researchspace.org/resource/system/')
mpFieldDefNs = Namespace('http://www.metaphacts.com/ontology/fields#')
mpFieldConNs = Namespace('http://www.metaphacts.com/ontologies/platform#')
# used prefixes, add chosen flavor of field*NS later
nsPrefixes = {'rdfs': rdfsNs, 'ldp': ldpNs, 'sp': spNs, 'crm': crmNs}

# separate NamespaceManager for normalizations
# rdflib BUG: queries may break when you use the store's manager :-(
nsManager = NamespaceManager(Dataset())
for pref, ns in nsPrefixes.items():
    nsManager.bind(pref, ns)


def uristr(node):
    """return string form of node, normalizing URIs.""" 
    if isinstance(node, URIRef):
        # normalize to N3 form including namespaces
        return node.n3(nsManager)
        
    return str(node)

def open_sparql_store(endpoint, repository='assets', auth_user='admin', auth_pass='admin'):
    """open connection to SPARQL store.
    endpoint: SPARQL endpoint URI
    repository: RS/MP repository parameter
    auth: (username, password) tuple
    returns rdflib Dataset.
    """
    logging.info(f"connecting to SPARQLStore at {endpoint} (repository={repository} user={auth_user} pass={auth_pass})")
    # configure connection to SPARQL endpoint
    if repository:
        params={'repository': repository}
    else:
        params=None
        
    if auth_user:
        auth = (auth_user, auth_pass)
    else:
        auth = None
        
    _store = SPARQLStore(query_endpoint=endpoint, params=params, auth=auth)
    # instantiate Dataset
    store = Dataset(_store)
    return store

def read_trig_store(pathname):
    """create store from trig file(s).
    """
    logging.info(f"creating trig file store from {pathname}")
    store = Dataset()
    p = Path(pathname)
    if p.is_dir():
        for f in p.glob('*.trig'):
            logging.debug(f"reading trig file {f}")
            store.parse(f, format='trig')

    else:
        logging.debug(f"reading trig file {p}")
        store.parse(p, format='trig')

    return store

def read_fields(store, flavor, field_id_prefix=None):
    """read all fields of given flavor from store.
    returns list of fields as dicts.
    """
    fields = []
    prefixes = nsPrefixes
    if flavor == METAPHACTS:
        prefixes['fielddef'] = mpFieldDefNs
        prefixes['fieldcon'] = mpFieldConNs
    else:
        prefixes['fielddef'] = rsFieldDefNs
        prefixes['fieldcon'] = rsFieldConNs

    query = '''select ?graph ?field
    where {
        graph ?graph {
            fieldcon:fieldDefinitionContainer ldp:contains ?field .
            ?field a fielddef:Field .
        }
    }'''
    logging.debug(f"fields query='{query}'")
    res = store.query(query, initNs=prefixes)
    logging.info(f"found {len(res)} fields (flavor={flavor})")
    for r in res:
        logging.debug(f"field uri={r.field} in graph={r.graph}")
        field_id = str(r.field)
        if field_id_prefix and field_id.startswith(field_id_prefix):
            field_id = field_id[len(field_id_prefix):]
            
        field = read_field(store, r.field, r.graph, field_id, prefixes)
        if field is not None:
            fields.append(field)

        #break # debug
    return fields

def _set_once(items, key, value):
    """set items[key] to value if it doesn't exist, warn if value is different."""
    if key in items:
        if items[key] != value:
            logging.warning(f"Ignoring different value to set! key={key} value={value}")
        
    else:
        items[key] = value
        
    return items

def _set_append(items, key, value):
    """set items[key] to value if it doesn't exist, append to list if value is different."""
    if key in items:
        oldval = items[key]
        if oldval != value:
            # existing value is different
            if isinstance(oldval, list):
                # append to existing list
                oldval.append(value)
            else:
                # create new list
                items[key] = [oldval, value]
        
    else:
        items[key] = value
        
    return items

def read_field(store, field_uri, graph_uri, field_id, prefixes):
    """read the semantic field with URI field_uri in named graph graph_uri from store.
    returns dict of field attributes.
    
    field attributes (see https://documentation.researchspace.org/resource/Help:SemanticForm)
    - id*: Unique identifier of the field definition, in most cases it will be the URI of the field definition
    - label*: A human readable label for the field. Will be used as default label for the input elements within the form.
    - description: A human readable description of the field.
    - categories: An unordered array of category IRIs as additional metadata for improved organisation.
    - domain: Domain restriction on classes this field applicable to.
    - range: Range restriction on allowed classes of objects for the field values.
    - xsdDatatype: A full or prefix XSD URI datatype identifier as specified in RDF 1.1
    - minOccurs: XSD schema min cardinality number of 0:N. 0 for not required. Defaults to 0.
    - maxOccurs: XSD schema max cardinality number of 1:N or unbound for infinite (default).
    - defaultValues: An array of default values (represented as text) assigned to the field if subject doesn't contain a value
    - selectPattern: SPARQL SELECT query string
    - insertPattern*: SPARQL INSERT query string to create new values
    - deletePattern: SPARQL DELETE query string to delete old values (only required if running in SPARQL mode)
    - askPattern: SPARQL ASK query string, parameterized with the current $subject and new $value.
    - autosuggestionPattern: SPARQL SELECT query string for autosuggestion lookups
    - valueSetPattern: SPARQL SELECT query string for populating set choices such as in dropdown
    - treePatterns: SPARQL configuration to select terms from an hierarchical thesaurus.
    """
    query = '''SELECT *
    WHERE {
        GRAPH ?graph {
            ?field rdfs:label ?label .
            OPTIONAL {
                ?field rdfs:comment ?description .
            } OPTIONAL {
                ?field fielddef:domain ?domain .
            } OPTIONAL {
                ?field fielddef:range ?range .
            } OPTIONAL {
                ?field fielddef:xsdDatatype ?datatype . 
            } OPTIONAL {
                ?field fielddef:minOccurs ?minOccurs . 
            } OPTIONAL {
                ?field fielddef:maxOccurs ?maxOccurs . 
            } OPTIONAL {
                ?field fielddef:order ?order .
            } OPTIONAL {
                ?field fielddef:defaultValue ?defaultValue .
            } OPTIONAL {
                ?field fielddef:selectPattern / sp:text ?selectPattern .
            } OPTIONAL {
                ?field fielddef:insertPattern / sp:text ?insertPattern .
            } OPTIONAL {
                ?field fielddef:deletePattern / sp:text ?deletePattern .
            } OPTIONAL {
                ?field fielddef:askPattern / sp:text ?askPattern .
            } OPTIONAL {
                ?field fielddef:autosuggestionPattern / sp:text ?autosuggestionPattern .
            } OPTIONAL {
                ?field fielddef:valueSetPattern / sp:text ?valueSetPattern .
            }
        }
    }'''
    logging.debug(f"field query='{query}' bindings=('field': {field_uri}, 'graph': {graph_uri}) prefixes={prefixes}")
    res = store.query(query, initNs=prefixes, initBindings={'field': field_uri, 'graph': graph_uri})
    if len(res) < 1:
        logging.error(f"Field definition not found for URI={field_uri}")
        return None
    
    field = {
        'id': field_id,
    }
    # loop through possibly multiple attribute values
    for f in res:
        _set_once(field, 'label', str(f.label))
        if f.description:
            _set_once(field, 'description', str(f.description))
        if f.domain:
            _set_append(field, 'domain', uristr(f.domain))
        if f.range:
            _set_append(field, 'range', uristr(f.range))
        if f.datatype:
            _set_once(field, 'datatype', uristr(f.datatype))
        if f.minOccurs:
            _set_once(field, 'minOccurs', str(f.minOccurs))
        if f.maxOccurs:
            _set_once(field, 'maxOccurs', str(f.maxOccurs))
        if f.order:
            _set_once(field, 'order', str(f.order))
        if f.defaultValue:
            _set_append(field, 'defaultValue', str(f.defaultValue))
        
        queries = {}
        if f.selectPattern:
            _set_once(queries, 'select', str(f.selectPattern))
        if f.insertPattern:
            _set_once(queries, 'insert', str(f.insertPattern))
        if f.deletePattern:
            _set_once(queries, 'delete', str(f.deletePattern))
        if f.askPattern:
            _set_once(queries, 'ask', str(f.askPattern))
        if f.autosuggestionPattern:
            _set_once(queries, 'autosuggestion', str(f.autosuggestionPattern))
        if f.valueSetPattern:
            _set_once(queries, 'valueSet', str(f.valueSetPattern))
        
        if queries:
            field['queries'] = [{k: v} for k, v in queries.items()]
    
    return field

def write_fields_yaml(fields, filename, field_id_prefix=None):
    """write all fields to YAML file filename."""
    logging.info(f"writing {len(fields)} fields to YAML file {filename}")
    with open(filename, 'w') as f:
        data = {'fields': fields}
        if field_id_prefix:
            data['prefix'] = field_id_prefix
        
        yaml.dump(data, stream=f)
