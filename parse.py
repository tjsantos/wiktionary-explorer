
def parse_xml_to_json(infile, outfile):
    import xml.etree.ElementTree as ET
    def recursive_clear(elem):
        for nested_elem in list(elem):
            recursive_clear(nested_elem)
        elem.clear()

    def make_json(word, text):
        import json
        return json.dumps({'word': word, 'text': text})

    f = infile
    elems = ET.iterparse(f)
    ns = '{http://www.mediawiki.org/xml/export-0.9/}'

    errors = []
    words = []
    n = 0
    with open(outfile, 'w', encoding='utf-8') as out:
        out.write('[\n')
        for event, elem in ET.iterparse(f):
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

            #print(i, tag, elem.text[:20] if elem.text else None)
            # obtain words
            if tag == 'page':
                n += 1
                # words are assumed to have ns = 0
                if elem.find(ns+'ns').text == '0':
                    word = elem.find('./{0}title'.format(ns)).text
                    text = elem.find('./{0}revision/{0}text'.format(ns)).text
                    if text.find('==English==') != -1:
                        words.append(word)
                        out.write(make_json(word, text) + ',\n')
                # clear page from memory
                recursive_clear(elem)

            #if n % 100000 == 0:
            #    print(n, len(words))
        out.write(make_json('', ''))
        out.write('\n]')
    print(len(words))
    print(errors)
    return len(words)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        raise RuntimeError('Expected 2 arguments: infile and outfile.')
    infile, outfile = sys.argv[1:3]
    parse_xml_to_json(infile, outfile)
