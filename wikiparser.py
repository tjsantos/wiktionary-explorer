import json
import os
import re
import string
import sys

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


def get_ipa(wikitext):
    """return a list of IPA's found"""
    # TODO: possibly match [brackets] ? (phonetic transcriptions)
    # match /slashes/ (phonemic transcriptions in IPA)
    #reg = r'IPA\|[^/]*(/[^/]+/)[^}\n]*}'
    ipalist = []
    #reg = r'IPA(?:[^/]*(/[^/]+/))+.*?}'
    reg_template = r'{{.*?}}'
    reg_ipa = r'/.*?/'
    for line in wikitext.splitlines():
        for template in re.findall(reg_template, line):
            if 'IPA' in template:
                ipalist += re.findall(reg_ipa, template)
    return ipalist

def get_ipa_lenient(wikitext):
    reg = r'/[^/]+/'
    ipalist = re.findall(reg, wikitext)
    return ipalist

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
    steps = ['text', 'lang', 'pron', 'ipa']
    assert start in steps and end in steps, 'steps: {}'.format(steps)
    # track the next step in the pipeline and parse appropriately
    n = steps.index(start) + 1
    end_n = steps.index(end)
    while n <= end_n:
        step_from = steps[n-1]
        step_to = steps[n]
        print(step_from, 'to', step_to)
        wikidict = json_load(step_from + '.json')
        map_function = map_functions[steps[n]]
        hit, miss = map_filter_dict(map_function, wikidict)
        print(len(hit), 'hits,', len(miss), 'misses')
        json_dump(hit, step_to + '.json')
        json_dump(miss, 'no_' + step_to + '.json')
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
