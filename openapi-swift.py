#!/usr/bin/env python3

import subprocess
import argparse
import os
import json
import sys
import yaml
import re

def to_camel_case(snake_str):
    snake_str = snake_str.replace(' ', '_')
    snake_str = re.sub(r'([a-z])([A-Z])', '\\1_\\2', snake_str)
    components = snake_str.split('_')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return components[0].lower() + ''.join(x.title() for x in components[1:])

def type_from_schema(schema):
    if schema is None:
        return 'Void'
    if ref := schema.get('$ref'):
        return os.path.basename(ref)
    elif 'string' == schema.get("type"):
        type = 'String'
        if format := schema.get("format"):
            if format == 'uuid':
                type = 'UUID'
            elif format == 'byte':
                type = 'Data'
            else:
                type += f'/* {format} */'
        return type
    elif 'array' == schema.get("type"):
        return "["+type_from_schema(schema['items'])+"]"
    elif 'integer' == schema.get("type"):
        type = 'Int'
        if format := schema.get("format"):
            if format == 'int32':
                type = 'Int32'
            elif format == 'int64':
                type = 'Int64'
            else:
                type += f'/* {format} */'
        return type
    elif 'object' == schema.get("type"):
        return 'Any'
    elif 'boolean' == schema.get("type"):
        return 'Bool'
    elif allOf := property.get("allOf"):
        return type_from_schema(allOf[0])
    raise Exception(f'Unknown type: {schema}')

def set_in_dict(store, keys, value):
    head, *tail = keys
    if len(tail) > 0:
        if head not in store:
            store[head] = dict()
        if isinstance(store[head], dict):
            set_in_dict(store[head], tail, value)
    else:
        store[head] = value

def get_in_dict(store, *keys):
    head, *tail = keys
    # warn(head, store)
    if len(tail) > 0:
        if head in store:
            return get_in_dict(store[head], *tail)
        else:
            return None
    else:
        return store.get(head)

def warn(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get the build number based on git tags")

    parser.add_argument('--input', required=True, help='OpenAPI spec')
    parser.add_argument('--tab', default="    ", help='OpenAPI spec')
    parser.add_argument('--name', required=True, help='OpenAPI spec')
    args = parser.parse_args()
    tab = args.tab
    with open(args.input, 'r') as file:
        specification = yaml.load(file.read(), Loader=yaml.FullLoader)

    output = ""
    output += f"enum {args.name} {{\n"

    output += f"{tab}enum Operation {{\n"

    if paths := specification.get('paths'):
        for path in paths:
            for method in paths[path]:
                endpoint = paths[path][method]
                if description := endpoint.get('description'):
                    output += f'{tab}{tab}// {description}\n'
                output += f'{tab}{tab}case {to_camel_case(endpoint["operationId"])}'
                parameterIndex = 0
                if parameters := endpoint.get('parameters'):
                    output += '('
                    for parameter in parameters:
                        if parameterIndex > 0:
                            output += ', '
                        output += f'{parameter["name"]}: {type_from_schema(parameter["schema"])}'
                        parameterIndex += 1
                    output += ')'
                output += '\n'

        output += f'\n'

    output += f"{tab}{tab}func path(description: (Any) -> String) -> String {{\n"
    output += f"{tab}{tab}{tab}switch self {{\n"
    if paths := specification.get('paths'):
        for path in paths:
            for method in paths[path]:
                endpoint = paths[path][method]
                output += f'{tab}{tab}{tab}case .{to_camel_case(endpoint["operationId"])}'
                parameterIndex = 0
                if parameters := endpoint.get('parameters'):
                    output += '('
                    for parameter in parameters:
                        if parameterIndex > 0:
                            output += ', '
                        output += f'let {parameter["name"]}'
                        parameterIndex += 1
                    output += ')'
                output += ':\n'
                path = re.sub(r"{([^/{]+)}", f"\\(description(\\1))", path)
                output += f'{tab}{tab}{tab}{tab}return "{path}"\n'
            # output += f'\n'


    output += f"{tab}{tab}{tab}}}\n"
    output += f"{tab}{tab}}}\n"
    output += f"{tab}}}\n"
    output += f'\n'

    output += f"{tab}struct Endpoint<Response> {{ \n"
    output += f"{tab}{tab}let operation: Operation\n"
    output += f"{tab}{tab}let method: String\n"
    output += f"{tab}{tab}let body: Any?\n"

    if paths := specification.get('paths'):
        for path in paths:
            for method in paths[path]:
                endpoint = paths[path][method]
                output += "\n"
                operation = ""
                if description := endpoint.get('description'):
                    output += f'{tab}{tab}// {description}\n'
                output += f'{tab}{tab}static func {to_camel_case(endpoint["operationId"])}('
                operation += f'.{to_camel_case(endpoint["operationId"])}'
                body = "nil"
                if requestBody := endpoint.get('requestBody'):
                    body = "body"
                    output += f'_ {body}: {type_from_schema(requestBody["content"]["application/json"]["schema"])}'
                    if True != requestBody.get('required'):
                        output += '?'
                if parameters := endpoint.get('parameters'):
                    operation += '('
                    for parameter in parameters:
                        if not output.endswith('('):
                            output += ', '
                        if not operation.endswith('('):
                            operation += ', '
                        output += f'{parameter["name"]}: {type_from_schema(parameter["schema"])}'
                        operation += f'{parameter["name"]}: {parameter["name"]}'
                    operation += ')'
                # if parameterIndex > 0:
                #     output += f'\n'

                responseType = "Void"
                if httpOk := get_in_dict(endpoint, 'responses', '200') or get_in_dict(endpoint, 'responses', 200):
                    responseType = type_from_schema(get_in_dict(httpOk, "content", "application/json", "schema"))

                output += f') -> Endpoint<{responseType}> {{ \n'
                output += f'{tab}{tab}{tab}.init(operation: {operation},\n'
                output += f'{tab}{tab}{tab}         method: "{method.upper()}",\n'
                output += f'{tab}{tab}{tab}           body: {body})\n'
                output += f"{tab}{tab}}}\n"

    output += f"{tab}}}\n"

    if components := specification.get('components'):
        if schemas := components.get('schemas'):
            for className in schemas:
                output += "\n"
                schema = schemas[className]
                if description := schema.get('description'):
                    output += f'{tab}{tab}// {description}\n'
                if 'enum' in schema:
                    if schema['type'] != 'string':
                        exit('shit')
                    output += f"{tab}enum {className}: String, Codable, CaseIterable {{\n"
                    for case in schema['enum']:
                        output += f'{tab}{tab}case {to_camel_case(case)} = "{case}"\n'
                    output += f"{tab}}}\n"
                elif schema.get('type') in {'array', 'string'}:
                    output += f"{tab}typealias {className} = {type_from_schema(schema)}\n"
                else:
                    output += f"{tab}struct {className}: Codable {{\n"
                    for propertyName in schema['properties']:
                        property = schema['properties'][propertyName]

                        required = "?" if propertyName not in (schema.get("required") or []) else ""

                        if description := property.get('description'):
                            output += f'{tab}{tab}// {description}\n'

                        output += f'{tab}{tab}let {to_camel_case(propertyName)}: {type_from_schema(property)}{required}\n'

                    output += "\n"
                    output += f"{tab}{tab}enum CodingKeys: String, CodingKey {{\n"
                    for propertyName in schema['properties']:
                        output += f'{tab}{tab}{tab}case {to_camel_case(propertyName)} = "{propertyName}"\n'
                    output += f"{tab}{tab}}}\n"
                    output += f"{tab}}}\n"
    output += f"}}"

    print(output)
