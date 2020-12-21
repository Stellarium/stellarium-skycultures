#!/usr/bin/env python3

from _ctypes import PyObj_FromPtr
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord, Angle
from astropy import units as u
import sys
import re
import percache
import os
import json
from collections import defaultdict

constellation_map = {
  "And": "Andromeda",
  "Ant": "Antlia",
  "Aps": "Apus",
  "Aql": "Aquila",
  "Aqr": "Aquarius",
  "Ara": "Ara",
  "Ari": "Aries",
  "Aur": "Auriga",
  "Boo": "Bootes",
  "CMa": "Canis Major",
  "CMi": "Canis Minor",
  "CVn": "Canes Venatici",
  "Cae": "Caelum",
  "Cam": "Camelopardalis",
  "Cap": "Capricornus",
  "Car": "Carina",
  "Cas": "Cassiopeia",
  "Cen": "Centaurus",
  "Cep": "Cepheus",
  "Cet": "Cetus",
  "Cha": "Chamaeleon",
  "Cir": "Circinus",
  "Cnc": "Cancer",
  "Col": "Columba",
  "Com": "Coma Berenices",
  "CrA": "Corona Australis",
  "CrB": "Corona Borealis",
  "Crt": "Crater",
  "Cru": "Crux",
  "Crv": "Corvus",
  "Cyg": "Cygnus",
  "Del": "Delphinus",
  "Dor": "Dorado",
  "Dra": "Draco",
  "Equ": "Equuleus",
  "Eri": "Eridanus",
  "For": "Fornax",
  "Gem": "Gemini",
  "Gru": "Grus",
  "Her": "Hercules",
  "Hor": "Horologium",
  "Hya": "Hydra",
  "Hyi": "Hydrus",
  "Ind": "Indus",
  "LMi": "Leo Minor",
  "Lac": "Lacerta",
  "Leo": "Leo",
  "Lep": "Lepus",
  "Lib": "Libra",
  "Lup": "Lupus",
  "Lyn": "Lynx",
  "Lyr": "Lyra",
  "Men": "Mensa",
  "Mic": "Microscopium",
  "Mon": "Monoceros",
  "Mus": "Musca",
  "Nor": "Norma",
  "Oct": "Octans",
  "Oph": "Ophiuchus",
  "Ori": "Orion",
  "Pav": "Pavo",
  "Peg": "Pegasus",
  "Per": "Perseus",
  "Phe": "Phoenix",
  "Pic": "Pictor",
  "PsA": "Piscis Austrinus",
  "Psc": "Pisces",
  "Pup": "Puppis",
  "Pyx": "Pyxis",
  "Ret": "Reticulum",
  "Scl": "Sculptor",
  "Sco": "Scorpius",
  "Sct": "Scutum",
  "Ser": "Serpens",
  "Sex": "Sextans",
  "Sge": "Sagitta",
  "Sgr": "Sagittarius",
  "Tau": "Taurus",
  "Tel": "Telescopium",
  "TrA": "Triangulum Australe",
  "Tri": "Triangulum",
  "Tuc": "Tucana",
  "UMa": "Ursa Major",
  "UMi": "Ursa Minor",
  "Vel": "Vela",
  "Vir": "Virgo",
  "Vol": "Volans",
  "Vul": "Vulpecula"
}

# https://stackoverflow.com/questions/13249415/how-to-implement-custom-indentation-when-pretty-printing-with-the-json-module
class NoIndent(object):
    """ Value wrapper. """
    def __init__(self, value):
        self.value = value

# https://stackoverflow.com/questions/13249415/how-to-implement-custom-indentation-when-pretty-printing-with-the-json-module
class MyEncoder(json.JSONEncoder):
    FORMAT_SPEC = '@@{}@@'
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))

    def __init__(self, **kwargs):
        # Save copy of any keyword argument values needed for use here.
        self.__sort_keys = kwargs.get('sort_keys', None)
        super(MyEncoder, self).__init__(**kwargs)

    def default(self, obj):
        return (self.FORMAT_SPEC.format(id(obj)) if isinstance(obj, NoIndent)
                else super(MyEncoder, self).default(obj))

    def encode(self, obj):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.
        json_repr = super(MyEncoder, self).encode(obj)  # Default JSON.

        # Replace any marked-up object ids in the JSON repr with the
        # value returned from the json.dumps() of the corresponding
        # wrapped Python object.
        for match in self.regex.finditer(json_repr):
            # see https://stackoverflow.com/a/15012814/355230
            id = int(match.group(1))
            no_indent = PyObj_FromPtr(id)
            json_obj_repr = json.dumps(no_indent.value, sort_keys=self.__sort_keys)

            # Replace the matched id string with json formatted representation
            # of the corresponding Python object.
            json_repr = json_repr.replace(
                            '"{}"'.format(format_spec.format(id)), json_obj_repr)

        return json_repr

def snt_data():
    """
    Reads data from the STDIN and returns a generator that
    returns a dict with each field parsed out.
    """
    #                              mag           ra          npd             bayer              sup       weight    cons
    data_regex = re.compile(r'([0-9\. -]{5}) ([0-9\. ]{8}) ([0-9\. ]{8}) ([A-Za-z0-9 -]{3})([a-zA-Z0-9 ])([0-9])([a-zA-Z]{3})')
    for line in sys.stdin:
        line = line.rstrip('\n\r')
        m = re.match(data_regex, line)

        if m:
            # The S&T data has "Erj" as the continuation of Eridanus
            # after pi.  This is because the S&T data has a gap around
            # pi, since it lies slightly within Cetus.  S&T's own line
            # drawing software requires that one of the last four characters
            # change to signify a new line is to be started, rather than
            # continuing from the previous point.  So they had to create
            # a "fake" constellation to make their line drawing software
            # start a new line after pi.  Hence 'Erj'.
            constellation = m.group(7)
            if constellation == 'Erj':
                constellation = 'Eri'

            yield {
                "mag": float(m.group(1).strip()),
                "ra": round(float(m.group(2).strip()), 5),
                "npd": round(float(m.group(3).strip()), 4),
                "dec": round(90 - float(m.group(3).strip()), 4),
                "bayer": m.group(4).strip(),
                "superscript": None if m.group(5) == " " else m.group(5),
                "weight": int(m.group(6)),
                "constellation": constellation,
            }
        else:
            if not line.startswith('#'):
                print("WARNING: No match: {}".format(line), file=sys.stderr) # lgtm [py/syntax-error]

# livesync=True so that even if we ctrl-c out of
# the program, any previously cached values will
# be present for future invocations
cache = percache.Cache('.hip_cache', livesync=True)
@cache
def get_hip(ra, dec, mag):
    """
    Given an RA (in hours and decimals), and Dec (in
    degrees and decimals), and a magnitude (in
    visual magnitudes), queries VizieR and attempts
    to locate a Hipparcos star ID at the location.

    Returns an integer HIP ID if found, or None otherwise

    Maintains a .hip_cache file to speed up lookups;
    you can delete the .hip_cache file to perform
    fresh lookups.
    """
    coord = SkyCoord(ra=Angle("{} hours".format(ra)),
                     dec=Angle("{} degree".format(dec)),
                     obstime="J2000.0")

    # Search the Hipparcos catalog, and only return results that include
    # a HIP (Hipparcos) column, sorting the results by magnitude.  The
    # top result is almost certainly the star we want.
    v = Vizier(catalog='I/239/hip_main', columns=["HIP", "+Vmag"])
    # Constrain the search to stars within 1 Vmag of our target
    v.query_constraints(Vmag="{}..{}".format(mag - 0.5, mag + 0.5))

    # Start with a targeted search, which returns more quickly from the
    # API. If that fails to find a star, query a 3 degree diameter circle
    # around the ra/dec.  This is because Sky & Telescope has a convention
    # of stopping their constellation lines a degree or so away from the
    # star, if that star isn't actually part of the constellation
    # (example: Alpheratz, which is part of the Pegasus figure, but the
    # star is in Andromeda)
    for radius in (0.05, 1.5):
        result = v.query_region(coord, radius=radius*u.deg)
        try:
            table = result['I/239/hip_main']
        except TypeError:
            # A TypeError means that the results didn't include anything from
            # the I/239/hip_main catalog.  The "in" operator doesn't seem to
            # work with Table objects.
            continue
        else:
            # There seems to be a bug in the Hipparcos catalog in VizieR for
            # Xi UMa (Alula Australis).  No matter how you query the region
            # it never seems to return that star.  It's in the catalog, but
            # I can't figure out how to get a query to return it without
            # just specifying its ID.  So this just overrides that one star.
            # See https://github.com/Stellarium/stellarium/issues/1414
            if table['HIP'][0] == 55302:
                return 55203
            else:
                return table['HIP'][0]
    return None

class Line():
    def __init__(self, constellation, weight):
        '''
        constellation: the short name, Ori, Lyn, etc.
        weight: line weight, 1=heaviest, 4=lightest
        '''
        self.constellation = constellation
        self.weight = weight
        self.vertices = [ ]

    def add_vertex(self, hip):
        '''
        Add a vertex to the line.  Every vertex is a Hipparcos star ID.
        '''
        self.vertices.append(int(hip))

    def generate_paths(self, use_weight=True):
        '''
        Generate the path array for this line.
        This will be an array of arrays.
        If use_weight=True, then the same path array
        will be repeated some number of times based on
        the weight of this line:
          4 = 1x (lightest)
          3 = 2x
          2 = 3x
          1 = 4x (heaviest)
        '''
        repeat = 1
        ret = [ [*self.vertices] ]
        if use_weight:
            for i in range(4 - self.weight):
                ret.append([*self.vertices])
        return ret

    def __str__(self):
        return f"{self.weight}[" + ",".join(f"{i}" for i in self.vertices) + "]"

if __name__ == '__main__':
    exitval = 0
    # Each item in the constellations dict is a list of Line objects
    constellations = defaultdict(list)
    current_line = None
    previous_line = None
    current_hip = None
    previous_hip = None
    try:
        for vertex in snt_data():
            # The line weight and constellation, taken together, indicate
            # one continuous line.  If this value changes, we start a new line.
            previous_line = current_line
            previous_hip = current_hip
            current_line = "{weight}{constellation}".format(**vertex)

            print("{bayer} {constellation} [ra={ra}, dec={dec}, mag={mag}]...".format(**vertex), file=sys.stderr, end='', flush=True)
            # The S&T data is ambiguous for the location of the o2 (31) Cyg vertex,
            # so we skip get_hip and assign it manually.
            if vertex['constellation'] == 'Cyg' and vertex['bayer'] == '31-':
                current_hip = 99848
            else:
                current_hip = get_hip(ra=vertex['ra'], dec=vertex['dec'], mag=vertex['mag'])
            if not current_hip:
                raise ValueError("Unable to locate HIP for {bayer} {constellation} vertex [ra={ra}, dec={dec}, mag={mag}]".format(**vertex))
            print("HIP {}".format(current_hip), file=sys.stderr, flush=True)

            if previous_line != current_line:
                # If we are on a new line, append a new Line object to the constellation
                constellations[vertex['constellation']].append(Line(constellation=vertex['constellation'], weight=vertex['weight']))

            # Append the vertex to the last line path of the constellation
            constellations[vertex['constellation']][-1].add_vertex(current_hip)

    except KeyboardInterrupt:
        # If the user hits ctrl+c during processing, don't just abort; continue
        # on to output the constellationship data that was already gathered,
        # then exit non-zero.
        exitval = 1
        print("Caught KeyboardInterrupt", file=sys.stderr)

    # Special case for Mensa and Microscopium constellations (without lines!)
    constellations['Men'].append(Line(constellation='Men', weight=1))
    constellations['Men'][-1].add_vertex(26264)
    constellations['Men'][-1].add_vertex(26264)
    constellations['Mic'].append(Line(constellation='Mic', weight=1))
    constellations['Mic'][-1].add_vertex(103882)
    constellations['Mic'][-1].add_vertex(103882)

    print("Generating constellation data...", file=sys.stderr)
    output_json = { "constellations": [ ] }
    for constellation in sorted(constellations.keys()):
        print("{} {} {} {}".format(constellation, constellation_map[constellation], len(constellations[constellation]), " ".join(f"{i}" for i in constellations[constellation])), file=sys.stderr)
        segments = [ ]
        for l in constellations[constellation]:
            segments.extend(l.generate_paths())
        output_json["constellations"].append({
            "id": f"CON western_SnT {constellation}",
            "common_name": NoIndent({"english":constellation_map[constellation]}),
            "lines": NoIndent(segments)
        })

    print(json.dumps(output_json, cls=MyEncoder, indent=2, sort_keys=True))
    sys.exit(exitval)
