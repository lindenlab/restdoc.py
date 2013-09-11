from urllib import quote
import re
op_table = {}

DEBUG=False

ALPHA               =  "A-Za-z"
DIGIT               =  "0-9"
HEXDIG              =  "%sA-Fa-f" % DIGIT

pct_encoded         =  "%%[%s]{2}" % HEXDIG
unreserved          =  "%s%s-._~" % (ALPHA, DIGIT)
gen_delims          =  ":/?#[]@"
gen_delims_escaped  =  ":/?#\[\]@"
sub_delims          =  "!$&'()*+,;="
reserved            =  "%s%s" % (gen_delims, sub_delims)
reserved_escaped    =  "%s%s" % (gen_delims_escaped, sub_delims)

#ucschar        =  %xA0-D7FF / %xF900-FDCF / %xFDF0-FFEF
#               /  %x10000-1FFFD / %x20000-2FFFD / %x30000-3FFFD
#               /  %x40000-4FFFD / %x50000-5FFFD / %x60000-6FFFD
#               /  %x70000-7FFFD / %x80000-8FFFD / %x90000-9FFFD
#               /  %xA0000-AFFFD / %xB0000-BFFFD / %xC0000-CFFFD
#               /  %xD0000-DFFFD / %xE1000-EFFFD
#
#iprivate       =  %xE000-F8FF / %xF0000-FFFFD / %x100000-10FFFD

def debug(mesg, params=None):
    if DEBUG:
        if params is not None:
            print mesg % params
        else:
            print mesg

def expand_template(source, context):
    debug("expand_template: expanding: %s", source)
    end = len(source)
    ret = ""
    i = 0
    while i < end:
        c = source[i]
        if c == '{':
            j = i
            try:
                while source[j] != '}':
                    j += 1
            except IndexError:
                raise URITemplateError("Mismatched {}: %s" % source[i:])
            ret += expand_expression(source[i + 1:j], context)
            i = j
        else:
            ret += c
        i += 1
    return ret

def expand_expression(expr, context):
    if expr[0] in op_table:
        expr_type = op_table[expr[0]]
        expr = expr[1:]
    else:
        expr_type = SimpleExpr

    debug("expand_expression: expr_type %s", expr_type)
    
    return expr_type.expand(expr.split(','), context)

def expand_regex(source, params):
    debug("expand_regex: %s" % source)
    end = len(source)
    regex_template = "^"
    i = 0
    validations=[]
    validation_idx = 0
    while i < end:
        c = source[i]
        if c == '{':
            j = i
            try:
                while source[j] != '}':
                    j += 1
            except IndexError:
                raise URITemplateError("Mismatched {}: %s" % source[i:])
            param_regex, param_validations = expand_regex_expression(source[i + 1:j], params, validation_idx)
            regex_template += param_regex
            validations += param_validations
            validation_idx += 1
            i = j
        else:
            regex_template += c
        i += 1
    regex_template += "$"

    debug("regex_template: %s", regex_template)

    done = False
    valid_regex_list=[]
    while not done:
        regex_dict = {}
        # Construct a map of param to regex mappings.
        for i in range(len(validations)):
            validation_idx = validations[i][1]
            regex_dict[validations[i][0]] = validations[i][2][validation_idx]

        valid_regex_list.append(regex_template % regex_dict)

        # Increment combinations.
        i = 0
        while 1:
            validations[i][1] += 1
            if len(validations[i][2]) == validations[i][1]:
                validations[i][1] = 0
                i += 1
                if len(validations) == i:
                    done = True
                    break
            else:
                break
    return valid_regex_list

def expand_regex_expression(expr, params, param_idx):
    if expr[0] in op_table:
        expr_type = op_table[expr[0]]
        expr = expr[1:]
    else:
        expr_type = SimpleExpr
    
    return expr_type.expand_regex(expr.split(','), params, param_idx)
    
class URITemplateError(Exception):
    pass

class SimpleExpr(object):
    glue   = ','
    leader = ''

    @classmethod
    def expand(cls, names, data):
        expanded = []
        for name in names:
            # Check for explode prefix modifier.
            explode = name[-1] == '*'
            if explode: name = name[:-1] 
            # Check for max-length prefix modifier.
            segments = name.split(":")
            max_length = None
            if len(segments) > 1:
                try:
                    max_length = int(segments[-1])
                except ValueError as e:
                    debug("%s.expand: Skipping non-integer max-length in name '%s'" % (cls, name))

                if max_length is not None and max_length > 0 and max_length < 10000:
                    name = ":".join(segments[:-1])
                    debug("%s.expand: Using max-length %s from name '%s'" % (cls, max_length, name))
                else:
                    max_length = None
        
            if name in data:
                debug("%s.expand: expanding '%s' (explode=%s, max_length=%s) using data: %s", (cls, name, explode, max_length, data[name]))
                expanded_name = cls.expand_name(name, data[name], explode, max_length)
                debug("%s.expand: expanded to: %s", (cls, expanded_name))
                if expanded_name is not None:
                    debug("%s.expand: appending: %s", (cls, expanded_name))
                    expanded.append(expanded_name)
            else:
                debug("%s.expand: name '%s' not in context", (cls, name))
        if len(expanded) == 0:
            expanded_names = ''
        else:
            expanded_names = cls.leader + cls.glue.join(expanded)
        debug("%s.expand: '%s' + '%s'.join(%s) => %s", (cls, cls.leader, cls.glue, expanded, expanded_names))
        return expanded_names

    @classmethod
    def expand_regex(cls, names, params, param_idx):
        expanded_regex = []
        param_regex = ''
        if cls.leader != '':
            param_regex += "\%s?" % cls.leader
        param_regex += "(?:"

        param_regex_list = []
        for name in names:
            explode = name[-1] == '*'
            if explode: name = name[:-1]
            # *TODO: Support this?
            if explode:
                raise URITemplateError("Explode modifier not supported")

            param_key = name + "_" + str(param_idx)
            name_regex, name_validators = cls.expand_param_regex(name, param_key, params)
            expanded_regex.append([param_key, 0, name_validators])
            param_regex_list.append(name_regex)
        param_regex += "|".join(param_regex_list)
        param_regex += "){0,%d}" % len(names)
        return param_regex, expanded_regex

    @classmethod
    def expand_param_regex(cls, name, param_key, params):
        name_validators = []
        valid_characters = "[^%s]" % cls.glue
        if name in params and 'validations' in params[name]:
            for validation in params[name]['validations']:
                if validation.get('type', '') == 'match':
                    pattern = validation['pattern']
                    regex_prefix = ''
                    regex_suffix = ''
                    if pattern[0] == '^':
                        pattern = pattern[1:]
                    else:
                        regex_prefix = valid_characters + "*"
                    if pattern[-1] == '$':
                        pattern = pattern[:-1]
                    else:
                        regex_suffix = valid_characters + "*"
                    if len(pattern) == 0:
                        pattern = valid_characters + "+"
                    # Test that the pattern will compile
                    try:
                        _regex = re.compile(pattern)
                    except re.error as e:
                        raise URITemplateError("Invalid validation pattern for parameter '%s' (%s): %s" % (name, e, pattern))
                    name_validators.append(regex_prefix + pattern + regex_suffix)
        if len(name_validators) == 0:
            name_validators = [valid_characters + "+"]
        name_regex = cls.expand_name_regex(name, param_key)
        return name_regex, name_validators

    @classmethod
    def expand_name_regex(cls, name, param_key):
        return "%s?(?P<%s>%%(%s)s)()" % (cls.glue, param_key, param_key)

    @classmethod
    def expand_name(cls, name, data, explode, max_length):
        # Expand keys types
        try:
            if hasattr(data, 'items'):
                items = data.items()
                sort = True
                debug("%s.expand_name: data using attribute 'items': %s" % (cls, items))
            else:
                items = data
                sort = False
                debug("%s.expand_name: data: %s" % (cls, items))
            if type(items) in (list, tuple):
                return cls.expand_pairs(name, items, explode, max_length, sort)
            else:
                debug("%s.expand_name: Skipping expand_pairs on '%s' %s: %s", (cls, name, type(items), items))
        except TypeError as e:
            debug("%s.expand_name: except %s", (cls, str(e)))
        except ValueError as e:
            debug("%s.expand_name: except %s", (cls, str(e)))

        # Expand list types
        if not isinstance(data, basestring):
            try:
                return cls.expand_list(name, data, explode, max_length)
            except TypeError as e:
                debug("%s.expand_name: except %s", (cls, str(e)))
            except ValueError as e:
                debug("%s.expand_name: except %s", (cls, str(e)))

        return cls.expand_one(name, data, max_length)

    @classmethod
    def expand_one(cls, name, data, max_length):
        if data is None:
            expanded = None
        else:
            expanded = cls.escape(data, max_length)
        debug("%s.expand_one: %s => %s", (cls, data, expanded))
        return expanded

    @classmethod
    def expand_pairs(cls, name, items, explode, max_length, sort):
        glue = explode and cls.glue or ','
        #import pdb; pdb.set_trace();
        if sort:
            debug("%s.expand_pairs: sorting items", cls)
            items.sort()
        pairs_list = []
        for k, v in items:
            if v is None:
                debug("%s.expand_pairs: skipping undefined key '%s'", (cls, k))
                continue
            pairs_list.append(cls.expand_pair(k, v, explode, max_length))
        debug("%s.expand_pairs: checking for 0 length on %s", (cls, pairs_list))
        if len(pairs_list) == 0:
            return None
        return glue.join(pairs_list)

    @classmethod
    def expand_pair(cls, k, v, explode, max_length):
        if explode and v == "":
            expanded = k 
        else:
            pairglue = explode and '=' or ','
            expanded = pairglue.join([k, cls.escape(v, max_length)])
        debug("%s.expand_pair: (%s, %s) -> %s" % (cls, k, v, expanded))
        return expanded
    
    @classmethod
    def expand_list(cls, name, data, explode, max_length):
        items = [cls.escape(v, max_length) for v in data if v is not None]
        glue = explode and cls.glue or ','
        debug("%s.expand_list: checking for 0 length on %s", (cls, items))
        if len(items) == 0:
            expanded = None
        else:
            expanded = glue.join(items)
        debug("%s.expand_list: %s => %s", (cls, data, expanded))
        return expanded

    @staticmethod
    def escape(value, max_length):
        escaped = quote(str(value[:max_length]), safe='')
        debug("SimpleExpr.escape: quote %s -> %s", (value, escaped))
        return escaped

class ReservedExpr(SimpleExpr):
    @staticmethod
    def escape(value, max_length):
        '''
        The allowed set for a given expansion depends on the expression type:
        reserved ("+") and fragment ("#") expansions allow the set of
        characters in the union of ( unreserved / reserved / pct-encoded ) to
        be passed through without pct-encoding.
        '''
        escaped = quote(str(value[:max_length]), safe="%" + reserved)

        # Note that the percent character ("%") is only allowed
        # as part of a pct-encoded triplet and only for reserved/fragment
        # expansion: in all other cases, a value character of "%" MUST be pct-
        # encoded as "%25" by variable expansion.
        segments = escaped.split("%")
        escaped = segments[0]
        for segment in segments[1:]:
            # Check for a valid pct-encoded triplet.
            try:
                h = int(segment[:2], 16)
                # Valid.  Put back the '%'.
                escaped += '%'
            except:
                # Invalid.  Insert a '%25' encoding.
                escaped += '%25'
            escaped += segment

        debug("ReservedExpr.escape: quote %s -> %s", (value, escaped))
        return escaped

class FragmentExpr(ReservedExpr):
    leader = "#"

class LabelExpr(SimpleExpr):
    glue   = '.'
    leader = '.'

class PathSegmentExpr(SimpleExpr):
    glue   = '/'
    leader = '/'

class KeepNameMixin(object):
    @classmethod
    def expand_one(cls, name, data, max_length):
        expanded = super(KeepNameMixin, cls).expand_one(name, data, max_length)
        if expanded is not None:
            if not cls.form_style and expanded == "":
                expanded = name
            else:
                expanded = name + '=' + expanded
        return expanded
    
    @classmethod
    def expand_list(cls, name, data, explode, max_length):
        #expanded = super(KeepNameMixin, cls).expand_list(name, data, explode, max_length)
        if explode:
            items = ["%s=%s" % (name, cls.escape(v, max_length)) for v in data if v is not None]
        else:
            items = [cls.escape(v, max_length) for v in data if v is not None]
        glue = explode and cls.glue or ','
        debug("%s.expand_list: checking for 0 length on %s", (cls, items))
        if len(items) == 0:
            expanded = None
        else:
            expanded = glue.join(items)
            if not explode:
                expanded = name + '=' + expanded
        debug("%s.expand_list: %s => %s", (cls, data, expanded))
        return expanded


    @classmethod
    def expand_pairs(cls, name, data, explode, max_length, sort):
        expanded = super(KeepNameMixin, cls).expand_pairs(name, data, explode, max_length, sort)
        if expanded is not None and not explode:
            expanded = name + '=' + expanded
        debug("%s.expand_pairs: expanding '%s' => '%s' with data: %s" % (cls, name, expanded, data))
        return expanded

    @classmethod
    def expand_pair(cls, k, v, explode, max_length):
        expanded = super(KeepNameMixin, cls).expand_pair(k, v, explode, max_length)
        if explode and cls.form_style and v == "":
            expanded += "="
        debug("%s.expand_pair: (%s, %s) -> %s" % (cls, k, v, expanded))
        return expanded

    @classmethod
    def expand_name_regex(cls, name, param_key):
        return "%s?%s=?(?P<%s>%%(%s)s)()" % (cls.glue, name, param_key, param_key)


class PathParamExpr(KeepNameMixin, SimpleExpr):
    leader = ';'
    glue   = ';'
    form_style = False

class QueryExpr(KeepNameMixin, SimpleExpr):
    leader = '?'
    glue   = '&'
    form_style = True

class QueryContinuationExpr(QueryExpr):
    leader = '&'

for cls in (QueryContinuationExpr, QueryExpr, PathParamExpr, PathSegmentExpr, LabelExpr, SimpleExpr, FragmentExpr):
    op_table[cls.leader] = cls

op_table['+'] = ReservedExpr
