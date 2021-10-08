from flask import Flask, request, jsonify
from zeep import Client, transports
from requests import Session, session
import os
import sys
from flask_swagger_ui import get_swaggerui_blueprint
from urllib.parse import urlparse
session.trust_env = False


url = os.getenv('SOAP_URL', '')
verify_ssl = os.getenv('VERIFY_SSL', False)
parsed_uri = urlparse(url)
host = '{uri.netloc}'.format(uri=parsed_uri)
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


# Custom Transport class to be able to get the
# raw response after the xml response parsing
class Transport(transports.Transport):
    def post(self, address, message, headers):
        parsed_address = urlparse(address)
        address = parsed_address._replace(netloc=host).geturl()
        self.xml_request = message.decode('utf-8')
        print(message.decode('utf-8'), file=sys.stderr)
        response = super().post(address, message, headers)
        # assign response to transport object
        # to be able to fetch last http response code
        self.response = response

        return response


def create_client(session):
    session.trust_env = False
    if url is not None:
        # create the soap client object and configure using the wsdl url
        return Client(url, transport=Transport(session=session))
    return None


def get_request_session(headers):
    session = Session()
    session.verify = verify_ssl
    header_list = ['Authorization']
    for header in headers:
        if header[0] in header_list:
            session.headers[header[0]] = header[1]
    return session


"""
    ----------------------------------------------------------------
    Functions to generate the swagger definition file
    ----------------------------------------------------------------
    vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
"""


def parseElements(elements, array=False):
    """
    source:
    https://stackoverflow.com/questions/50089400/introspecting-a-wsdl-with-python-zeep
    """
    all_elements = {}
    for name, element in elements:
        all_elements[name] = {}
        # all_elements[name]['required'] = not element.is_optional
        if hasattr(element.type, 'elements'):
            if (
                hasattr(element.type, '_array_type') and
                str(element.type).startswith('ArrayOf')
            ):
                all_elements[name]['type'] = 'array'
                all_elements[name]['items'] = parseElements(
                    element.type.elements, True)
            elif array is True:
                del all_elements[name]
                all_elements['properties'] = parseElements(
                    element.type.elements)
            else:
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


def generate_openapi_entry(api_path, input_parameter, output_parameter):
    return {
        'summary': api_path,  # TODO Add a request summary
        # 'description': '',  # TODO Add a request description
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
                'description': 'OK',
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
    session = get_request_session(request.headers)
    client = create_client(session)
    if client is None:
        # return 500 and no content, when the client failed to initialize
        return jsonify('internal error'), 500
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
                            operation_name,
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


@application.route('/test', methods=['GET'])
def refresh():
    if url is not None:
        # create the soap client object and configure using the wsdl url
        try:
            session = get_request_session(request.headers)
            # test, if the connection to the backend successful
            create_client(session)
            return jsonify(True), 200
        except Exception as e:
            return jsonify(e), 500
    return jsonify(False), 400


if __name__ == '__main__':
    application.debug = True
    application.run(host='0.0.0.0', port=5001)
