from wikiparser import *
import unittest
import os
import json

class TestParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """set up wikitext examples with expected output for each parser step
        example['word']
        example['text'] -- full wikitext
        example['lang'] -- only the language section
        example['pron'] -- only the pronunciation section of the language
                            section
        example['ipa'] -- only the extracted ipa
        """
        # cls.examples = [{'word': 'foo', 'text': ... }, {'word': ...]
        with open('test/wikitext_examples.json', 'r', encoding='utf-8') as f:
            cls.examples = json.load(f)

    @unittest.skip('will not be using until refactor or next data dump')
    def test_xml_to_wikitext(self):
        test_xml_file = 'test/small.xml'
        test_out = 'test/test.tmp'
        words_found = parse_xml_to_json(test_xml_file, test_out)
        os.remove(test_out)
        words_expected = 19
        self.assertEqual(words_found, words_expected)

    def test_extract_language_section(self):
        for example in self.examples:
            with self.subTest(word=example['word']):
                english = get_english(example['text'])
                # assert to fail on length first, as the string output is long
                self.assertEqual(len(english), len(example['lang']))
                self.assertEqual(english, example['lang'])

    def test_extract_pronunciation_section(self):
        for example in self.examples:
            with self.subTest(word=example['word']):
                pron = get_pronunciation(example['lang'])
                self.assertEqual(pron, example['pron'])

    def test_extract_ipa(self):
        for example in self.examples:
            with self.subTest(word=example['word']):
                ipa = get_ipa(example['pron'])
                self.assertEqual(sorted(ipa), sorted(example['ipa']))
        with self.subTest(word='oxypnictide'):
            pron = "===Pronunciation===\nOXEE-nick-tyde <ref> Space Daily; [http://www.spacedaily.com/reports/Quantum_criticality_observed_in_new_class_of_materials_999.html \"Quantum criticality observed in new class of materials\"]; 5 June 2014 </ref>\n\n"
            ipa = get_ipa(pron)
            self.assertEqual(sorted(ipa), [])
        # catch the 4 correct IPA but neither the link, nor embedded note IPA
        with self.subTest(word='adversary'):
            pron = "===Pronunciation===\n* {{a|UK}} {{IPA|/\u02c8\u00e6d.v\u0259.s(\u0259)\u0279i/|lang=en}}<ref>[http://dictionary.cambridge.org/define.asp?key=1216&amp;dict=CALD Cambridge Advanced Learner's Dictionary]</ref>\n* {{a|UK}} {{IPA|/\u02c8\u00e6d.v\u0259.s\u025b\u0279i/|lang=en}}<ref>According to UK audio file in Longman Exams Dictionary, even though IPA given in dictionary is /\u02c8\u00e6d.v\u0259.s(\u0259)\u0279i\u02d0/</ref>\n* {{a|UK}} {{IPA|/\u00e6d\u02c8v\u025c\u02d0.s\u0259.\u0279i/|lang=en}}\n* {{a|US}} {{IPA|/\u02c8\u00e6d.v\u0259\u0279.s\u025b\u0279i/|lang=en}}\n* {{audio|en-us-adversary.ogg|Audio (US)|lang=en}}\n\n"
            ipa_list = get_ipa(pron)
            expected = ["/\u02c8\u00e6d.v\u0259.s(\u0259)\u0279i/",
                        "/\u02c8\u00e6d.v\u0259.s\u025b\u0279i/",
                        "/\u00e6d\u02c8v\u025c\u02d0.s\u0259.\u0279i/",
                        "/\u02c8\u00e6d.v\u0259\u0279.s\u025b\u0279i/"]
            self.assertEqual(ipa_list, expected)
        # extra section between IPA label and actual IPA
        with self.subTest(word='mishap'):
            pron = "===Pronunciation===\n* {{IPA|lang=en|/\u02c8m\u026as.h\u00e6p/}}\n\n"
            ipa_list = get_ipa(pron)
            expected = ["/\u02c8m\u026as.h\u00e6p/"]
            self.assertEqual(ipa_list, expected)
        # word: hoping
        with self.subTest(word='pecan'):
            pron = "===Pronunciation===\n{{rel-top|Pronunciation}}\n* {{IPA|[\u02ccpi(\u02d0)\u02c8k\u0252\u02d0n]|lang=en}} {{qualifier|pronunciation used by 32% of speakers in the US; common everywhere except New York, New England and the coastal Southeast}}<ref name=\"dialect\">[http://www4.uwm.edu/FLL/linguistics/dialect/staticmaps/q_21.html The Dialect Survey], and [http://spark-1590165977.us-west-2.elb.amazonaws.com/jkatz/SurveyMaps/ Joshua Katz' maps of it]</ref>\n** {{rhymes|\u0252n|lang=en}}\n* {{IPA|[p\u026a.k\u0252\u02d0n]|[\u02ccp\u026a\u02c8k\u0252\u02d0n]|lang=en}} {{qualifier|used by 23% of speakers in the US, mostly in the southern Midwest; also used in the UK}}<ref name=\"dialect\"></ref><ref>{{R:Dictionary.com}}</ref><ref name=COED>\"[http://www.wordreference.com/definition/pecan pecan]\" in the ''Concise Oxford English Dictionary'', 2008, WordReference.com</ref>\n* {{IPA|[\u02c8pi\u02d0\u02cck\u00e6n]|lang=en}} {{qualifier|used by 14% of speakers in the US; common in New York, New England and the coastal Southeast; also used in the UK}}<ref name=\"dialect\"></ref><ref name=Merriam-Webster>{{R:Merriam Webster Online}}</ref><ref>Christopher Davies, ''Divided by a Common Language: A Guide to British and American English'' (2005-7)</ref>\n** {{rhymes|\u00e6n|lang=en}}\n* {{IPA|[\u02c8pi\u02d0\u02cck\u0252(\u02d0)n]|lang=en}} {{qualifier|used by 13% of speakers in the US, mostly in the Upper Midwest}}<ref name=\"dialect\"></ref>\n* {{IPA|[\u02ccpi(\u02d0)\u02c8k\u00e6n]|lang=en}} {{qualifier|used by 7% of speakers in the US, not common in any region}}<ref name=\"dialect\"></ref>\n* {{IPA|[p\u026ak.\u00e6n]|lang=en}} {{qualifier|used almost exclusively in coastal New England, and not the most common pronunciation even there}}<ref name=\"dialect\"></ref>\n* {{IPA|[\u02ccp\u0259\u02c8k\u0254\u02d0n]|[\u02ccp\u026a\u02c8k\u0254\u02d0n]|lang=en}} {{qualifier|used in Louisiana}}<ref>Claude E. Kantner, ''Variant Louisiana pronunciations of the word \"pecan\"'' (1944)</ref>\n* {{IPA|[\u02ccp\u0259\u02c8k\u0252(\u02d0)n]|lang=en}} {{qualifier|sometimes used in the US when the word is unstressed}}<ref name=Merriam-Webster></ref>\n* {{IPA|[\u02ccp\u026a\u02c8k\u00e6n]|lang=en}} {{qualifier|used in the UK; also used by some US speakers}}<ref>Burkhard Dretzke, ''Modern British and American English pronunciation'' (2008)</ref><ref name=Merriam-Webster></ref>\n* {{IPA|[\u02c8pi\u02d0\u02cck\u0259n]|lang=en}} {{qualifier|used in the UK<ref name=COED></ref>}}\n{{rel-bottom}}\n\n"
            ipa_list = get_ipa(pron)
            self.assertEqual(ipa_list, [])
        with self.subTest(word='diddle'):
            pron = "===Pronunciation===\n* {{a|UK}} {{IPA|[\u02c8d\u026ad\u0259\u026b]|lang=en}}\n* {{rhymes|\u026ad\u0259l|lang=en}}\n\n{{examples-right|sense=music|width=300px|examples=<table cellpadding=7>\n  <tr>\n    <td></td><td>Single Paradiddle</td>\n    <td>[[image:16_single_paradiddle.gif]]</td>\n  </tr>\n  <tr>\n    <td></td><td>Double Paradiddle</td>\n    <td>[[image:17_double_paradiddle.gif]]</td>\n  </tr>\n  <tr>\n    <td></td><td>Triple Paradiddle</td>\n    <td>[[image:18_triple_paradiddle.gif]]</td>\n  </tr>\n  <tr>\n    <td></td><td>Paradiddle-Diddle</td>\n    <td>[[image:19_paradiddle_diddle.gif]]</td>\n  </tr>\n</table>\n}}\n\n"
            ipa_list = get_ipa(pron)
            self.assertEqual(ipa_list, [])

        # using lenient matching for everything within /slashes/: r'/[^/]+/'
        # from full english wordlist: 32028 potential ipa, 12806 without
        pronunciation = json_to_dict('s3_pronunciation.json')

        ipa, _ = map_filter_dict(get_ipa, pronunciation)
        ipa_lenient, _ = map_filter_dict(get_ipa_lenient, pronunciation)
        diff = diff_dict(ipa_lenient, ipa)
        self.assertEqual(len(diff), 247)
#        # output diff to tmp file for examination
#        if diff:
#            out = 'test/diff.tmp'
#            with open(out, 'w', encoding='utf-8') as f:
#                json.dump(diff, f, indent=2)
#            print('length of diff:', len(diff))
#        # output new ipa list to tmp file for examination
#        new_ipa_list = [{word: ipa} for word, ipa in with_ipa.items()]
#        out = 'test/new_ipa.tmp'
#        with open(out, 'w', encoding='utf-8') as f:
#            json.dump(new_ipa_list, f, indent=2)

#        import code; code.interact(local=dict(globals(), **locals()))


        ## future possibility: match [brackets] for phonetic transcriptions
        ## as opposed to just the phonemic transcriptions within /slashes/
        # with self.subTest(word='accend'):
        #     pron = ("===Pronunciation===\n"
        #             "* {{IPA|[\u00e6k\u02c8s\u025bnd]|lang=en}}\n\n")
        #     ipa = "[[\u00e6k\u02c8s\u025bnd]]"
        #     self.assertEqual(get_ipa(pron), ipa)


if __name__ == '__main__':
    unittest.main()
