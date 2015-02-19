import json
import os
import re
import string
import sys

class Wikitext(str):
    '''A string with extra helper methods to process wikitext'''

    def filter_sections(self, *args):
        r'''Return a new `Wikitext`, filtered by case-insensitive section titles in the order of the
        given `*args` strings. Return an empty `Wikitext` if no matches.

        >>> wt = Wikitext(
        ...     '==English==\n'
        ...     '===Pronunciation===\n'
        ...     '* /english ipa/\n'
        ...     '==French==\n'
        ...     '===Pronunciation===\n'
        ...     '* /french ipa/\n'
        ... )
        >>> wt.filter_sections('english', 'pronunciation')
        '===Pronunciation===\n* /english ipa/\n'
        '''

        if not args or not self:
            return Wikitext(self)
        lines = self.splitlines(keepends=True)

        # find the line that starts the section, and the corresponding header level
        for i, line in enumerate(lines):
            section_title = line.strip('=' + string.whitespace).lower()
            if section_title == args[0]:
                level = self.heading_level(line)
                break
        else:
            i = 0 # default if empty lines

        # the section ends at the next matching header level
        for j in range(i+1, len(lines)):
            if self.heading_level(lines[j]) == level:
                break
        else:
            j = len(lines) # default

        filtered = ''.join(lines[i:j])
        return Wikitext(filtered).filter_sections(*args[1:])

    @classmethod
    def heading_level(cls, s):
        count = 0
        for c in s.lstrip():
            if c == '=':
                count += 1
            else:
                break
        return count

def parse_xml_to_json(infile, outfile):
    import xml.etree.ElementTree as ET
    def recursive_clear(elem):
        for nested_elem in list(elem):
            recursive_clear(nested_elem)
        elem.clear()

    def make_json(word, text):
        return json.dumps({'word': word, 'text': text})

    ns = '{http://www.mediawiki.org/xml/export-0.9/}'

    errors = []
    words = []
    with open(outfile, 'w', encoding='utf-8') as out:
        out.write('[\n')
        for event, elem in ET.iterparse(infile):
            # unexpected event
            if event != 'end':
                err = 'unknown event: ' + event
                print(err)
                errors.append(err)

            # remove namespace prefix from tag
            tag = elem.tag
            if tag.find(ns) != -1:
                tag = elem.tag[len(ns):]
            else: # unexpected tag
                err = 'unexpected tag: ' + tag
                print(err)
                errors.append(err)

            # obtain words
            if tag == 'page':
                # words are assumed to have ns = 0
                if elem.find(ns+'ns').text == '0':
                    word = elem.find('./{0}title'.format(ns)).text
                    text = elem.find('./{0}revision/{0}text'.format(ns)).text
                    if text.find('==English==') != -1:
                        words.append(word)
                        out.write(make_json(word, text) + ',\n')
                # clear page from memory
                recursive_clear(elem)

        out.write(make_json('', ''))
        out.write('\n]')
    print('words found:', len(words))
    print('errors:', errors)
    return len(words)

def get_english(wikitext):
    # split by sections with header ==TITLE==
    regex = r'(^==[^=]+==\s*$)'
    results = re.split(regex, wikitext, flags=re.MULTILINE)
    # find the section for English and save the result
    for i, res in enumerate(results):
        if res.strip() == '==English==':
            english_section = results[i] + results[i+1]
            break
    else:
        english_section = ''
    return english_section

def get_pronunciation(wikitext):
    """return all pronunciation sections found"""
    regex = r'(^==+[^=]+==+\s*$)'
    results = re.split(regex, wikitext, flags=re.MULTILINE)
    # find the sections for pronunciation and save the result
    pronunciation = ''
    for i, res in enumerate(results):
        if res.strip(string.whitespace + '=') == 'Pronunciation':
            pronunciation += results[i] + results[i+1]
    return pronunciation


def get_ipa_test(wikitext):
    """return a list of IPA's found"""
    # match /slashes/ (phonemic transcriptions in IPA)
    ipalist = []
    reg_template = r'{{.*?}}'
    reg_ipa = r'/.*?/'
    for line in wikitext.splitlines():
        for template in re.findall(reg_template, line):
            if re.search(r'IPA(?!char)', template):
                ipalist += re.findall(reg_ipa, template)
    return ipalist

def get_ipa(wikitext):
    """return a list of IPA's found"""
    # match /slashes/ (phonemic transcriptions in IPA)
    ipalist = []
    re_ipa = r'/.*?/'
    templates = get_templates(wikitext)
    for template in templates:
        if template.name in ('IPA', 'audio-IPA'):
            for arg in template.args:
                match = re.search(re_ipa, arg)
                if match:
                    ipalist.append(match.group())
    return ipalist

def get_ipa_lenient(wikitext):
    reg = r'/[^/]+/'
    ipalist = re.findall(reg, wikitext)
    return ipalist

class Wikitemplate(list):

    @classmethod
    def parse(cls, s):
        if s[:2] != '{{' or s[-2:] != '}}':
            msg = 'string "{}" must start with "{{{{" and end with "}}}}"'.format(s)
            raise SyntaxError(msg)
        # TODO: don't split arguments on inner templates
        return cls(map(str.strip, s[2:-2].split('|')))

    @property
    def name(self):
        return self[0] if self else None

    @property
    def args(self):
        return self[1:]

def get_templates(wikitext):
    """Return a list of top level templates found in the given wikitext."""
    templates = []
    i = 0
    while i < len(wikitext):
        if wikitext[i:i+2] == '{{':
            # find matching '}}'
            stack = ['{{']
            j = i + 2
            while stack and j < len(wikitext):
                if wikitext[j:j+2] == '}}':
                    stack.pop()
                    j += 2
                elif wikitext[j:j+2] == '{{':
                    stack.append('{{')
                    j += 2
                else:
                    j += 1
            if stack:
                # SyntaxError: unclosed template
                #print('skipping unclosed template: {}'.format(wikitext[i:j]))
                pass
            else:
                # parse and collect template
                templates.append(Wikitemplate.parse(wikitext[i:j]))
            i = j
        else:
            i += 1
    return templates

def normalize_accent(accent):
    accents = {
        '': '',
        'Audio': '',
        'Audio (US)': 'US',
        'audio (US)': 'US',
        'Audio (U.S.A.)': 'US',
        'Audio (US, Northern California)': 'US',
        'Audio (Northern California, US)': 'US',
        'Audio (UK)': 'UK',
        'Audio (CA)': 'CA',
        'Audio (AUS)': 'AU',
        'Audio (Australia)': 'AU',
        'US': 'US',
        'GenAm': 'US',
        'UK': 'UK',
        'RP': 'UK',
        'British': 'UK',
        'Canada': 'CA',
        'CA': 'CA',
        'Australia': 'AU',
        'AusE': 'AU',
        'AU': 'AU',
        'Aus': 'AU',
        'NZ': 'NZ',
        'Ireland': 'IE'
    }
    return accents[accent] if accent in accents else '--'

def ipas_from_template(template):
    ipas = []
    re_ipa = r'/.+/'
    for arg in template.args:
        # obtain first match in each arg
        match = re.search(re_ipa, arg)
        if match:
            ipas.append(match.group())
    return ipas

def parse_pron(wikitext):
    '''Parse a pronunciation wikitext section into audio and ipa.'''
    audio_list = []
    ipa_list = []
    for line in wikitext.splitlines():
        templates = get_templates(line)
        # grab accents from the first accent template, default: ''
        accents = ['']
        for t in templates:
            if t.name == 'a':
                accents = t.args
                break
        assert accents, 'Expected arguments in template: {}'.format(t)
        # associate each template with the accent
        for a in accents:
            a = normalize_accent(a)
            for t in templates:
                if t.name == 'IPA':
                    for ipa in ipas_from_template(t):
                        ipa_list.append({'ipa': ipa, 'accent': a})
                elif t.name == 'audio':
                    # grab accent from audio template if not given
                    if not a:
                        a = normalize_accent(t.args[1])
                    audio_list.append({'filename': t.args[0], 'accent': a})
                elif t.name == 'audio-IPA':
                    audio_list.append({'filename': t.args[0], 'accent': a})
                    for ipa in ipas_from_template(t):
                        ipa_list.append({'ipa': ipa, 'accent': a})
                else:
                    # TODO: log skipped templates?
                    pass
    return {'audio': audio_list, 'ipa': ipa_list}

def map_filter_dict(f, d):
    """return two dictionary copies: one with mapped values using `f`, another
    with original values where f(value) is empty/False.
    """
    hit, miss = {}, {}
    for key, val in d.items():
        new_val = f(val)
        if new_val:
            hit[key] = new_val
        else:
            miss[key] = val
    return hit, miss

def json_load(filename):
    """shortcut for json.load using a filename"""
    with open(filename, 'r', encoding='utf-8') as f:
        wikitext_dict = json.load(f)
    return wikitext_dict

def json_dump(obj, filename, indent=2, **kwargs):
    """shortcut for json.dump using a filename and default preferred options
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=indent, **kwargs)

map_functions = {'lang': get_english, 'pron': get_pronunciation, 'ipa': get_ipa}

def pipeline(start='text', end='ipa'):
    # TODO: ipa_lenient and ipa_diff
    steps = ['text', 'lang', 'pron', 'ipa']
    assert start in steps and end in steps, 'steps: {}'.format(steps)
    # prepare output folder
    folder = 'out/'
    os.makedirs(folder, exist_ok=True)
    # track the next step in the pipeline and parse appropriately
    n = steps.index(start) + 1
    end_n = steps.index(end)
    while n <= end_n:
        step_from = steps[n-1]
        step_to = steps[n]
        print(step_from, 'to', step_to)
        wikidict = json_load(folder + step_from + '.json')
        map_function = map_functions[steps[n]]
        hit, miss = map_filter_dict(map_function, wikidict)
        print(len(hit), 'hits,', len(miss), 'misses')
        json_dump(hit, folder + step_to + '.json')
        json_dump(miss, folder + 'no_' + step_to + '.json')
        n += 1

if __name__ == '__main__':
    if len(sys.argv) not in (2, 3):
        print('Usage: python {} start [end]'.format(sys.argv[0]))
    else:
        kwargs = {}
        kwargs['start'] = sys.argv[1]
        if len(sys.argv) == 3:
            kwargs['end'] == sys.argv[2]
        pipeline(**kwargs)

#if __name__ == '__main__':
#    import sys
#    if len(sys.argv) != 3:
#        print('Expected 2 arguments: infile and outfile.')
#    else:
#        infile, outfile = sys.argv[1:3]
#        parse_xml_to_json(infile, outfile)
