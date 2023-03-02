import copy
import yaml
import logging
from pathlib import Path
from pybars import Compiler

__version__ = '1.2'

UNIVERSAL = 0
RESEARCHSPACE = 1
METAPHACTS = 2
JSON = 3
INLINE = 4

def loadSourceFromFile(file):
    try:
        with open (file, 'r') as f:
            source = yaml.safe_load(f.read())
            return source
    except:
        raise Exception("Could not read " + file)

def _checkSource(source):
    # make sure some attributes are not lists
    for field in source['fields']:
        for att in ['domain', 'range', 'defaultValue']:
            if att in field and isinstance(field[att], list):
                logging.warning(f"Multiple values in Field attribute '{att}' not supported! Using only first value.")
                field[att] = field[att][0]

    return source

def generate(source, output=UNIVERSAL, splitFields=False):
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
                fieldSource = {'prefix': prefix, 'fields': [field]}
                fieldOutput = template(fieldSource)
                # add id,output pair to list
                outputs.append((prefix + fieldId, fieldOutput))
                
            return outputs

        else:
            output = template(processedSource)
            return output
    except:
        raise Exception("Could not generate definitions")

