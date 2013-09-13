
import validictory
import re
from .uritemplate import expand_regex

DEBUG=True

def debug(mesg, params=None):
    if DEBUG:
        if params is not None:
            print mesg % params
        else:
            print mesg

class RestdocError(ValueError):
    '''
    errors encountered during restdoc validation
    '''

class RestdocValidator(object):
    '''
    Restdoc validator.  See https://github.com/RestDoc/specification/blob/master/specification.md
    '''

    def __init__(self, restdoc, validator_cls=validictory.SchemaValidator, format_validators=None):
        self.validator_cls = validator_cls
        self.format_validators=format_validators
        # Basic validation of restdoc itself.
        if not isinstance(restdoc, dict):
            raise RestdocError("Restdoc must be a dictionary.")
        self.restdoc = restdoc
        if 'resources' not in self.restdoc:
            raise RestdocError("Restdoc missing 'resources'.")
        self.resources = self.restdoc['resources']
        if not isinstance(self.resources, list):
            raise RestdocError("Resources must be a list.")

        self.schemas = self.restdoc.get('schemas', {})

        # Basic validation of each resource as well as pre-populating
        # path regex -> resource lookup table.
        self.resource_patterns = {}
        for resource in self.resources:
            self._validateResource(resource)
            self._addResourcePath(resource)

    def _addResourcePath(self, resource):
        # Compile the list of valid regex expansions.
        for valid_regex in expand_regex(resource['path'], resource.get('params', {})):
            try:
                regex = re.compile(valid_regex)
            except re.error as e:
                raise RestdocError("Invalid validation regex (%s): %s" % (e, valid_regex))
            self.resource_patterns[regex] = resource

    def _getResourceName(self, resource):
        if 'id' in resource:
            return resource['id']
        if 'path' in resource:
            return resource['path']
        return '(no id)'

    def _validateResource(self, resource):
        if not isinstance(resource, dict):
            raise RestdocError("Resource must be a dictionary")

        if 'path' not in resource:
            name = self._getResourceName(resource)
            raise RestdocError("Resource '%s' has no path." % name)

        if 'methods' not in resource:
            name = self._getResourceName(resource)
            raise RestdocError("Resource '%s' has no methods." % name)

    def findResource(self, path):
        matches = set()
        last_match = None
        for regex, resource in self.resource_patterns.iteritems():
            r = regex.match(path)
            if r is not None:
                matches.add(resource['path'])
                last_match = r
                last_resource = resource
        if len(matches) > 1:
            raise RestdocError("Multiple resources match path '%s': %s" % (path, list(matches)))
        if last_match is None:
            raise RestdocError("No resource found matching path '%s'" % path)
        uri_params = {}
        for param_idx, value in last_match.groupdict().iteritems():
            param = '_'.join(param_idx.split('_')[:-1])
            if param not in uri_params:
                uri_params[param] = []
            if value is not None:
                uri_params[param].append(value)
        return last_resource, uri_params
            

    def validateRequest(self, method, path, body='', headers={}, lazy_schema_matching=False):
        resource, uri_params = self.findResource(path)
        resource_name = self._getResourceName(resource)
        if method not in resource['methods']:
            raise RestdocError("Resource '%s' does not have method '%s'" % (resource_name, method))
        method_name = method + " " + resource_name

        resource_method = resource['methods'][method]
        if 'headers' in resource_method:
            for header, header_spec in resource_method['headers'].iteritems():
                if 'required' in header_spec and header_spec['required']:
                    if header not in headers:
                        raise RestdocError("Method '%s' requires header '%s'" % (method_name, header))

        matching_schema = None
        if 'accepts' in resource_method:
            errors = []

            for accept in resource_method['accepts']:
                if self._validate_schema(accept, body, errors, lazy_schema_matching):
                    matching_schema = accept
                    break

            if matching_schema is None:
                raise RestdocError("Method '%s' does not accept given body.  Errors: %s" % (method_name, errors)) 

        if 'headers' in self.restdoc:
            for header, header_spec in self.restdoc['headers'].get('request', {}).iteritems():
                if 'required' in header_spec and header_spec['required']:
                    if header not in headers:
                        raise RestdocError("Method '%s' requires header '%s'" % (method_name, header))

        return resource, uri_params, matching_schema

    def validateResponse(self, method, path, status, body='', headers={}, lazy_schema_matching=False):
        resource, uri_params = self.findResource(path)
        resource_name = self._getResourceName(resource)
        if method not in resource['methods']:
            raise RestdocError("Resource '%s' does not have method '%s'" % (resource_name, method))
        method_name = method + " " + resource_name

        resource_method = resource['methods'][method]
        if 'statusCodes' not in resource_method:
            raise RestdocError("Method '%s' missing statusCodes definition")

        statusCodes = self.restdoc.get('statusCodes', {})
        statusCodes.update(resource_method['statusCodes'])

        if str(status) not in statusCodes:
            raise RestdocError("Method '%s' responding with invalid status code '%s'" % (method_name, status))

        matching_schema = None
        errors = []
        status_spec = statusCodes[str(status)]
        if isinstance(status_spec, dict) and 'response' in status_spec:
            for response_type in status_spec['response'].get('types', []):
                if self._validate_schema(response_type, body, errors, lazy_schema_matching):
                    matching_schema = response_type
                    break

            for header, header_spec in status_spec['response'].get('headers', {}).iteritems():
                if 'required' in header_spec and header_spec['required']:
                    if header not in headers:
                        raise RestdocError("Method '%s' response requires header '%s'" % (method_name, header))

        if 'response' in resource_method:
            for response_type in resource_method['response'].get('types', []):
                if self._validate_schema(response_type, body, errors, lazy_schema_matching):
                    matching_schema = response_type
                    break

            for header, header_spec in resource_method['response'].get('headers', {}).iteritems():
                if 'required' in header_spec and header_spec['required']:
                    if header not in headers:
                        raise RestdocError("Method '%s' response requires header '%s'" % (method_name, header))

        if 'headers' in self.restdoc:
            for header, header_spec in self.restdoc['headers'].get('response', {}).iteritems():
                if 'required' in header_spec and header_spec['required']:
                    if header not in headers:
                        raise RestdocError("Method '%s' response requires header '%s'" % (method_name, header))
            
        if matching_schema is None:
            raise RestdocError("Method '%s' responded with invalid body.  Errors: %s" % (method_name, errors)) 

        return resource, uri_params, matching_schema

    def _validate_schema(self, method_schema, body, errors, lazy_schema_matching):
        if 'schema' not in method_schema or method_schema['schema'] not in self.schemas:
            if not lazy_schema_matching:
                # Ignore this schema; do not assume success.
                return False
            # Unknown schema.  Assume body is valid.
            return True

        schema_spec = self.schemas[method_schema['schema']]
        if schema_spec.get('type', 'url') != 'inline' or 'schema' not in schema_spec:
            if not lazy_schema_matching:
                # Ignore this schema; do not assume success.
                return False
            # Cannot analyse schema.  Assume body is valid.
            return True

        # Validate body against schema.
        try:
            validictory.validate(body, schema_spec['schema'], validator_cls=self.validator_cls,
                                 format_validators=self.format_validators,
                                 required_by_default=False, disallow_unknown_properties=True, 
                                 disallow_unknown_schemas=True, schemas=self.schemas)
            return True
        except ValueError as e:
            errors.append(e)
            return False



