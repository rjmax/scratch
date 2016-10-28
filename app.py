"""
This script runs the application using a development server.
"""

import bottle
import os
import sys
from bottle import route, run, response
import json
import opsCenter
import nodes

@route('/')
def hello():
    response.headers['Content-Type'] = 'application/json'

    # This python script generates an ARM template that deploys DSE across multiple datacenters.
    with open('clusterParameters.json') as inputFile:
        clusterParameters = json.load(inputFile)

    locations = clusterParameters['locations']
    vmSize = clusterParameters['vmSize']
    nodeCount = clusterParameters['nodeCount']
    adminUsername = clusterParameters['adminUsername']
    adminPassword = clusterParameters['adminPassword']

    # This is the skeleton of the template that we're going to add resources to
    generatedTemplate = {
        "$schema": "https://schema.management.azure.com/schemas/2015-01-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {},
        "variables": {
            "uniqueString": "[uniqueString(resourceGroup().id, deployment().name)]"
        },
        "resources": [],
        "outputs": {
            "opsCenterURL": {
                "type": "string",
                "value": "[concat('http://opscenter', variables('uniqueString'), '.', resourceGroup().location, '.cloudapp.azure.com:8888')]"
            }
        }
    }

    # Create DSE nodes in each location
    for datacenterIndex in range(0, len(locations)):
        location = locations[datacenterIndex]
        resources = nodes.generate_template(location, datacenterIndex, vmSize, nodeCount, adminUsername, adminPassword, locations)
        generatedTemplate['resources'] += resources

    # Create the OpsCenter node
    resources = opsCenter.generate_template(locations, nodeCount, adminUsername, adminPassword)
    generatedTemplate['resources'] += resources

    return json.dump(generatedTemplate, outputFile, sort_keys=True, indent=4, ensure_ascii=False)


if '--debug' in sys.argv[1:] or 'SERVER_DEBUG' in os.environ:
    # Debug mode will enable more verbose output in the console window.
    # It must be set at the beginning of the script.
    bottle.debug(True)

def wsgi_app():
    """Returns the application to make available through wfastcgi. This is used
    when the site is published to Microsoft Azure."""
    return bottle.default_app()

if __name__ == '__main__':
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
    STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static').replace('\\', '/')
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555

    # Starts a local test server.
    bottle.run(server='wsgiref', host=HOST, port=PORT)
