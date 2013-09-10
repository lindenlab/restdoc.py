from unittest import TestCase
from copy import deepcopy

from restdoc.validate import RestdocValidator, RestdocError


class TestValidate(TestCase):
    spec = {
        "schemas" : {
            "inline_empty" : {
                "type" : "inline",
                "schema" : {
                    "type" : "string",
                    "blank" : True,
                    "maxLength" : 0,
                }
            },

            "inline_object_1" : {
                "type" : "inline",
                "schema" : {
                    "type" : "object",
                    "description" : "An inline object",
                    "required" : ["prop1", "prop2"],
                    "properties" : {
                        "prop1" : { "type" : "integer", },
                        "prop2" : { "type" : "string", "maxLength" : 6 },
                        "prop3" : {
                            "type" : "integer",
                            "minimum" : -1,
                            "maximum" : 51,
                        },
                    }
                }
            },
            "inline_object_2" : {
                "type" : "inline",
                "schema" : {
                    "type" : "object",
                    "description" : "Another inline object",
                    "required" : ["prop4"],
                    "properties" : {
                        "prop4" : { "type" : "integer", "minimum" : 1 },
                    }
                }
            },
            "inline_object_pattern" : {
                "type" : "inline",
                "schema" : {
                    "type" : "object",
                    "patternProperties": {
                        "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" : {
                            "type" : "object",
                            "$ref" : "inline_object_1",
                        }
                    },
                    "additionalProperties" : False,
                }
            },
            "inline_object_allof" : {
                "type" : "inline",
                "schema" : {
                    "type" : "object",
                    "allOf" : [
                        { "$ref" : "inline_object_1" },
                        { "$ref" : "inline_object_2" },
                    ]
                }
            },
            "inline_object_ref" : {
                "type" : "inline",
                "schema" : {
                    "type" : "object",
                    "required" : [ "prop6", "prop7" ],
                    "properties" : {
                        "prop5" : { "$ref" : "inline_object_1" },
                        "prop6" : { "$ref" : "inline_object_2" },
                        "prop7" : { "type" : "boolean" },
                    },
                    "additionalProperties" : False,
                }
            },
            "inline_object_allof_ref" : {
                "type" : "inline",
                "schema" : {
                    "type" : "object",
                    "allOf" : [ {
                        "$ref" : "inline_object_2",
                    }, {
                        "type" : "object",
                        "required" : [ "prop8" ],
                        "properties" : {
                            "prop8" : { "$ref" : "inline_object_1" },
                        }
                    }]
                }
            },
        },
        "statusCodes" : {
            "400" : {
                "description" : "Invalid request",
                "response" : {
                    "types" : [{
                            "type" : "application/json",
                            "schema" : "inline_object_1"
                        }
                    ]
                }
            },
            "500" : {
                "description" : "Internal Error",
                "response" : {
                    "types" : [{
                            "type" : "application/llsd+xml",
                            "schema" : "inline_object_2"
                        }
                    ]
                }
            }
        },
        "headers" : {
            "request" : {
                "Accept" : {
                    "description" : "Preferred response Content-Type."
                },
                "Accept-Encoding" : {
                    "description" : "Preferred response encoding (e.g. 'gzip')"
                },
                "Cache-Control" : {
                    "description" : "Directives to caching mechanisms."
                },
                "Content-Type" : {
                    "description" : "Content type of request payload."
                }
            },
            "response" : {
                "Cache-Control" : {
                    "description" : "Directives to caching mechanisms.",
                    "required" : True
                },
                "Content-Encoding" : {
                    "description" : "Response encoding (e.g. 'gzip')"
                },
                "Content-Location" : {
                    "description" : "Canonical location of requested resource."
                },
                "Content-Type" : {
                    "description" : "Content type of response payload.",
                    "required" : True
                },
                "Vary" : {
                    "description" : "Indicates the set of request-header fields that determines request variants.",
                    "required" : True
                }
            }
        },
        "resources" : [{
                "id" : "resource1",
                "description" : "A resource",
                "path" : "/resource1/{resource_id}{?param1,param2}",
                "params" : {
                    "resource_id" : {
                        "description" : "Resource ID",
                        "validations" : [{
                                "type" : "match",
                                "pattern" : "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                            }, {
                                "type" : "match",
                                "pattern" : "^(alt1|alt2)$"
                            }, {
                                "type" : "match",
                                "pattern" : "^(alt3|alt4)$"
                            }
                        ]
                    },
                    "param1" : {
                        "description" : "Parameter 1",
                    },
                    "param2" : {
                        "description" : "Parameter 2",
                        "default" : 0,
                        "validations" : [{
                            "type" : "match",
                            "pattern" : "^([0-9]+)?$"
                        }]
                    },
                },
                "methods" : {
                    "GET" : {
                        "description" : "Retrieve resource 1",
                        "statusCodes" : {
                            "200" :  {
                                "description" : "Resource 1 retrieved successfully",
                                "response" : {
                                    "types" : [{
                                            "type" : "application/json",
                                            "schema" : "inline_object_1",
                                        }, {
                                            "type" : "application/json",
                                            "schema" : "inline_object_2",
                                        }
                                    ],
                                    "headers" : {
                                        "ETag" : {
                                            "description" : "Current value of the entity tag for the requested variant.",
                                            "required" : True
                                        }
                                    }
                                }
                            },
                            "304" : {
                                "description" : "Not modified",
                                "response" : {
                                    "types" : [{
                                            "type" : "application/json",
                                            "schema" : "inline_empty",
                                        }
                                    ],
                                    "headers" : {
                                        "ETag" : {
                                            "description" : "Current value of the entity tag for the requested variant.",
                                            "required" : True
                                        }
                                    }
                                }
                            },
                            "404" : {
                                "description" : "Category not found",
                                "response" : {
                                    "types" : [{
                                            "type" : "application/json",
                                            "schema" : "inline_object_pattern",
                                        }
                                    ]
                                }
                            },
                            "412" : {
                                "description" : "Precondition failed",
                                "response" : {
                                    "types" : [{
                                            "type" : "application/json",
                                            "schema" : "inline_object_allof",
                                        }
                                    ],
                                    "headers" : {
                                        "ETag" : {
                                            "description" : "Current value of the entity tag for the requested variant.",
                                            "required" : True
                                        }
                                    }
                                }
                            }
                        },
                        "headers" : {
                            "If-Match" : {
                                "description" : "Only process request if any supplied entity tags matches resource."
                            },
                            "If-None-Match" : {
                                "description" : "Only process request if none of the supplied entity tags matches resource."
                            }
                        }
                    },
                    "POST" : {
                        "description" : "Create a sub resource 2",
                        "statusCodes" : {
                            "201" :  {
                                "description" : "Resource 2 created",
                                "response" : {
                                    "types" : [{
                                            "type" : "application/json",
                                            "schema" : "inline_object_ref",
                                        }
                                    ],
                                    "headers" : {
                                        "Location" : {
                                            "description" : "The URL of the newly created resource 2",
                                            "required" : True
                                        }
                                    }
                                }
                            },
                            "404" : {
                                "description" : "Resource 1 not found",
                                "response" : {
                                    "types" : [{
                                            "type" : "application/json",
                                            "schema" : "inline_object_allof_ref",
                                        }
                                    ]
                                }
                            },
                            "409" : {
                                "description" : "Resource 2 already exists",
                                "response" : {
                                    "types" : [{
                                            "type" : "application/json",
                                            "schema" : "inline_object_2",
                                        }
                                    ]
                                }
                            },
                        },
                        "accepts" : [{
                                "type" : "application/llsd+xml",
                                "schema" : "inline_object_1",
                            }, {
                                "type" : "application/llsd+xml",
                                "schema" : "inline_object_2",
                            }
                        ]
                    },
                }
            }, {
                "id" : "resource2",
                "description" : "A sub resource",
                "path" : "/resource1/{resource_id1}/{resource_id2}{?param1,param2}",
                "params" : {
                    "resource_id" : {
                        "description" : "Resource ID",
                        "validations" : [{
                                "type" : "match",
                                "pattern" : "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                            }, {
                                "type" : "match",
                                "pattern" : "^(alt1|alt2)$"
                            }, {
                                "type" : "match",
                                "pattern" : "^(alt3|alt4)$"
                            }
                        ]
                    },
                    "param1" : {
                        "description" : "Parameter 1",
                    },
                    "param2" : {
                        "description" : "Parameter 2",
                        "default" : 0,
                        "validations" : [{
                            "type" : "match",
                            "pattern" : "^([0-9]+)?$"
                        }]
                    },
                },
                "methods" : {
                    "GET" : {
                        "description" : "Retrieve resource 2",
                        "statusCodes" : {
                            "200" :  {
                                "description" : "Resource 2 retrieved",
                                "response" : {
                                    "types" : [{
                                            "type" : "application/json",
                                            "schema" : "inline_object_2"
                                        }
                                    ],
                                }
                            },
                            "404" : {
                                "description" : "Resource 2 not found",
                                "response" : {
                                    "types" : [{
                                            "type" : "application/json",
                                            "schema" : "inline_object_1",
                                        }
                                    ]
                                }
                            },
                        },
                    },
                }
            }
        ]
    }

    RESOURCE_ID1 = '86e9be95-bd0e-4b05-8518-df4048792c29'
    RESOURCE_ID2 = '1ab9ce78-8fa2-41b5-af4e-44d9e59cf80f'


    def setUp(self):
        self.validator = RestdocValidator(self.spec)

        self.VALID_RESPONSE_HEADERS = {
            'ETag' : '1',
            'Vary' : 'Accept',
            'Content-Type' : 'application/json',
            'Cache-Control' : 'no-cache',
        }

        self.VALID_OBJECT_1 = {
            'prop1' : 0,
            'prop2' : 'test',
        }

        self.VALID_OBJECT_2 = {
            'prop4' : 1,
        }

        self.VALID_OBJECT_PATTERN = {
            '0cc311ce-9ca7-44ef-9ec8-f19b445387a5' : {
                'prop1' : 1,
                'prop2' : 'test2',
            }
        }

        self.VALID_OBJECT_REF = {
            'prop5' : deepcopy(self.VALID_OBJECT_1),
            'prop6' : deepcopy(self.VALID_OBJECT_2),
            'prop7' : True,
        }

        self.VALID_RESOURCE1_PATH = "/resource1/4f71b22f-e7ea-4afe-b822-a83bce4c248f"
        self.EXPECTED_PARAMS1 = {
            'resource_id' : '4f71b22f-e7ea-4afe-b822-a83bce4c248f',
            'param2' : None,
            'param1' : None,
        }

        self.VALID_RESOURCE2_PATH = "/resource1/4f71b22f-e7ea-4afe-b822-a83bce4c248f/34f7bc1c-8240-42ff-8d36-442da6d3531b"
        self.EXPECTED_PARAMS2 = {
            'resource_id1' : '4f71b22f-e7ea-4afe-b822-a83bce4c248f',
            'resource_id2' : '34f7bc1c-8240-42ff-8d36-442da6d3531b',
            'param2' : None,
            'param1' : None,
        }

        self.path = self.VALID_RESOURCE1_PATH
        self.params = deepcopy(self.EXPECTED_PARAMS1)
        self.headers = deepcopy(self.VALID_RESPONSE_HEADERS)

    def _test_request(self, method, path, expected_resource, expected_params = {},
                      expected_schema=None, body='', headers={}):
        resource, uri_params, schema = self.validator.validateRequest(method, path, headers=headers, body=body)
        self.assertEqual(resource['id'], expected_resource)
        if expected_schema is None:
            self.assertEqual(schema, expected_schema)
        else:
            self.assertEqual(schema['schema'], expected_schema)

        for k, v in expected_params.iteritems():
            self.assertTrue(k in uri_params)
            if v is None:
                self.assertEqual(len(uri_params[k]), 0)
            else:
                self.assertTrue(str(v) in uri_params[k])

    def _test_response(self, method, path, status, expected_resource, expected_params = {}, 
            expected_schema=None, body='', headers={}, raiseAssert=True):
        resource, uri_params, schema = self.validator.validateResponse(method, path, status, body, headers)
        self.assertEqual(resource['id'], expected_resource)
        if expected_schema is None:
            self.assertEqual(schema, expected_schema)
        else:
            self.assertEqual(schema['schema'], expected_schema)

        for k, v in expected_params.iteritems():
            self.assertTrue(k in uri_params)
            if v is None:
                self.assertEqual(len(uri_params[k]), 0)
            else:
                self.assertTrue(str(v) in uri_params[k])

    def _test_response_fail(self, *args, **kwargs):
        try:
            self._test_response(*args, **kwargs)
        except (AssertionError, RestdocError):
            return
        raise AssertionError("_test_response did not raise assertion.")

    def test_request_success(self):
        self._test_request('GET', self.VALID_RESOURCE1_PATH, 'resource1', self.EXPECTED_PARAMS1)

    def test_request_fail(self):
        self.assertRaises(RestdocError, self._test_request, 'GET', '/resource1', 'resource1')

    def test_params_parsing(self):
        body = deepcopy(self.VALID_OBJECT_1)

        for status in [200, 400]:
            self.path = self.VALID_RESOURCE1_PATH
            self.params = deepcopy(self.EXPECTED_PARAMS1)
            self._test_response('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            self.path += "?param2=42"
            self.params['param2'] = 42
            self.params['param1'] = None
            self._test_response('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            self.path += "&param1=test"
            self.params['param1'] = 'test'
            self._test_response('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            self.path += "&bad=test"
            self._test_response_fail('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)


        path = self.VALID_RESOURCE1_PATH
        params = deepcopy(self.EXPECTED_PARAMS1)
        self._test_response('GET', path, 200, 'resource1', params, 'inline_object_1', body, self.headers)

        for alt in ['alt1', 'alt2', 'alt3', 'alt4', '5bb12122-0973-48b6-8fc1-54ccf7b89fcc']:
            path = '/resource1/' + alt
            params['resource_id'] = alt
            self._test_response('GET', path, 200, 'resource1', params, 'inline_object_1', body, self.headers)

        for alt in ['test1', 'foo', '42', '0.0', '']:
            path = '/resource1/' + alt
            params['resource_id'] = alt
            self._test_response_fail('GET', path, 200, 'resource1', params, 'inline_object_1', body, self.headers)

        path = self.VALID_RESOURCE1_PATH
        params = deepcopy(self.EXPECTED_PARAMS1)
        params['resource_id'] = 'foo'
        self._test_response_fail('GET', path, 200, 'resource1', params, 'inline_object_1', body, self.headers)

        path = self.VALID_RESOURCE1_PATH + "?param2=42"
        params = deepcopy(self.EXPECTED_PARAMS1)
        params['param2'] = "42"
        self._test_response('GET', path, 200, 'resource1', params, 'inline_object_1', body, self.headers)

        path = self.VALID_RESOURCE1_PATH + "?param2=test"
        params['param2'] = "test"
        self._test_response_fail('GET', path, 200, 'resource1', params, 'inline_object_1', body, self.headers)

    def test_inline_object(self):
        for status in [200, 400]:
            body = deepcopy(self.VALID_OBJECT_1)
            self._test_response('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            body['prop3'] = -1
            self._test_response('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            body['prop3'] = 51
            self._test_response('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            body['prop2'] = "123456"
            self._test_response('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            body['prop3'] = "51"
            self._test_response_fail('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            body['prop3'] = 52
            self._test_response_fail('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            body['prop3'] = -2
            self._test_response_fail('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            body['prop3'] = False
            self._test_response_fail('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            del body['prop3']
            body['prop2'] = ''
            self._test_response_fail('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            body['prop2'] = '1234567'
            self._test_response_fail('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            del body['prop2']
            self._test_response_fail('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

            body = deepcopy(self.VALID_OBJECT_2)
            self._test_response_fail('GET', self.path, status, 'resource1', self.params, 'inline_object_1', body, self.headers)

        self.path = self.VALID_RESOURCE2_PATH
        self.params = deepcopy(self.EXPECTED_PARAMS2)
        body = deepcopy(self.VALID_OBJECT_2)
        self._test_response('GET', self.path, 200, 'resource2', self.params, 'inline_object_2', body, self.headers)

        body['prop4'] = 0.9
        self._test_response_fail('GET', self.path, 200, 'resource2', self.params, 'inline_object_2', body, self.headers)

        body['prop4'] = 0
        self._test_response_fail('GET', self.path, 200, 'resource2', self.params, 'inline_object_2', body, self.headers)

        del body['prop4']
        self._test_response_fail('GET', self.path, 200, 'resource2', self.params, 'inline_object_2', body, self.headers)

    def test_response_headers(self):
        body = deepcopy(self.VALID_OBJECT_1)
        headers = deepcopy(self.VALID_RESPONSE_HEADERS)
        self._test_response('GET', self.path, 200, 'resource1', self.params, 'inline_object_1', body, headers)

        headers = {}
        self._test_response_fail('GET', self.path, 200, 'resource1', self.params, 'inline_object_1', body, headers)

        for required in self.VALID_RESPONSE_HEADERS.keys():
            headers = deepcopy(self.VALID_RESPONSE_HEADERS)
            del headers[required]
            self._test_response_fail('GET', self.path, 200, 'resource1', self.params, 'inline_object_1', body, headers)

        headers = deepcopy(self.VALID_RESPONSE_HEADERS)
        body = self.VALID_OBJECT_REF
        self._test_response_fail('POST', self.path, 201, 'resource1', self.params, 'inline_object_ref', body, headers)
        headers['Location'] = 'foo'
        self._test_response('POST', self.path, 201, 'resource1', self.params, 'inline_object_ref', body, headers)


    def test_empty_response(self):
        body = ''
        self._test_response('GET', self.path, 304, 'resource1', self.params, 'inline_empty', body, self.headers)
        self._test_response_fail('GET', self.path, 200, 'resource1', self.params, 'inline_empty', body, self.headers)
        body = 'test'
        self._test_response_fail('GET', self.path, 304, 'resource1', self.params, 'inline_empty', body, self.headers)

    def test_inline_object_pattern(self):
        body = deepcopy(self.VALID_OBJECT_PATTERN)
        self._test_response('GET', self.path, 404, 'resource1', self.params, 'inline_object_pattern', body, self.headers)
        body['c17b0aab-fdb3-4ada-b7ef-5f77056632d3'] = self.VALID_OBJECT_1
        self._test_response('GET', self.path, 404, 'resource1', self.params, 'inline_object_pattern', body, self.headers)
        body['c17b0aab-fdb3-4ada-b7ef-5f77056632d3'] = self.VALID_OBJECT_2
        self._test_response_fail('GET', self.path, 404, 'resource1', self.params, 'inline_object_pattern', body, self.headers)

        body = {
           'test' : self.VALID_OBJECT_1,
        }
        self._test_response_fail('GET', self.path, 404, 'resource1', self.params, 'inline_object_pattern', body, self.headers)

        body = deepcopy(self.VALID_OBJECT_PATTERN)
        body['test'] =  self.VALID_OBJECT_1
        self._test_response_fail('GET', self.path, 404, 'resource1', self.params, 'inline_object_pattern', body, self.headers)

        body = deepcopy(self.VALID_OBJECT_PATTERN)
        body[''] =  self.VALID_OBJECT_1
        self._test_response_fail('GET', self.path, 404, 'resource1', self.params, 'inline_object_pattern', body, self.headers)

    def test_inline_allof(self):
        body = deepcopy(self.VALID_OBJECT_1)
        body.update(self.VALID_OBJECT_2)
        self._test_response('GET', self.path, 412, 'resource1', self.params, 'inline_object_allof', body, self.headers)
        body = self.VALID_OBJECT_1
        self._test_response_fail('GET', self.path, 412, 'resource1', self.params, 'inline_object_allof', body, self.headers)

        body = self.VALID_OBJECT_2
        self._test_response_fail('GET', self.path, 412, 'resource1', self.params, 'inline_object_allof', body, self.headers)

    def test_inline_object_ref(self):
        self.headers['Location'] = 'foo'
        body = deepcopy(self.VALID_OBJECT_REF)
        self._test_response('POST', self.path, 201, 'resource1', self.params, 'inline_object_ref', body, self.headers)

        del body['prop5']
        self._test_response('POST', self.path, 201, 'resource1', self.params, 'inline_object_ref', body, self.headers)

        del body['prop7']
        self._test_response_fail('POST', self.path, 201, 'resource1', self.params, 'inline_object_ref', body, self.headers)

        body = deepcopy(self.VALID_OBJECT_REF)
        body['test'] = 1
        self._test_response_fail('POST', self.path, 201, 'resource1', self.params, 'inline_object_ref', body, self.headers)


    def test_inline_allof_object_ref(self):
        self.headers = deepcopy(self.VALID_RESPONSE_HEADERS)

        body = {
            'prop8' : self.VALID_OBJECT_1
        }
        self._test_response_fail('POST', self.path, 404, 'resource1', self.params, 'inline_object_allof_ref', body, self.headers)

        body = deepcopy(self.VALID_OBJECT_2)
        self._test_response_fail('POST', self.path, 404, 'resource1', self.params, 'inline_object_allof_ref', body, self.headers)

        body['prop8'] = self.VALID_OBJECT_1

        self._test_response('POST', self.path, 404, 'resource1', self.params, 'inline_object_allof_ref', body, self.headers)


    def test_another_resource(self):
        self.path = self.VALID_RESOURCE2_PATH
        self.params = deepcopy(self.EXPECTED_PARAMS2)
        body = self.VALID_OBJECT_2
        self._test_response('GET', self.path, 200, 'resource2', self.params, 'inline_object_2', body, self.headers)

        body = self.VALID_OBJECT_1
        self._test_response('GET', self.path, 404, 'resource2', self.params, 'inline_object_1', body, self.headers)


