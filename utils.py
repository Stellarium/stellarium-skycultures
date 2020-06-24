#!/usr/bin/python3
# coding: utf-8

# Stellarium Web Engine - Copyright (c) 2020 - Noctua Software Ltd
#
# This program is licensed under the terms of the GNU AGPL v3, or
# alternatively under a commercial licence.
#
# The terms of the AGPL v3 license can be found in the main directory of this
# repository.

import os
import re
import json
import copy
import uuid

DIR = os.path.abspath(os.path.dirname(__file__))

# Languages officially supported by SWE
OFFICIAL_LANGS = ['ar', 'de', 'es', 'fr', 'it', 'ja', 'ko', 'pl', 'pt', 'ru',
                  'zh_TW', 'zh_CN', 'cs', 'nl']


def get_common_names():
    res = {}
    current_id = ''
    current_ninfo = None
    with open(DIR + '/common_names.tab', 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            fields = [ff.strip() for ff in line.strip().split('|')]
            ninfo = {
                'english': fields[1]
            }
            if fields[2]:
                ninfo['wikipedia_title'] = fields[2]
            if fields[3]:
                ninfo['model'] = fields[3]
            if fields[4]:
                ninfo['sources'] = fields[4].split(',')
            if fields[5]:
                ninfo['notes'] = fields[5]

            if fields[0] == current_id:
                current_ninfo.append(ninfo)
            else:
                if current_ninfo:
                    # Save previously read names
                    res[current_id] = current_ninfo
                current_ninfo = [ninfo]
                current_id = fields[0]
        # Save last read names
        res[current_id] = current_ninfo
    return res


COMMON_NAMES = get_common_names()
COMMON_NAMES_KEYS = set(COMMON_NAMES.keys())


def dumps_sky_culture_json(sc):
    class NoIndent(object):
        def __init__(self, value):
            self.value = value

        def append(self, v):
            self.value.append(v)

    class NoIndentEncoder(json.JSONEncoder):
        '''JSON encoder that doesn't indent NoIndent values
           See: https://stackoverflow.com/a/13249927/355230'''

        def __init__(self, *args, **kwargs):
            super(NoIndentEncoder, self).__init__(*args, **kwargs)
            self.kwargs = dict(kwargs)
            del self.kwargs['indent']
            self._replacement_map = {}

        def default(self, o):
            if isinstance(o, NoIndent):
                key = uuid.uuid4().hex
                self._replacement_map[key] = json.dumps(o.value, **self.kwargs)
                return "@@%s@@" % (key,)
            else:
                return super(NoIndentEncoder, self).default(o)

        def encode(self, o):
            result = super(NoIndentEncoder, self).encode(o)
            for k, v in self._replacement_map.items():
                result = result.replace('"@@%s@@"' % (k,), v)
            return result

    sc = copy.deepcopy(sc)
    if 'langs_use_native_names' in sc:
        sc['langs_use_native_names'] = NoIndent(sc['langs_use_native_names'])
    if 'common_names' in sc:
        cn2 = {}
        for k, val in sc['common_names'].items():
            cn2[k] = NoIndent(val)
        sc['common_names'] = cn2

    for feature in sc['constellations']:
        if 'lines' in feature:
            feature['lines'] = NoIndent(feature['lines'])
        if 'image' in feature:
            feature['image']['anchors'] = [NoIndent(x) for x in
                                           feature['image']['anchors']]
            feature['image']['size'] = NoIndent(feature['image']['size'])
        if 'common_name' in feature:
            feature['common_name'] = NoIndent(feature['common_name'])

    return json.dumps(sc, indent=2, ensure_ascii=False, cls=NoIndentEncoder)


SKY_CULTURE_MD_KEYS = ['Introduction', 'Description', 'Extras', 'References',
                       'Authors', 'Licence']
SKY_CULTURE_MD_KEYSL = [k.lower() for k in SKY_CULTURE_MD_KEYS]


# Parse a sky culture markdown description file
def parse_skyculture_markdown(description_file):
    def feature_text_to_dict(text):
        ret = {}
        desc = ''
        for line in iter(text.splitlines()):
            m = re.match(r'^ *- *(english|pronounce|native):(.*)$', line)
            if m:
                ret[m.group(1)] = m.group(2).strip()
            else:
                desc += line + '\n'
        if desc:
            ret['description'] = desc.strip()
        return ret

    ret = {}
    with open(description_file, 'r', encoding='utf8') as f:
        sc = {}
        # Read name from markdown
        md = f.readline()
        m = re.match(r'^#\s*(.+)$', md, re.MULTILINE)
        if not m:
            print('Error in sky culture ' + sc['id'] +
                  ': md file must start with # Sky Culture Name')
        ret['name'] = m.group(1)

        # Read all other sections
        md = f.read()
        m = re.split(r'^##\s+(.*)\n', md, 0, re.MULTILINE)
        sections = {}
        section_title = ''
        if m[0] == '':
            m.pop(0)
        for s in m:
            if section_title:
                sections[section_title] = s.strip('\n')
                section_title = ''
            else:
                section_title = s.strip()

        if 'Constellations' in sections:
            constellations_text = sections['Constellations']
            del sections['Constellations']

            m = re.split(r'^#####\s+(.*)\n', constellations_text, 0,
                re.MULTILINE)
            features = {}
            feature_id = ''
            if m[0] == '':
                m.pop(0)
            for s in m:
                s = s.strip()
                if feature_id:
                    features[feature_id] = s
                    feature_id = ''
                else:
                    feature_id = s
            celestial_objects = {}
            for (id, text) in features.items():
                celestial_objects[id] = feature_text_to_dict(text)
            ret['constellations'] = celestial_objects

        for key in sections.keys():
            if key not in SKY_CULTURE_MD_KEYS:
                print('Error in sky culture description, forbidden section: ' +
                      key)
                print('Only allowed are: ' + ', '.join(SKY_CULTURE_MD_KEYS) +
                      ' and Constellations')
                assert(0)

        for key in sections.keys():
            ret[key.lower()] = sections[key]
    return ret


# Load the sky culture from the given directory
def load_skyculture(path):
    def find_constellation(sc, name):
        for c in sc['constellations']:
            if c['id'] == name:
                return c
            cn = c['common_name']
            if cn.get('english', '') == name:
                return c
            if cn.get('pronounce', '') == name:
                return c
            if cn.get('native', '') == name:
                return c
        return None

    index_file = os.path.join(path, 'index.json')
    description_file = os.path.join(path, 'description.md')
    sc = None

    with open(index_file, 'r', encoding='utf8') as f:
        sc = json.load(f)

    md_sc = parse_skyculture_markdown(description_file)
    if 'constellations' in md_sc:
        md_constellations = md_sc.get('constellations', [])
        del md_sc['constellations']
        for md_coid, md_codata in md_constellations.items():
            co = find_constellation(sc, md_coid)
            if co:
                if 'description' in md_codata:
                    co['description'] = md_codata['description']
                if 'pronounce' in md_codata:
                    co['common_name']['pronounce'] = md_codata['pronounce']
                if 'english' in md_codata:
                    co['common_name']['english'] = md_codata['english']
                if 'native' in md_codata:
                    co['common_name']['native'] = md_codata['native']
            else:
                print('Error: cannot find constellation ' + md_coid +
                      ' in sky culture ' + sc['id'])

    for key in md_sc.keys():
        sc[key] = md_sc[key]

    return sc
