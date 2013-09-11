from unittest import TestCase

from restdoc.uritemplate import expand_template


class TestExpandTemplate(TestCase):
    '''
    Test that uritemplate expansion conforms to http://tools.ietf.org/html/rfc6570
    '''

    context = {
        'count' :        ["one", "two", "three"],
        'dom' :          ["example", "com"],
        'dub' :          "me/too",
        'hello' :        "Hello World!",
        'half' :         "50%",
        'var' :          "value",
        'who' :          "fred",
        'base' :         "http://example.com/home/",
        'path' :         "/foo/bar",
        'list' :         ["red", "green", "blue", "Hello World!", None],
        'keys' :         {
                            "comma": ",",
                            "dot"  : ".",
                            "empty": "",
                            "semi" : ";",
                            "undef": None,
                         },
        'keys_tuple' :   [
                            ("semi" , ";"),
                            ("dot"  , "."),
                            ("empty", ""),
                            ("comma", ","),
                            ("undef", None),
                         ],
        'v' :            "6",
        'x' :            "1024",
        'y' :            "768",
        'empty' :        "",
        'empty_keys' :   {},
        'undef' :        None,
    }

    validations = {
        "simple" : {
            # 3.2.2. Simple String Expansion: {var}
            "{var}" :              "value",
            "{hello}" :            "Hello%20World%21",
            "{half}" :             "50%25",
            "O{empty}X" :          "OX",
            "O{undef}X" :          "OX",
            "{x,y}" :              "1024,768",
            "{x,hello,y}" :        "1024,Hello%20World%21,768",
            "?{x,empty}" :         "?1024,",
            "?{x,undef}" :         "?1024",
            "?{undef,y}" :         "?768",
            "{var:3}" :            "val",
            "{var:30}" :           "value",
            "{list}" :             "red,green,blue,Hello%20World%21",
            "{list*}" :            "red,green,blue,Hello%20World%21",
            "{keys}" :             "comma,%2C,dot,.,empty,,semi,%3B",
            "{keys*}" :            "comma=%2C,dot=.,empty,semi=%3B",
            "{keys_tuple}" :       "semi,%3B,dot,.,empty,,comma,%2C",
            "{keys_tuple*}" :      "semi=%3B,dot=.,empty,comma=%2C",
        },
        "reserved" : {
            # 3.2.3. Reserved Expansion: {+var}
            "{+var}" :                "value",
            "{+hello}" :              "Hello%20World!",
            "{+half}" :               "50%25",

            "{base}index" :           "http%3A%2F%2Fexample.com%2Fhome%2Findex",
            "{+base}index" :          "http://example.com/home/index",
            "O{+empty}X" :            "OX",
            "O{+undef}X" :            "OX",

            "{+path}/here" :          "/foo/bar/here",
            "here?ref={+path}" :      "here?ref=/foo/bar",
            "up{+path}{var}/here" :   "up/foo/barvalue/here",
            "{+x,hello,y}" :          "1024,Hello%20World!,768",
            "{+path,x}/here" :        "/foo/bar,1024/here",

            "{+path:6}/here" :        "/foo/b/here",
            "{+list}" :               "red,green,blue,Hello%20World!",
            "{+list*}" :              "red,green,blue,Hello%20World!",
            "{+keys}" :               "comma,,,dot,.,empty,,semi,;",
            "{+keys*}" :              "comma=,,dot=.,empty,semi=;",
            "{+keys_tuple}" :         "semi,;,dot,.,empty,,comma,,",
            "{+keys_tuple*}" :        "semi=;,dot=.,empty,comma=,",

        },
        "fragment" : {
            # 3.2.4. Fragment Expansion: {#var}
            "{#var}" :             "#value",
            "{#hello}" :           "#Hello%20World!",
            "{#half}" :            "#50%25",
            "foo{#empty}" :        "foo#",
            "foo{#undef}" :        "foo",
            "{#x,hello,y}" :       "#1024,Hello%20World!,768",
            "{#path,x}/here" :     "#/foo/bar,1024/here",
            "{#path:6}/here" :     "#/foo/b/here",
            "{#list}" :            "#red,green,blue,Hello%20World!",
            "{#list*}" :           "#red,green,blue,Hello%20World!",
            "{#keys}" :            "#comma,,,dot,.,empty,,semi,;",
            "{#keys*}" :           "#comma=,,dot=.,empty,semi=;",
            "{#keys_tuple}" :      "#semi,;,dot,.,empty,,comma,,",
            "{#keys_tuple*}" :     "#semi=;,dot=.,empty,comma=,",
        },
        "label" : {
            # 3.2.5. Label Expansion with Dot-Prefix: {.var}
            "{.who}" :             ".fred",
            "{.who,who}" :         ".fred.fred",
            "{.half,who}" :        ".50%25.fred",
            "www{.dom*}" :         "www.example.com",
            "X{.var}" :            "X.value",
            "X{.empty}" :          "X.",
            "X{.undef}" :          "X",
            "X{.var:3}" :          "X.val",
            "X{.list}" :           "X.red,green,blue,Hello%20World%21",
            "X{.list*}" :          "X.red.green.blue.Hello%20World%21",
            "X{.keys}" :           "X.comma,%2C,dot,.,empty,,semi,%3B",
            "X{.keys*}" :          "X.comma=%2C.dot=..empty.semi=%3B",
            "X{.keys_tuple}" :     "X.semi,%3B,dot,.,empty,,comma,%2C",
            "X{.keys_tuple*}" :    "X.semi=%3B.dot=..empty.comma=%2C",
            "X{.empty_keys}" :     "X",
            "X{.empty_keys*}" :    "X",
        },
        "path" : {
            # 3.2.6. Path Segment Expansion: {/var}
            "{/who}" :             "/fred",
            "{/who,who}" :         "/fred/fred",
            "{/half,who}" :        "/50%25/fred",
            "{/who,dub}" :         "/fred/me%2Ftoo",
            "{/var}" :             "/value",
            "{/var,empty}" :       "/value/",
            "{/var,undef}" :       "/value",
            "{/var,x}/here" :      "/value/1024/here",
            "{/var:1,var}" :       "/v/value",
            "{/list}" :            "/red,green,blue,Hello%20World%21",
            "{/list*}" :           "/red/green/blue/Hello%20World%21",
            "{/list*,path:4}" :    "/red/green/blue/Hello%20World%21/%2Ffoo",
            "{/keys}" :            "/comma,%2C,dot,.,empty,,semi,%3B",
            "{/keys*}" :           "/comma=%2C/dot=./empty/semi=%3B",
            "{/keys_tuple}" :      "/semi,%3B,dot,.,empty,,comma,%2C",
            "{/keys_tuple*}" :     "/semi=%3B/dot=./empty/comma=%2C",
        },
        "path-parameter" : {
            # 3.2.7. Path-Style Parameter Expansion: {;var}
            "{;who}" :             ";who=fred",
            "{;half}" :            ";half=50%25",
            "{;empty}" :           ";empty",
            "{;v,empty,who}" :     ";v=6;empty;who=fred",
            "{;v,bar,who}" :       ";v=6;who=fred",
            "{;x,y}" :             ";x=1024;y=768",
            "{;x,y,empty}" :       ";x=1024;y=768;empty",
            "{;x,y,undef}" :       ";x=1024;y=768",
            "{;hello:5}" :         ";hello=Hello",
            "{;list}" :            ";list=red,green,blue,Hello%20World%21",
            "{;list*}" :           ";list=red;list=green;list=blue;list=Hello%20World%21",
            "{;keys}" :            ";keys=comma,%2C,dot,.,empty,,semi,%3B",
            "{;keys*}" :           ";comma=%2C;dot=.;empty;semi=%3B",
            "{;keys_tuple}" :      ";keys_tuple=semi,%3B,dot,.,empty,,comma,%2C",
            "{;keys_tuple*}" :     ";semi=%3B;dot=.;empty;comma=%2C",
        },
        "query-expansion" : {
            # 3.2.8. Form-Style Query Expansion: {?var}
            "{?who}" :             "?who=fred",
            "{?half}" :            "?half=50%25",
            "{?x,y}" :             "?x=1024&y=768",
            "{?x,y,empty}" :       "?x=1024&y=768&empty=",
            "{?x,y,undef}" :       "?x=1024&y=768",
            "{?var:3}" :           "?var=val",
            "{?list}" :            "?list=red,green,blue,Hello%20World%21",
            "{?list*}" :           "?list=red&list=green&list=blue&list=Hello%20World%21",
            "{?keys}" :            "?keys=comma,%2C,dot,.,empty,,semi,%3B",
            "{?keys*}" :           "?comma=%2C&dot=.&empty=&semi=%3B",
            "{?keys_tuple}" :      "?keys_tuple=semi,%3B,dot,.,empty,,comma,%2C",
            "{?keys_tuple*}" :     "?semi=%3B&dot=.&empty=&comma=%2C",
        },
        "query-continuation" : {
            # 3.2.9. Form-Style Query Continuation: {&var}
            "{&who}" :             "&who=fred",
            "{&half}" :            "&half=50%25",
            "?fixed=yes{&x}" :     "?fixed=yes&x=1024",
            "{&x,y,empty}" :       "&x=1024&y=768&empty=",
            "{&x,y,undef}" :       "&x=1024&y=768",

            "{&var:3}" :           "&var=val",
            "{&list}" :            "&list=red,green,blue,Hello%20World%21",
            "{&list*}" :           "&list=red&list=green&list=blue&list=Hello%20World%21",
            "{&keys}" :            "&keys=comma,%2C,dot,.,empty,,semi,%3B",
            "{&keys*}" :           "&comma=%2C&dot=.&empty=&semi=%3B",
            "{&keys_tuple}" :      "&keys_tuple=semi,%3B,dot,.,empty,,comma,%2C",
            "{&keys_tuple*}" :     "&semi=%3B&dot=.&empty=&comma=%2C",
        },
    }
        

    def _test_expand(self, source, expected):
        self.assertEqual(expand_template(source, self.context), expected)

    def test_simple(self):
        for source, expected in self.validations["simple"].iteritems():
            self._test_expand(source, expected)

    def test_reserved(self):
        for source, expected in self.validations["reserved"].iteritems():
            self._test_expand(source, expected)

    def test_fragment(self):
        for source, expected in self.validations["fragment"].iteritems():
            self._test_expand(source, expected)

    def test_label(self):
        for source, expected in self.validations["label"].iteritems():
            self._test_expand(source, expected)

    def test_path(self):
        for source, expected in self.validations["path"].iteritems():
            self._test_expand(source, expected)

    def test_path_parameter(self):
        for source, expected in self.validations["path-parameter"].iteritems():
            self._test_expand(source, expected)

    def test_query_expansion(self):
        for source, expected in self.validations["query-expansion"].iteritems():
            self._test_expand(source, expected)

    def test_query_continuation(self):
        for source, expected in self.validations["query-continuation"].iteritems():
            self._test_expand(source, expected)
