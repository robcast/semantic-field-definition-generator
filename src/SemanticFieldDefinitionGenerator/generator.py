import copy
import yaml
import logging
from pathlib import Path
from pybars import Compiler

__version__ = '1.3'

UNIVERSAL = 0
RESEARCHSPACE = 1
METAPHACTS = 2
JSON = 3
INLINE = 4

def loadSourceFromFile(file):
    try:
        p = Path(file)
        if p.is_dir():
            fields = []
            prefix = None
            for fn in p.glob('*.yml'):
                logging.debug(f"reading yaml file {fn}")
                with open (fn, 'r') as f:
                    new_source = yaml.safe_load(f.read())
                    fields.extend(new_source['fields'])
                    new_prefix = new_source['prefix']
                    if new_prefix:
                        if new_prefix != prefix:
                            if prefix is not None:
                                raise Exception(f"YAML files have different prefixes: {prefix} vs {new_prefix}")
                            else:
                                prefix = new_prefix
            
            source = {'fields': fields}
            if prefix:
                source['prefix'] = prefix
            return source
    
        else:
            with open (file, 'r') as f:
                source = yaml.safe_load(f.read())
                return source

    except Exception as e:
        raise Exception(f"Could not read {file}: {e}")

def _checkSource(source):
    # make sure some attributes are lists
    for field in source['fields']:
        for att in ['domain', 'range', 'defaultValue']:
            if att in field and not isinstance(field[att], list):
                logging.debug(f"Wrapping single value in Field attribute '{att}' in list.")
                field[att] = [field[att]]

    return source

def generate(source, output=UNIVERSAL, splitFields=False, add_ns_prefix=None):
    if output == METAPHACTS:
        templateFile = Path(__file__).parent / './templates/metaphacts.handlebars'
    elif output == RESEARCHSPACE:
        templateFile = Path(__file__).parent / './templates/researchspace.handlebars'
    elif output == JSON:
        templateFile = Path(__file__).parent / './templates/json.handlebars'
    elif output == INLINE:
        templateFile = Path(__file__).parent / './templates/inline.handlebars'
    else:
        templateFile = Path(__file__).parent / './templates/universal.handlebars'
    
    with templateFile.open() as f:
        templateSource = f.read()

    processedSource = _checkSource(copy.deepcopy(source))
        
    if output == JSON or output == INLINE:
        for i in range(len(source['fields'])):
            if 'queries' in source['fields'][i]:
                for queryIndex, query in enumerate(source['fields'][i]['queries']):
                    for queryType in query.keys():
                        escapedQuery = source['fields'][i]['queries'][queryIndex][queryType].replace('"','\\"')
                        processedSource['fields'][i]['queries'][queryIndex][queryType] = escapedQuery
            if 'treePatterns' in source['fields'][i]:
                for key, value in source['fields'][i]['treePatterns'].items():
                    escapedValue = value.replace('"','\\"')
                    processedSource['fields'][i]['treePatterns'][key] = escapedValue

    compiler = Compiler()
    template = compiler.compile(templateSource)
    try:
        if splitFields:
            outputs = []
            prefix = processedSource.get('prefix', '')
            for field in processedSource['fields']:
                # create new source for each field
                fieldId = field['id']
                fieldSource = {'prefix': prefix, 'fields': [field], 'extra_ns': add_ns_prefix}
                fieldOutput = template(fieldSource)
                # add id,output pair to list
                outputs.append((prefix + fieldId, fieldOutput))
                
            return outputs

        else:
            processedSource['extra_ns'] = add_ns_prefix
            output = template(processedSource)
            return output
    except:
        raise Exception("Could not generate definitions")

