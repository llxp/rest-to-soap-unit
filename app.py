from flask import Flask, request, jsonify
from zeep import Client, Plugin, transports
from lxml import etree
import zeep
import json
import os

url = os.getenv('soap_url', None)

class Transport(transports.Transport):
    def post(self, address, message, headers):
        self.xml_request = message.decode('utf-8')
        response = super().post(address, message, headers)
        self.response = response
        
        return response

application = Flask(__name__)
if url is not None:
    client = Client(url, transport=Transport())

@application.route(
    '/api/<string:action>', # rest endpoint listens on /api/*
    methods=['POST']) # allow only post requests
def index(action: str):
    if client is None:
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
    with client.settings(strict=True,xsd_ignore_sequence_order=True):
        # find the soap action provided by the wsdl
        method = getattr(client.service, action)
        try:
            # execute the soap action
            result = method(parameter)
        except zeep.exceptions.Fault as e:
            # error in the exection of the requested soap action
            return jsonify(e.message), client.transport.response.status_code
        except ValueError as e:
            # The String type doesn't accept collections as value ...
            return jsonify(str(e)), 400
        except zeep.exceptions.ValidationError as e:
            # missing parameter for the soap action
            return jsonify(str(e)), 400
        # parse response object and return json instead of xml
        a = zeep.helpers.serialize_object(result)
        return jsonify(a), client.transport.response.status_code