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

    def templates(self):
        """Return a list of top level templates found in the given wikitext."""
        templates = []
        i = 0
        while i < len(self):
            if self[i:i+2] == '{{':
                nested = 1
                j = i + 2
                while nested and j < len(self):
                    if self[j:j+2] == '{{':
                        nested += 1
                        j += 2
                    elif self[j:j+2] == '}}':
                        nested -= 1
                        j += 2
                    else:
                        j += 1
                if not nested:
                    # found a valid template
                    templates.append(Wikitemplate.parse(self[i:j]))
                i = j
            else:
                i += 1
        return templates

class Wikitemplate(list):
    '''A wikitemplate is a list whose first element is its name and the rest are its arguments'''

    @classmethod
    def parse(cls, s):
        '''Parse a string into a `Wikitemplate`'''
        s = s.strip()
        if s[:2] != '{{':
            raise SyntaxError(r'Expected template opening: {{')
        if s[-2:] != '}}':
            raise SyntaxError(r'Expected template closing: }}')

        # find the location of each separator
        # e.g. if s = '{{one|two}}', then indices == [1, 5, 9], s[2:5] == 'one', s[6:9] == 'two'
        # also, don't index separators of nested templates
        separator_indices = [1]
        nested = 0
        for i in range(2, len(s)-2):
            if s[i] == '|' and not nested:
                separator_indices.append(i)
            elif s[i:i+2] == '{{':
                nested += 1
            elif s[i:i+2] == '}}':
                nested -= 1
        separator_indices.append(len(s)-2)

        tokens = []
        for i in range(len(separator_indices) - 1):
            start = 1 + separator_indices[i]
            end = separator_indices[i+1]
            token = s[start:end]
            tokens.append(token)

        return cls(tokens)

    @property
    def name(self):
        try:
            return self[0]
        except IndexError:
            return None

    @property
    def args(self):
        return self[1:]

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
