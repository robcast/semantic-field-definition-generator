#!/usr/bin/env python3
from SemanticFieldDefinitionGenerator import generator, parser
import argparse
import logging
import sys

__version__ = '1.0'

def main():
    ## 
    ## main
    ##
    argp = argparse.ArgumentParser(description='Utility to convert ResarchSpace/Metaphacts semantic field definitions.')
    argp.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    argp.add_argument('action', choices=['read', 'write'],
                      help='Action: read=read semantic field definitions in RDF (SPARQL store or file) and write YAML file, '
                      + 'write=read YAML file and write semantic field definitions to RDF file')
    argp.add_argument('-f', '--flavor', dest='flavor', choices=['RS', 'MP', 'UNI', 'JSON', 'INLINE'],
                      default='RS',
                      help='Flavor of RDF field definitions: RS=ResearchSpace, MP=Metaphacts, UNI=universal, '
                      + 'JSON=JSON, INLINE=inline, default=RS')
    argp.add_argument('-y', '--yaml', required=True, dest='yaml_file',
                      help='YAML file with field definitions to read or write')
    argp.add_argument('-u', '--sparql-uri', dest='sparql_uri',
                      help='SPARQL endpoint URI, e.g. http://localhost:8081/sparql')
    argp.add_argument('--sparql-repository', dest='sparql_repository', default='assets',
                      help='Optional SPARQL repository parameter, default=assets')
    argp.add_argument('--sparql-auth-user', dest='sparql_user', default='admin',
                      help='Optional SPARQL auth username, default=admin')
    argp.add_argument('--sparql-auth-password', dest='sparql_pass', default='admin',
                      help='Optional SPARQL auth password, default=admin')
    argp.add_argument('-t', '--trig-file', dest='trig_file',
                      help='RDF TriG file to read (can be directory containing *.trig files) or write')
    argp.add_argument('-l', '--log', dest='loglevel', choices=['INFO', 'DEBUG', 'ERROR'], default='INFO', 
                      help='Log level.')
    args = argp.parse_args()
    
    logging.basicConfig(level=args.loglevel)
    
    ##
    ## write action
    ##
    if args.action == 'write':
        if args.flavor == 'RS':
            flavor = generator.RESEARCHSPACE
        elif args.flavor == 'MP':
            flavor = generator.METAPHACTS
        elif args.flavor == 'UNI':
            flavor = generator.UNIVERSAL
        elif args.flavor == 'JSON':
            flavor = generator.JSON
        elif args.flavor == 'INLINE':
            flavor = generator.INLINE
            
        if not args.trig_file:
            sys.exit(f"ERROR: action 'write' requires TRIG_FILE!")
            
        logging.info(f"reading field definitions from YAML file {args.yaml_file}")
        model = generator.loadSourceFromFile(args.yaml_file)
        output = generator.generate(model, flavor)
        with open(args.trig_file, 'w') as f:
            logging.info(f"writing field definitions to RDF trig file {args.trig_file} in flavor {args.flavor}")
            f.write(output)
    
    ##
    ## read action
    ##        
    elif args.action == 'read':
        if args.flavor == 'RS':
            flavor = parser.RESEARCHSPACE
        elif args.flavor == 'MP':
            flavor = parser.METAPHACTS
        else:
            sys.exit(f"ERROR: action 'read' does not support flavor {args.flavor}!")
    
        if args.sparql_uri:
            store = parser.open_sparql_store(args.sparql_uri, repository=args.sparql_repository, 
                                      auth_user=args.sparql_user, auth_pass=args.sparql_pass)
        elif args.trig_file:
            store = parser.read_trig_store(args.trig_file)
        else:
            sys.exit(f"ERROR: action 'read' requires SPARQL_URI or TRIG_FILE!")
    
        fields = parser.read_fields(store, flavor)
        parser.write_fields_yaml(fields, args.yaml_file)