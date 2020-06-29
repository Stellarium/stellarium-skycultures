#!/usr/bin/python3
# coding: utf-8

# Stellarium Web Engine - Copyright (c) 2020 - Noctua Software Ltd
#
# This program is licensed under the terms of the GNU AGPL v3, or
# alternatively under a commercial licence.
#
# The terms of the AGPL v3 license can be found in the main directory of this
# repository.

import sys
import os.path
import re
import polib
import html
import utils
import argparse

if sys.version_info[0] < 3:
    raise Exception("Please use Python 3 (current is {})".format(
        sys.version_info[0]))

parser = argparse.ArgumentParser()
parser.add_argument("--sky_culture",
                    help="process only for the specified sky culture.")
parser.add_argument("--lang", help="process only for the specified language.")
parser.add_argument("--use_google_translate",
                    help="translate missing text with google translate.",
                    action="store_true")
args = parser.parse_args()

# Set to true to activate auto-translation of missing pieces
# Requires to be logged in to google cloud API, e.g. using
# export GOOGLE_APPLICATION_CREDENTIALS=path to credential.json
USE_GOOGLE_TANSLATE = args.use_google_translate
if USE_GOOGLE_TANSLATE:
    from google.cloud import translate_v2 as translate
    translate_client = translate.Client()

DIR = os.path.abspath(os.path.dirname(__file__))

# Sky cultures with clean descriptions ready to be shipped in SWE
CLEAN_SKYCULTURES = ['belarusian', 'arabic', 'aztec']

# Generate the list of all know common names (in english)
all_english_cn = []
for id, name_data in utils.COMMON_NAMES.items():
    for nd in name_data:
        all_english_cn.append(nd['english'])
all_english_cn = set(all_english_cn)


# Generate a po translation file for the given sky culture.
# legacy is a dict containing existing translations to merge in this po.
def po_for_skyculture(sc, lang, team, legacy):
    po = polib.POFile(encoding='utf-8', check_for_duplicates=True)
    po.metadata = {
        'Project-Id-Version': '1.0',
        'Last-Translator': "Stellarium's developers",
        'Language-Team': team,
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
        'Language': lang
    }

    # Sky Culture title
    entry = polib.POEntry(msgid=sc['name'],
                          msgstr=legacy.get(sc['name'], ''),
                          tcomment="Sky culture name")
    po.append(entry)

    # Sky culture description elements
    for key in utils.SKY_CULTURE_MD_KEYSL:
        if key == 'extras' and key not in sc:
            continue
        entry = polib.POEntry(msgid=sc[key],
                              msgstr=legacy.get(sc[key], ''),
                              tcomment='Sky culture ' + key +
                              ' section in markdown format')
        try:
            po.append(entry)
        except Exception as e:
            print('Error while adding entry for ' + key + ' in sky culture ' +
                  sc['id'])
            print('msgid=' + sc[key] + ' msgstr=' + legacy.get(sc[key], ''))
            raise e

    # Constellation names & descriptions
    prefer_native = False
    if 'langs_use_native_names' in sc:
        # Use the native name as a translation reference string if english
        # is listed as a language using native name. E.g. in the case of
        # the Western sky culture, we want to use "Aquila" as a translatable
        # string for the constellation rather than "Eagle" for most language.
        # The only exception to this rule is for languages such as spanish
        # which also use the latin name as a main constellation name and
        # the translation of the english name as a secondary name. In such case
        # we don't want to translate the latin name (which is not changed) but
        # only the english name.
        prefer_native = ('en' in sc['langs_use_native_names'] and
                         lang not in sc['langs_use_native_names'])

    is_native_lang = False
    if 'native_lang' in sc:
        is_native_lang = lang == sc['native_lang']

    for constel in sc['constellations']:
        id = constel['id']
        notes_id = ''
        if 'common_name' in constel:
            cn = constel['common_name']
            if prefer_native and 'native' in cn:
                english = cn['native']
                if notes_id == '':
                    notes_id = english
            elif 'english' in cn:
                english = cn['english']
                if notes_id == '':
                    notes_id = english
            # Don't add names in po if it already exist in the
            # international common names
            if english in all_english_cn:
                english = ''
            if english:
                tr = legacy.get(english, '')
                if is_native_lang and 'native' in cn:
                    tr = cn['native']
                notes = sc['name'] + ' constellation'
                if 'native' in cn:
                    notes = notes + ', native: ' + cn['native']
                if 'pronounce' in cn:
                    notes = notes + ', pronounce: ' + cn['pronounce']
                entry = polib.POEntry(msgid=english, msgstr=tr, tcomment=notes)
                if entry not in po:
                    po.append(entry)
        if 'description' in constel:
            desc = constel['description']
            tr = legacy.get(desc, '')
            if notes_id == '':
                notes_id = id
            notes = 'Description of ' + sc['name'] + ' constellation ' + notes_id
            entry = polib.POEntry(msgid=desc, msgstr=tr,
                                  tcomment=notes)
            if entry not in po:
                po.append(entry)
    # Other common names
    for id, cns in sc.get('common_names', {}).items():
        for cn in cns:
            if 'english' in cn:
                english_name = cn['english']
            else:
                continue
            if sc['id'] in ['chinese', 'chinese_contemporary']:
                cleaned = english_name
                cleaned = re.sub(' Added', '', cleaned)
                has_added = cleaned != english_name
                cleaned = re.sub(' [MDCLXVI]+$', '', cleaned)
                cleaned_tr = legacy.get(cleaned, '')
                notes = 'Chinese star name for ' + id
                entry = polib.POEntry(msgid=cleaned,
                                      msgstr=cleaned_tr,
                                      tcomment=notes)
                if entry not in po:
                    po.append(entry)

                if has_added:
                    notes = '"Added" chinese star name'
                    added_tr = legacy.get('Added', '')
                    entry = polib.POEntry(
                        msgid='Added',
                        msgstr=added_tr,
                        tcomment=notes)
                    if entry not in po:
                        po.append(entry)
            else:
                # Don't add names in po if it already exist in the
                # international common names
                if english_name in all_english_cn:
                    continue
                tr = legacy.get(english_name, '')
                if is_native_lang and 'native' in cn:
                    tr = cn['native']
                notes = 'Name for ' + id
                entry = polib.POEntry(msgid=english_name, msgstr=tr,
                                      tcomment=notes)
                if entry not in po:
                    po.append(entry)
    return po


# Translate the passed markdown string using google translate
def translate_markdown(str, lang):
    print(str)
    # Convert [#123] refs to something more google translate-friendly
    str = re.sub(r'\[#(\d+)\]', '[RefX\\1]', str)
    # Remove \n in multiline blocs to avoid confusing google translate
    str = re.sub(r'([^\n])\n(?!\d+\.)(\w)', '\\1 \\2', str)
    tr = translate_client.translate(str, target_language=lang,
                                    source_language='en',
                                    format_='text')
    text = tr['translatedText']
    text = html.unescape(text)
    # Re-convert refs to proper format
    text = re.sub(r'\[RefX(\d+)\]', '[#\\1]', text)
    # Fix references lists in japanese
    text = re.sub(r' - \[#(\d+)\]：', ' - [#\\1]: ', text)
    # Fix references lists in korean
    text = re.sub(r' - ?\[#(\d+)\] : ', ' - [#\\1]: ', text)
    # Fix references lists in chinese
    text = re.sub(r' -\[#(\d+)\]：', ' - [#\\1]: ', text)
    # Fix spaces between links parts [xx] (url) -> [xx](url)
    text = re.sub(r'(\[.+\]) (\(\S+\))', '\\1\\2', text)
    text = re.sub(r'(\[.+\])（(\S+)）', '\\1(\\2)', text)
    # Fix spaces for email:links parts [xx] (mailto: url) -> [xx](mailto:url)
    text = re.sub(r'(\[.+\]) \(mailto: (\S+?)\)', '\\1(mailto:\\2)', text)
    text = re.sub(r'(\[.+\])mailto: (\S+)）', '\\1(mailto:\\2)', text)
    # Fix images links extra space
    text = re.sub(r'[！!] ?(\[.*?\]) ?[\(（](\S+?)[\)）]', '!\\1(\\2)', text)
    # Fix extra style content missing space
    text = re.sub(r'{: (.*)}', '{: \\1 }', text)
    text = re.sub(r'{：(.*)}', '{: \\1 }', text)
    # Fix wrongly spaced escaped [
    text = re.sub(r' \\ \[', ' \\[', text)
    text = re.sub(r'\s+\\ \]', '\\]', text)
    text = re.sub(r'\s+\\]', '\\]', text)
    # Re-add space after header ###, useful for asian languages
    text = re.sub(r'^(#+)(?![# ])', '\\1 ', text, flags=re.MULTILINE)
    print(text)
    return text


# Fill-in all missing translations in the passed po using google translate
def auto_translate_po(po):
    lang = po.metadata['Language']
    for entry in po.untranslated_entries():
        tr = translate_markdown(entry.msgid, lang)
        entry.msgstr = tr


def main():
    # Update all po files from the sky culture english content
    sclist = [d for d in os.listdir(DIR) if os.path.isdir(d)]
    sclist.sort()

    if args.sky_culture:
        # The user passed a specific sky culture to process
        sclist = [args.sky_culture]

    for sky_culture in sclist:
        data_path = os.path.join(DIR, sky_culture)
        index_file = os.path.join(data_path, 'index.json')
        if not os.path.exists(index_file):
            continue

        print('Processing ' + sky_culture)
        sc = utils.load_skyculture(data_path)

        langs = []
        if args.lang:
            langs = [args.lang]
            print('only in ' + langs[0])
        else:
            for filename in os.listdir(os.path.join(data_path, 'po')):
                langs.append(filename.replace('.po', ''))
        for lang in langs:
            # Load existing translations
            current_po_path = os.path.join(data_path, 'po', '%s.po' % lang)
            current_po = None
            legacy = {}
            try:
                current_po = polib.pofile(current_po_path)
                team = current_po.metadata['Language-Team']
                for entry in current_po.translated_entries():
                    legacy[entry.msgid] = entry.msgstr
            except:
                print('Error while loading po file for language ' + lang)

            # Generate a brand new po file from sky culture content, and
            # merge existing translations.
            po_md = po_for_skyculture(sc, lang, team, legacy)

            # Complete missing translations using Google Translate service
            if (USE_GOOGLE_TANSLATE
                    and lang in utils.OFFICIAL_LANGS
                    and sc['id'] != 'lokono'):
                auto_translate_po(po_md)

            # Replace the current source po file
            po_md.save(current_po_path)


if __name__ == '__main__':
    main()
