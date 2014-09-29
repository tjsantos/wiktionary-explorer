import os
import re
import json

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
    """return the first pronunciation section found"""
    regex = r'(^===[^=]+===\s*$)'
    results = re.split(regex, wikitext, flags=re.MULTILINE)
    # find the section for English and save the result
    for i, res in enumerate(results):
        if res.strip() == '===Pronunciation===':
            pronunciation = results[i] + results[i+1]
            break
    else:
        pronunciation = ''
    return pronunciation


def get_ipa(wikitext):
    """return a list of IPA's found"""
    # TODO: possibly match [brackets] ? (phonetic transcriptions)
    # match /slashes/ (phonemic transcriptions in IPA)
    reg = r'IPA\|[^/]*(/[^/]+/)[^}\n]*}'
    ipalist = re.findall(reg, wikitext)
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

def diff_dict(d1, d2):
    """return a dictionary of items in d1 whose key is absent from d2

    >>> d1 = {'a': 'apple', 'b': 'banana'}
    >>> d2 = {'a': 'apple'}
    >>> diff_dict(d1, d2)
    {'b': 'banana'}
    """
    return {key: val for key, val in d1.items() if key not in d2}

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

#if __name__ == '__main__':
#    import sys
#    if len(sys.argv) != 3:
#        print('Expected 2 arguments: infile and outfile.')
#    else:
#        infile, outfile = sys.argv[1:3]
#        parse_xml_to_json(infile, outfile)
