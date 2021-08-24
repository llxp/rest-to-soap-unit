#!/usr/bin/env node

const {
  createServer,
  IncomingMessage,
  ServerResponse,
} = require('unit-http')

require('http').ServerResponse = ServerResponse
require('http').IncomingMessage = IncomingMessage

const express = require('express');
const bodyParser = require('body-parser');
const soap = require('strong-soap').soap;
//const util = require('util');

process.env["NODE_TLS_REJECT_UNAUTHORIZED"] = 0;
const url = process.env['SOAP_URL'];


const app = express();
app.use(bodyParser.json());

app.post('/api/:service/:port/:action', function (req, res) {
  try {
    soap.createClient(url, function(err, client) {
      client.on('soapError', function(err) {
        console.error(err);
      });
      //client.on('request', function(envelope) {
      //  console.error(util.inspect(envelope, {showHidden: false, depth: null}));
      });
      //client.on('response', function (responseBody, incomingMessage) {
      //  console.error(responseBody);
      //  console.error(incomingMessage);
      //});
      //console.error(req.body);
      //const description = client.describe();
      //console.log(JSON.stringify(description.IF_Savvy2Savvy_REQ.IF_Savvy2Savvy_REQSoap12.SCYCIF_Savvy2Savvy_Request));
      service = client[req.params.service];
      if (service) {
        port = service[req.params.port];
        if (port) {
          method = port[req.params.action];
          method(req.body, function(err, result) {
            res.send(err ? (err.body ? err.body : "") : result);
          }, null, { Authorization: req.header('Authorization') });
          return;
        }
      }
      res.send('Error');
    });
  } catch (e) {
    res.send(e);
  }
});

const openapiInterface = {
    'openapi': '3.0.0',
    'info': {
        'title': '',
        'description': '',
        'version': ''
    }
};

const generateOpenAPIEntry = (apiPath, inputParameter, outputParameter) => {
    return {
        'summary': apiPath,
        //'description': '',
        'requestBody': {
            'required': true,
            'content': {
                'application/json': {
                    'schema': {
                        'properties': inputParameter
                    }
                }
            }
        },
        'responses': {
            '200': {
                'description': 'OK',
                'content': {
                    'application/json': {
                        'schema': {
                            'properties':
                            outputParameter
                        }
                    }
                }
            }
        }
    }
};

//var server = app.listen(8000, function () {
//   var host = server.address().address
//   var port = server.address().port
//   console.log("Example app listening at http://%s:%s", host, port)
//});

const parseOperation = (apiPath, operation) => {
//  console.dir(operation);
//  console.log(operation.input);
//  console.log(operation.input.message.parts.parameters.element.parent);
  const elements = operation.input.message.parts.parameters.element.parent.elements;
  const elementNames = Object.keys(elements);
  for (const element of elementNames) {
    console.dir(elements[element].complexType, { depth: 2 });
  }
  const parsedInputElements = parseElements(elements);
  return generateOpenAPIEntry(apiPath, parsedInputElements, []);
};

const parseElements = (elements, array = false) => {
  const allElements = {};
  for (const element of Object.keys(elements)) {
    allElements[element] = {};
    console.log(elements[element]['$name']);
    if (typeof(elements[element].children) !== typeof(undefined) && elements[element].children.length > 0) {
      console.log('has children');
      parseElements(elements[element].children);
    }
  }
  return allElements;
};

app.get('/help', function (req, res) {
  try {
    const interface = openapiInterface;
    soap.createClient(url, function(err, client) {
      const services = Object.keys(client.wsdl['definitions']['services']);
      const operationsObject = {};
      for (const service of services) {
        const ports = Object.keys(client.wsdl['definitions']['services'][service]['ports']);
        for (const port of ports) {
          const operations = Object.keys(client.wsdl['definitions']['services'][service]['ports'][port]['binding']['operations']);
          for (const operation of operations) {
            const operationName = `/api/${service}/${port}/${operation}`;
            operationsObject[operationName] = {};
            const operationObject = client.wsdl['definitions']['services'][service]['ports'][port]['binding']['operations'][operation];
            operationsObject[operationName]['post'] = parseOperation(operationName, operationObject);
            operationsObject[operationName]['post']['tags'] = [service];
            for (let i = 0; i<10;++i) { console.log(); }
          }
        }
      }
      interface['paths'] = operationsObject;
      res.send(interface);
    });
  } catch (e) {
    res.send(e);
  }
});


createServer(app).listen();
