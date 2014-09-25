import re

def parse_xml_to_json(infile, outfile):
    import xml.etree.ElementTree as ET
    def recursive_clear(elem):
        for nested_elem in list(elem):
            recursive_clear(nested_elem)
        elem.clear()

    def make_json(word, text):
        import json
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
    regex = r'(^==[^=]+==$)'
    results = re.split(regex, wikitext, flags=re.MULTILINE)
    # find the section for English and save the result
    for i, res in enumerate(results):
        if res == '==English==':
            english_section = results[i] + results[i+1]
            break
    else:
        english_section = None
    return english_section

def get_pronunciation(wikitext):
    regex = r'(^===[^=]+===$)'
    results = re.split(regex, wikitext, flags=re.MULTILINE)
    # find the section for English and save the result
    for i, res in enumerate(results):
        if res == '===Pronunciation===':
            pronunciation = results[i] + results[i+1]
            break
    else:
        pronunciation = None
    return pronunciation

def get_ipa(wikitext):
    """return a list of IPA's found"""
    results = re.findall(r'/[^/]+/', wikitext)
    # remove duplicates before returning
    ipa_list = []
    for ipa in results:
        if ipa not in ipa_list:
            ipa_list.append(ipa)
    return ipa_list

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        raise RuntimeError('Expected 2 arguments: infile and outfile.')
    infile, outfile = sys.argv[1:3]
    parse_xml_to_json(infile, outfile)
