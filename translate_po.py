#!/usr/bin/python3

# Stellarium
# Copyright (C) 2025 - Stellarium Labs SRL
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Suite 500, Boston, MA  02110-1335, USA.

# Translate a .po file by filling in the missing msgstr entries
#
# Need to export OPENAI_API_KEY='your API key' environment variable
# before running.

import os
import sys
import polib
import argparse
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI(api_key=api_key)

parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Translations file to process")
parser.add_argument("--skip-existing", help="Skip entries with non-empty msgstr", action="store_true")
args = parser.parse_args()

lang_names = {
"ar"        : "Arabic",
"cs"        : "Czech",
"de"        : "German",
"es"        : "Spanish",
"fil"       : "Filipino",
"fr"        : "French",
"id"        : "Indonesian",
"it"        : "Italian",
"ja"        : "Japanese",
"ko"        : "Korean",
"nl"        : "Dutch",
"pl"        : "Polish",
"pt"        : "Portuguese",
"ru"        : "Russian",
"tr"        : "Turkish",
"zh_CN"     : "Chinese (simplified)",
"zh_TW"     : "Chinese (traditional)",
}
if not args.filename.endswith(".po"):
    print("Unexpected file name, should be <locale>.po, where <locale> is the locale id", file=sys.stderr)
    sys.exit(1)

lang = os.path.basename(args.filename)
lang = lang[:len(lang)-3] # strip the .po
lang_name = lang_names[lang]

pofile = polib.pofile(args.filename)
for entry in pofile:
    if entry.msgstr and args.skip_existing:
        continue

    system_prompt = f"""
You are a professional technical translator for an astronomy mobile application Stellarium Mobile. You are translating names and texts in a sky culture.
Your priorities, in order:

 1. When a comment for translator tells that the text is in Markdown, preserve Markdown structure exactly—do not add, remove, or reorder sections, HTML tags, or any similar syntactically significant entities.
 2. Use domain-correct terminology for astronomy. Prefer established terms in the target locale over literal word-for-word renderings.
 3. Produce grammatically correct translations, following the expected noun cases, singular/plural forms etc.
 4. If a name is a "pronounce" entry as specified in the comment for translator, use the most appropriate transliteration in the target language. E.g. "al-Thurayya" in an Arabic sky culture will become "ас-Сурайя" in Russian and "al-Suraja" in Polish.

## Style & locale rules

 * Target language: {lang_name}.
 * Keep URLs and query strings unchanged.
 * Keep reference numbers like [#1], [#2] etc. verbatim.
 * Keep punctuation, lists, and capitalization natural for the target locale.
 * Use locale-appropriate astronomy terms (e.g., constellations, planets, asterisms, equatorial/alt-az coordinates, magnitude, FOV, RA/Dec, epoch J2000).
 * Numbers/units: preserve numeric values; convert units only if explicitly asked; keep degree symbol, arcmin/arcsec, and time formats as in source unless clearly unnatural in the locale.

## HTML constraints

 * Preserve inline math, Greek letters, and entities (e.g., &alpha;, &deg;, &#x2605;).

## Output requirements

 * Return only the translated result (no explanations).
 * Maintain original whitespace and indentation where reasonable.
"""

    user_prompt = f"""
Translate the following Stellarium Mobile sky culture string starting after "TEXT TO TRANSLATE:" to {lang_name}. Follow all system instructions. Take into account the comment for translator (marked with "COMMENT FOR TRANSLATOR:"; may happen to be empty).

COMMENT FOR TRANSLATOR:
{entry.comment}

TEXT TO TRANSLATE:
{entry.msgid}
"""
    try:
        print(f'Translating "{entry.msgid[:100]}"... to {lang_name}...', file=sys.stderr)
        response = openai_client.responses.create(model='gpt-5', input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}])
        txt = response.output_text.strip()
        entry.msgstr = txt
        entry.tcomment = "Translated by OpenAI, may be very wrong"
    except Exception as e:
        print("Error translating text: %s", str(e))
        sys.exit(1)

    pofile.save(args.filename)

pofile.save(args.filename)
