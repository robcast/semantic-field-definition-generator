# Semantic Field Definition Generator

A generator for Metaphacts/ResearchSpace semantic field definitions. Based on https://github.com/swiss-art-research-net/sari-field-definitions-generator

## Installation

install using pip

```sh
pip install semantic-field-definition-generator
```

## Usage

### Create field definitions

Define field definitions as a Python dict or in an external YAML file:

```yaml
prefix: http://rs.swissartresearch.net/instances/fields/

fields:

    - id: {unique identifier}
      label: {label}
      description: {description}
      dataType: {datatype}
      domain: {domain}
      range: {range}
      minOccurs: #
      maxOccurs: #
      queries:
        - ask: '{ask query}'
        - delete: '{delete query}'
        - insert: '{insert query}'
        - select: '{select query}'
        - valueSet: '{value set query}'
          
    - ...
```

Then, load and compile it using the the `write` action of the command line tool `semantic-field-util`

```
semantic-field-util -f RS -y ./fieldDefinitions.yml write -t ../ldp/assets/fieldDefinitions.trig
```

This will read the YAML file `fieldDefinitions.yml` and create ResearchSpace-flavor field definitions in the TriG file `../ldp/assets/fieldDefinitions.trig`. 

For more details on use of the command line tool run `semantic-field-util -h`.

You can also use the generator library in your Python program

```python
from sariFieldDefinitionsGenerator import generator

inputFile = './fieldDefinitions.yml'
outputFile = '../ldp/assets/fieldDefinitions.trig'

model = generator.loadSourceFromFile(inputFile)

output = generator.generate(model, generator.METAPHACTS)

with open(outputFile, 'w') as f:
    f.write(output)
```

Available templates are:
- `generator.METAPHACTS` for Metaphacts Open Source Platform (command line flavor `MP`)
- `generator.RESEARCHSPACE` for ResearchSpace (command line flavor `RS`)
- `generator.UNIVERSAL` for both platforms (command line flavor `UNI`)
- `generator.JSON` for a JSON representation (command line flavor `JSON`)
- `generator.INLINE` for a Backend Template version (command line flavor `INLINE`)

### Read field definitions

You can read semantic field definitions in RDF from a SPARQL endpoint or TriG files and create a YAML file in the format shown above using the `read` action of the command line tool `semantic-field-util`

```
semantic-field-util -f RS read -u http://localhost:8280/sparql -y ./fieldDefinitions.yml
```

This will read ResearchSpace-flavor field definitions from the SPARQL endpoint `http://localhost:8080/sparql` and create the YAML file `./fieldDefinitions.yml`.

You can also use the parser library in your Python program

```python
from SemanticFieldDefinitionGenerator import parser

sparql_uri = 'http://localhost:8080/sparql'
outputFile = './fieldDefinitions.yml'

store = parser.open_sparql_store(sparql_uri, repository='assets', auth_user='admin', auth_pass='admin')
fields = parser.read_fields(store, parser.RESEARCHSPACE)
parser.write_fields_yaml(fields, outputfile)
```
