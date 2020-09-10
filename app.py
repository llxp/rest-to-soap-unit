from flask import Flask, request, jsonify
from zeep import Client, transports
import zeep
import os
from flask_swagger_ui import get_swaggerui_blueprint


# Custom Transport class to be able to get the
# raw response after the xml response parsing
class Transport(transports.Transport):
    def post(self, address, message, headers):
        self.xml_request = message.decode('utf-8')
        response = super().post(address, message, headers)
        # assign response to transport object
        # to be able to fetch last http response code
        self.response = response

        return response


url = os.getenv('SOAP_URL')
# create the flask application object
application = Flask(__name__)
# swagger-ui config
swaggerui_blueprint = get_swaggerui_blueprint(
    '/doc',
    '/help',
    config={
        'app_name': "Test application"
    }
)
# add the swagger-ui blueprint to the flask application
application.register_blueprint(swaggerui_blueprint, url_prefix='/doc')

if url is not None:
    # create the soap client object and configure using the wsdl url
    client = Client(url, transport=Transport())


@application.route(
    # rest endpoint listens on /api/*
    '/api/<string:service>/<string:port>/<string:action>',
    # allow only post requests
    methods=['GET', 'POST'])
def index(service: str, port: str, action: str):
    if client is None:
        # return 500 and no content, when the client failed to initialize
        return '', 500
    try:
        if request.method == 'POST' and len(request.data) > 0:
            # if the body is not empty, try to parse the data as json data
            parameter = request.json
        else:
            parameter = None
    except Exception as e:
        # return http status 400 on parsing error
        return jsonify(str(e)), 400
    with client.settings(strict=True, xsd_ignore_sequence_order=True):
        try:
            if service != 'default' and port != 'default':
                service_obj = client.bind(service, port)
            elif service != 'default' and port == 'default':
                service_obj = client.bind(service, None)
            elif service == 'default' and port != 'default':
                service_obj = client.bind(None, port)
            else:
                service_obj = client.service
            # find the soap action provided by the wsdl
            method = getattr(service_obj, action)
            # execute the soap action
            if parameter is None:
                result = method()
            else:
                result = method(**parameter)
        except AttributeError as e:
            return jsonify(str(e)), 400
        except zeep.exceptions.Fault as e:
            # error in the exection of the requested soap action
            return jsonify(str(e)), client.transport.response.status_code
        except ValueError as e:
            # The String type doesn't accept collections as value ...
            return jsonify(str(e)), 400
        except zeep.exceptions.ValidationError as e:
            # missing parameter for the soap action
            return jsonify(str(e)), 400
        # parse response object and return json instead of xml
        a = zeep.helpers.serialize_object(result)
        return jsonify(a), client.transport.response.status_code


"""
    ----------------------------------------------------------------
    Functions to generate the swagger definition file
    ----------------------------------------------------------------
    vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
"""


def parseElements(elements):
    """
    source: https://stackoverflow.com/questions/50089400/introspecting-a-wsdl-with-python-zeep
    """
    all_elements = {}
    for name, element in elements:
        all_elements[name] = {}
        # all_elements[name]['required'] = not element.is_optional
        if hasattr(element.type, 'elements'):
            all_elements[name]['type'] = 'object'
            all_elements[name]['properties'] = parseElements(
                element.type.elements)
        else:
            # TODO add mapping of special objects if needed,
            # otherwise all objects not treated here default to string
            element_type = str(element.type)
            if element_type == 'String(value)':
                element_type = 'string'
            elif element_type == 'Integer(Value)':
                element_type = 'integer'
            elif element_type == 'Decimal(value)':
                element_type = 'number'
            elif element_type == 'Boolean(value)':
                element_type = 'boolean'
            elif 'array' in element_type or 'list' in element_type.lower():
                element_type = 'array'
            else:
                element_type = 'string'
            all_elements[name]['type'] = element_type

    return all_elements


def generate_openapi_entry(input_parameter, output_parameter):
    return {
        'summary': '',  # TODO Add a request summary
        'description': '',  # TODO Add a request description
        'requestBody': {
            'required': True,
            'content': {
                'application/json': {
                    'schema': {
                        'properties': input_parameter
                    }
                }
            }
        },
        'responses': {
            '200': {
                # TODO Add a response description
                'description': '',
                'content': {
                    'application/json': {
                        'schema': {
                            'properties':
                                output_parameter
                        }
                    }
                }
            }
        }
    }


@application.route(
    '/help',
    strict_slashes=False)
@application.route(
    '/help/<string:service>',
    defaults={'service': 'all'},
    strict_slashes=False)
@application.route(
    '/help/<string:service>/<string:port>',
    defaults={'port': 'all'})
def help(service: str = 'all', port: str = 'all'):
    with client.settings(strict=True, xsd_ignore_sequence_order=True):
        interface = {
            'openapi': '3.0.0',
            'info': {
                'title': '',  # TODO Add an api title
                'description': '',  # TODO Add an api description
                'version': ''  # TODO Add an api version
            }
        }
        operations = {}
        for service in client.wsdl.services.values():
            for port in service.ports.values():
                for operation in port.binding._operations.values():
                    operation_name = \
                        '/api/' + service.name + \
                        '/' + port.name + \
                        '/' + operation.name
                    operations[operation_name] = {}
                    parsed_input_elements = parseElements(
                        operation.input.body.type.elements)
                    parsed_output_elements = parseElements(
                        operation.output.body.type.elements)
                    operations[operation_name]['post'] = \
                        generate_openapi_entry(
                            parsed_input_elements,
                            parsed_output_elements)
                    operations[operation_name]['post']['tags'] = [service.name]
                interface['paths'] = operations
    return jsonify(interface)


"""
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ----------------------------------------------------------------
    Functions to generate the swagger definition file
    ----------------------------------------------------------------
"""


@application.route('/refresh', methods=['GET'])
def refresh():
    if url is not None:
        # create the soap client object and configure using the wsdl url
        global client
        try:
            client = Client(url, transport=Transport())
            return jsonify(True), 200
        except Exception as e:
            return jsonify(e), 500
    return jsonify(False), 400


if __name__ == '__main__':
    application.debug = True
    application.run(host='0.0.0.0', port=5001)
