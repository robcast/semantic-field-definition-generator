# Semantic Field Definition Generator

A generator for Metaphacts/ResearchSpace semantic field definitions. Based on https://github.com/swiss-art-research-net/sari-field-definitions-generator

## Installation

install using pip

```sh
pip install semantic-field-definition-generator
```

## Usage

### Command line tool

For more details on the use of the command line tool run `semantic-field-util -h`:

```
usage: semantic-field-util [-h] [--version] [-f {RS,MP,UNI,JSON,INLINE}] -y YAML_FILE [-u SPARQL_URI]
                           [--sparql-repository SPARQL_REPOSITORY] [--sparql-auth-user SPARQL_USER]
                           [--sparql-auth-password SPARQL_PASS] [-t TRIG_FILE]
                           [--field-id-prefix FIELD_PREFIX] [--split-fields] [-l {INFO,DEBUG,ERROR}]
                           {read,write}

Utility to convert ResarchSpace/Metaphacts semantic field definitions.

positional arguments:
  {read,write}          Action: read=read semantic field definitions in RDF (SPARQL store or file) and
                        write YAML file, write=read YAML file and write semantic field definitions to
                        RDF file

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -f {RS,MP,UNI,JSON,INLINE}, --flavor {RS,MP,UNI,JSON,INLINE}
                        Flavor of RDF field definitions: RS=ResearchSpace, MP=Metaphacts,
                        UNI=universal, JSON=JSON, INLINE=inline, default=RS
  -y YAML_FILE, --yaml YAML_FILE
                        YAML file with field definitions to read or write
  -u SPARQL_URI, --sparql-uri SPARQL_URI
                        SPARQL endpoint URI, e.g. http://localhost:8081/sparql
  --sparql-repository SPARQL_REPOSITORY
                        Optional SPARQL repository parameter, default=assets
  --sparql-auth-user SPARQL_USER
                        Optional SPARQL auth username, default=admin
  --sparql-auth-password SPARQL_PASS
                        Optional SPARQL auth password, default=admin
  -t TRIG_FILE, --trig TRIG_FILE
                        RDF TriG file (can be directory containing *.trig files) to read or write
  --field-id-prefix FIELD_PREFIX
                        Optional URL prefix for field ids
  --split-fields        Optional split TriG output into one file per field (file name = field id)
  -l {INFO,DEBUG,ERROR}, --log {INFO,DEBUG,ERROR}
                        Log level.
```

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

This will read the YAML file `fieldDefinitions.yml` and create ResearchSpace-flavor (`-f RS`) field definitions in the TriG file `../ldp/assets/fieldDefinitions.trig`.

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

## Limitations

- The parser currently doesn't support "Tree Patterns".
- The generator currently doesn't support multiple values for "Domains", "Ranges" and "Default Values".
