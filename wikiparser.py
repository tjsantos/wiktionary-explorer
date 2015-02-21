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

        filtered = ''
        i = 0
        while i < len(lines):
            # find the line that starts the section, and the corresponding header level
            while i < len(lines):
                section_title = lines[i].strip('=' + string.whitespace).lower()
                if section_title == args[0]:
                    level = self.heading_level(lines[i])
                    # section starts at lines[i]
                    break
                i += 1

            # the section ends when the next header level is less than or equal to initial level
            for j in range(i+1, len(lines)):
                if 0 < self.heading_level(lines[j]) <= level:
                    # section ends at lines[j]
                    break
            else:
                j = len(lines) # default

            filtered += ''.join(lines[i:j])
            i = j
        # recursive filter on the rest of the arguments
        return Wikitext(filtered).filter_sections(*args[1:])

    @classmethod
    def heading_level(cls, s):
        '''Return 0 if `s` is not a heading.'''
        count = 0
        for c in s.lstrip():
            if c == '=':
                count += 1
            else:
                break
        return count

    def tokenize_templates(self):
        '''Return a list of tokens from the wikitext, classified as either templates or strings
        (non-templates)
        '''
        tokens = []
        i = 0
        start_token = 0
        while i < len(self):
            if self[i:i+2] == '{{':
                # add the last token
                if i > start_token:
                    tokens.append(self[start_token:i])
                # find matching bracket
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
                # parse template and add it to the list
                if not nested:
                    tokens.append(Wikitemplate.parse(self[i:j]))
                i = j
                start_token = j
            else:
                i += 1
        if i > start_token:
            tokens.append(self[start_token:i])
        return tokens

    # TODO: refactor template parser

    def extract_pronunciation(self):
        '''Return JSON serializable IPA and audio information.

        {'ipa': [{'ipa': /example/, 'accent': 'GB'}, ...],
         'audio': [{'filename': 'En-us-example.ogg', 'accent': ''}, ...]}
        '''
        ipa_results = []
        audio_results = []
        for line in self.splitlines():
            accents = ['']
            templates = (t for t in Wikitext.tokenize_templates(line)
                         if isinstance(t, Wikitemplate))
            for t in templates:
                if t.name == 'a':
                    accents = [normalize_accent(a) for a in t.args]
                if t.name in Wikitemplate.IPA_templates:
                    for ipa in t.extract_ipa_list():
                        for accent in accents:
                            ipa_results.append({'ipa': ipa, 'accent': accent})
                if 'audio' in t.name:
                    for accent in accents:
                        audio_results.append({
                            'filename': normalize_filename(t.args[0]),
                            'accent': accent or normalize_accent(t.args[1])
                        })
        return {'ipa': ipa_results, 'audio': audio_results}

    def extract_ipa_lenient(self):
        '''Return a list of all results enclosed by "/".'''
        return re.findall(r'/[^/]+/', self)

class Wikitemplate(list):
    '''A wikitemplate is a list whose first element is its name and the rest are its arguments'''

    IPA_templates = ('IPA', 'audio-IPA', 'audio-pron')

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
            token = s[start:end].strip()
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

    def extract_ipa_list(self):
        if self.name not in self.IPA_templates:
            return []
        ipa_list = []
        re_ipa = r'/.+?/' # non-greedy match of first result enclosed by '/'
        for arg in self.args:
            # obtain first match in each arg
            match = re.search(re_ipa, arg)
            if match:
                ipa_list.append(match.group())
        return ipa_list


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

def normalize_accent(accent):
    accents = {
        '': '',
        'Audio': '',
        'Audio (US)': 'US',
        'audio (US)': 'US',
        'Audio (U.S.A.)': 'US',
        'Audio (US, Northern California)': 'US',
        'Audio (Northern California, US)': 'US',
        'Audio (UK)': 'GB',
        'Audio (CA)': 'CA',
        'Audio (AUS)': 'AU',
        'Audio (Australia)': 'AU',
        'US': 'US',
        'GenAm': 'US',
        'UK': 'GB',
        'RP': 'GB',
        'British': 'GB',
        'Canada': 'CA',
        'CA': 'CA',
        'Australia': 'AU',
        'AusE': 'AU',
        'AU': 'AU',
        'Aus': 'AU',
        'NZ': 'NZ',
        'Ireland': 'IE'
    }
    return accents[accent] if accent in accents else ''

def normalize_filename(filename):
    # capitalize first letter and replace blanks with underscores
    filename = filename[0].upper() + filename[1:]
    filename = filename.replace(' ', '_')
    return filename

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
