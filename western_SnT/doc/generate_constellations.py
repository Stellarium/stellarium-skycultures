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

# Extracted from the included SnT_star_names.docx provided by Sky & Telescope
star_common_names = {
    "HIP 677": [{"english": "Alpheratz"},{"native": "Alpheratz"}],
    "HIP 746": [{"english": "Caph"},{"native": "Caph"}],
    "HIP 1067": [{"english": "Algenib"},{"native": "Algenib"}],
    "HIP 2081": [{"english": "Ankaa"},{"native": "Ankaa"}],
    "HIP 3179": [{"english": "Schedar"},{"native": "Schedar"}],
    "HIP 3419": [{"english": "Deneb Kaitos"},{"native": "Deneb Kaitos"}],
    "HIP 5447": [{"english": "Mirach"},{"native": "Mirach"}],
    "HIP 6411": [{"english": "Adhil"},{"native": "Adhil"}],
    "HIP 6686": [{"english": "Ruchbah"},{"native": "Ruchbah"}],
    "HIP 7588": [{"english": "Achernar"},{"native": "Achernar"}],
    "HIP 8645": [{"english": "Baten Kaitos"},{"native": "Baten Kaitos"}],
    "HIP 8796": [{"english": "Mothallah"},{"native": "Mothallah"}],
    "HIP 8832": [{"english": "Mesartim"},{"native": "Mesartim"}],
    "HIP 8903": [{"english": "Sheratan"},{"native": "Sheratan"}],
    "HIP 9487": [{"english": "Alrescha"},{"native": "Alrescha"}],
    "HIP 9640": [{"english": "Almach"},{"native": "Almach"}],
    "HIP 9884": [{"english": "Hamal"},{"native": "Hamal"}],
    "HIP 10826": [{"english": "Mira"},{"native": "Mira"}],
    "HIP 11767": [{"english": "Polaris"},{"native": "Polaris"}],
    "HIP 13701": [{"english": "Azha"},{"native": "Azha"}],
    "HIP 13847": [{"english": "Acamar"},{"native": "Acamar"}],
    "HIP 14135": [{"english": "Menkar"},{"native": "Menkar"}],
    "HIP 14576": [{"english": "Algol"},{"native": "Algol"}],
    "HIP 14838": [{"english": "Botein"},{"native": "Botein"}],
    "HIP 15197": [{"english": "Zibal"},{"native": "Zibal"}],
    "HIP 15863": [{"english": "Mirfak"},{"native": "Mirfak"}],
    "HIP 17448": [{"english": "Atik"},{"native": "Atik"}],
    "HIP 17489": [{"english": "Celaeno"},{"native": "Celaeno"}],
    "HIP 17499": [{"english": "Electra"},{"native": "Electra"}],
    "HIP 17531": [{"english": "Taygeta"},{"native": "Taygeta"}],
    "HIP 17573": [{"english": "Maia"},{"native": "Maia"}],
    "HIP 17579": [{"english": "Sterope"},{"native": "Sterope"}],
    "HIP 17608": [{"english": "Merope"},{"native": "Merope"}],
    "HIP 17702": [{"english": "Alcyone"},{"native": "Alcyone"}],
    "HIP 17847": [{"english": "Atlas"},{"native": "Atlas"}],
    "HIP 17851": [{"english": "Pleione"},{"native": "Pleione"}],
    "HIP 18543": [{"english": "Zaurak"},{"native": "Zaurak"}],
    "HIP 18614": [{"english": "Menkib"},{"native": "Menkib"}],
    "HIP 19587": [{"english": "Beid"},{"native": "Beid"}],
    "HIP 19849": [{"english": "Keid"},{"native": "Keid"}],
    "HIP 20535": [{"english": "Theemin"},{"native": "Theemin"}],
    "HIP 20889": [{"english": "Ain"},{"native": "Ain"}],
    "HIP 21421": [{"english": "Aldebaran"},{"native": "Aldebaran"}],
    "HIP 23203": [{"english": "Hind's Crimson Star"},{"native": "Hind's Crimson Star"}],
    "HIP 23875": [{"english": "Cursa"},{"native": "Cursa"}],
    "HIP 24436": [{"english": "Rigel"},{"native": "Rigel"}],
    "HIP 24608": [{"english": "Capella"},{"native": "Capella"}],
    "HIP 25336": [{"english": "Bellatrix"},{"native": "Bellatrix"}],
    "HIP 25428": [{"english": "Elnath"},{"native": "Elnath"}],
    "HIP 25606": [{"english": "Nihal"},{"native": "Nihal"}],
    "HIP 25930": [{"english": "Mintaka"},{"native": "Mintaka"}],
    "HIP 25985": [{"english": "Arneb"},{"native": "Arneb"}],
    "HIP 26207": [{"english": "Meissa"},{"native": "Meissa"}],
    "HIP 26311": [{"english": "Alnilam"},{"native": "Alnilam"}],
    "HIP 26634": [{"english": "Phact"},{"native": "Phact"}],
    "HIP 26727": [{"english": "Alnitak"},{"native": "Alnitak"}],
    "HIP 27366": [{"english": "Saiph"},{"native": "Saiph"}],
    "HIP 27628": [{"english": "Wazn"},{"native": "Wazn"}],
    "HIP 27989": [{"english": "Betelgeuse"},{"native": "Betelgeuse"}],
    "HIP 28360": [{"english": "Menkalinan"},{"native": "Menkalinan"}],
    "HIP 29655": [{"english": "Propus"},{"native": "Propus"}],
    "HIP 30122": [{"english": "Furud"},{"native": "Furud"}],
    "HIP 30324": [{"english": "Mirzam"},{"native": "Mirzam"}],
    "HIP 30343": [{"english": "Tejat"},{"native": "Tejat"}],
    "HIP 30438": [{"english": "Canopus"},{"native": "Canopus"}],
    "HIP 31681": [{"english": "Alhena"},{"native": "Alhena"}],
    "HIP 32246": [{"english": "Mebsuta"},{"native": "Mebsuta"}],
    "HIP 32349": [{"english": "Sirius"},{"native": "Sirius"}],
    "HIP 33579": [{"english": "Adhara"},{"native": "Adhara"}],
    "HIP 34045": [{"english": "Muliphein"},{"native": "Muliphein"}],
    "HIP 34088": [{"english": "Mekbuda"},{"native": "Mekbuda"}],
    "HIP 34444": [{"english": "Wezen"},{"native": "Wezen"}],
    "HIP 35550": [{"english": "Wasat"},{"native": "Wasat"}],
    "HIP 35904": [{"english": "Aludra"},{"native": "Aludra"}],
    "HIP 36188": [{"english": "Gomeisa"},{"native": "Gomeisa"}],
    "HIP 36850": [{"english": "Castor"},{"native": "Castor"}],
    "HIP 37279": [{"english": "Procyon"},{"native": "Procyon"}],
    "HIP 37826": [{"english": "Pollux"},{"native": "Pollux"}],
    "HIP 39429": [{"english": "Naos"},{"native": "Naos"}],
    "HIP 39757": [{"english": "Tureis"},{"native": "Tureis"}],
    "HIP 39953": [{"english": "Regor"},{"native": "Regor"}],
    "HIP 40167": [{"english": "Tegmine"},{"native": "Tegmine"}],
    "HIP 41037": [{"english": "Avior"},{"native": "Avior"}],
    "HIP 41704": [{"english": "Muscida"},{"native": "Muscida"}],
    "HIP 42806": [{"english": "Asellus Borealis"},{"native": "Asellus Borealis"}],
    "HIP 42911": [{"english": "Asellus Australis"},{"native": "Asellus Australis"}],
    "HIP 44066": [{"english": "Acubens"},{"native": "Acubens"}],
    "HIP 44127": [{"english": "Talitha"},{"native": "Talitha"}],
    "HIP 44368": [{"english": "Vela X-1"},{"native": "Vela X-1"}],
    "HIP 44816": [{"english": "Suhail"},{"native": "Suhail"}],
    "HIP 45238": [{"english": "Miaplacidus"},{"native": "Miaplacidus"}],
    "HIP 45556": [{"english": "Aspidiske"},{"native": "Aspidiske"}],
    "HIP 45941": [{"english": "Markeb"},{"native": "Markeb"}],
    "HIP 46390": [{"english": "Alphard"},{"native": "Alphard"}],
    "HIP 46750": [{"english": "Alterf"},{"native": "Alterf"}],
    "HIP 47508": [{"english": "Subra"},{"native": "Subra"}],
    "HIP 48455": [{"english": "Rasalas"},{"native": "Rasalas"}],
    "HIP 49669": [{"english": "Regulus"},{"native": "Regulus"}],
    "HIP 50335": [{"english": "Adhafera"},{"native": "Adhafera"}],
    "HIP 50372": [{"english": "Tania Borealis"},{"native": "Tania Borealis"}],
    "HIP 50583": [{"english": "Algieba"},{"native": "Algieba"}],
    "HIP 50801": [{"english": "Tania Australis"},{"native": "Tania Australis"}],
    "HIP 53740": [{"english": "Alkes"},{"native": "Alkes"}],
    "HIP 53910": [{"english": "Merak"},{"native": "Merak"}],
    "HIP 54035": [{"english": "Lalande 21185"},{"native": "Lalande 21185"}],
    "HIP 54061": [{"english": "Dubhe"},{"native": "Dubhe"}],
    "HIP 54872": [{"english": "Zosma"},{"native": "Zosma"}],
    "HIP 54879": [{"english": "Chertan"},{"native": "Chertan"}],
    "HIP 55203": [{"english": "Alula Australis"},{"native": "Alula Australis"}],
    "HIP 55219": [{"english": "Alula Borealis"},{"native": "Alula Borealis"}],
    "HIP 56211": [{"english": "Giausar"},{"native": "Giausar"}],
    "HIP 57632": [{"english": "Denebola"},{"native": "Denebola"}],
    "HIP 57757": [{"english": "Zavijava"},{"native": "Zavijava"}],
    "HIP 57939": [{"english": "Groombridge 1830"},{"native": "Groombridge 1830"}],
    "HIP 58001": [{"english": "Phecda"},{"native": "Phecda"}],
    "HIP 59199": [{"english": "Alchiba"},{"native": "Alchiba"}],
    "HIP 59654": [{"english": "Rmk 14"},{"native": "Rmk 14"}],
    "HIP 59774": [{"english": "Megrez"},{"native": "Megrez"}],
    "HIP 59803": [{"english": "Gienah"},{"native": "Gienah"}],
    "HIP 60129": [{"english": "Zaniah"},{"native": "Zaniah"}],
    "HIP 60718": [{"english": "Acrux"},{"native": "Acrux"}],
    "HIP 60965": [{"english": "Algorab"},{"native": "Algorab"}],
    "HIP 61084": [{"english": "Gacrux"},{"native": "Gacrux"}],
    "HIP 61317": [{"english": "Chara"},{"native": "Chara"}],
    "HIP 61932": [{"english": "Muhlifain"},{"native": "Muhlifain"}],
    "HIP 61941": [{"english": "Porrima"},{"native": "Porrima"}],
    "HIP 62434": [{"english": "Mimosa"},{"native": "Mimosa"}],
    "HIP 62956": [{"english": "Alioth"},{"native": "Alioth"}],
    "HIP 63125": [{"english": "Cor Caroli"},{"native": "Cor Caroli"}],
    "HIP 63608": [{"english": "Vindemiatrix"},{"native": "Vindemiatrix"}],
    "HIP 65378": [{"english": "Mizar"},{"native": "Mizar"}],
    "HIP 65474": [{"english": "Spica"},{"native": "Spica"}],
    "HIP 65477": [{"english": "Alcor"},{"native": "Alcor"}],
    "HIP 67301": [{"english": "Alkaid"},{"native": "Alkaid"}],
    "HIP 67927": [{"english": "Muphrid"},{"native": "Muphrid"}],
    "HIP 68002": [{"english": "Alnair"},{"native": "Alnair"}],
    "HIP 68702": [{"english": "Hadar"},{"native": "Hadar"}],
    "HIP 68756": [{"english": "Thuban"},{"native": "Thuban"}],
    "HIP 68933": [{"english": "Menkent"},{"native": "Menkent"}],
    "HIP 69673": [{"english": "Arcturus"},{"native": "Arcturus"}],
    "HIP 69701": [{"english": "Syrma"},{"native": "Syrma"}],
    "HIP 69995": [{"english": "V1002"},{"native": "V1002"}],
    "HIP 70890": [{"english": "Proxima Centauri"},{"native": "Proxima Centauri"}],
    "HIP 71075": [{"english": "Seginus"},{"native": "Seginus"}],
    "HIP 71683": [{"english": "Rigil Kentaurus"},{"native": "Rigil Kentaurus"}],
    "HIP 72105": [{"english": "Izar"},{"native": "Izar"}],
    "HIP 72487": [{"english": "Merga"},{"native": "Merga"}],
    "HIP 72607": [{"english": "Kochab"},{"native": "Kochab"}],
    "HIP 72622": [{"english": "Zubenelgenubi"},{"native": "Zubenelgenubi"}],
    "HIP 73184": [{"english": "H N 28"},{"native": "H N 28"}],
    "HIP 73555": [{"english": "Nekkar"},{"native": "Nekkar"}],
    "HIP 74785": [{"english": "Zubeneschamali"},{"native": "Zubeneschamali"}],
    "HIP 75097": [{"english": "Pherkad"},{"native": "Pherkad"}],
    "HIP 75411": [{"english": "Alkalurops"},{"native": "Alkalurops"}],
    "HIP 75458": [{"english": "Edasich"},{"native": "Edasich"}],
    "HIP 75695": [{"english": "Nusakan"},{"native": "Nusakan"}],
    "HIP 76267": [{"english": "Alphecca"},{"native": "Alphecca"}],
    "HIP 77070": [{"english": "Unukalhai"},{"native": "Unukalhai"}],
    "HIP 78322": [{"english": "T = Blaze Star"},{"native": "T = Blaze Star"}],
    "HIP 78401": [{"english": "Dschubba"},{"native": "Dschubba"}],
    "HIP 78820": [{"english": "Graffias"},{"native": "Graffias"}],
    "HIP 79043": [{"english": "Marsic"},{"native": "Marsic"}],
    "HIP 79593": [{"english": "Yed Prior"},{"native": "Yed Prior"}],
    "HIP 79882": [{"english": "Yed Posterior"},{"native": "Yed Posterior"}],
    "HIP 80112": [{"english": "Al Niyat"},{"native": "Al Niyat"}],
    "HIP 80463": [{"english": "Cujam"},{"native": "Cujam"}],
    "HIP 80763": [{"english": "Antares"},{"native": "Antares"}],
    "HIP 80816": [{"english": "Kornephoros"},{"native": "Kornephoros"}],
    "HIP 80883": [{"english": "Marfik"},{"native": "Marfik"}],
    "HIP 82273": [{"english": "Atria"},{"native": "Atria"}],
    "HIP 83608": [{"english": "Alrakis"},{"native": "Alrakis"}],
    "HIP 84012": [{"english": "Sabik"},{"native": "Sabik"}],
    "HIP 84345": [{"english": "Rasalgethi"},{"native": "Rasalgethi"}],
    "HIP 85670": [{"english": "Rastaban"},{"native": "Rastaban"}],
    "HIP 85693": [{"english": "Maasym"},{"native": "Maasym"}],
    "HIP 85696": [{"english": "Lesath"},{"native": "Lesath"}],
    "HIP 85822": [{"english": "Yildun"},{"native": "Yildun"}],
    "HIP 85927": [{"english": "Shaula"},{"native": "Shaula"}],
    "HIP 86032": [{"english": "Rasalhague"},{"native": "Rasalhague"}],
    "HIP 86228": [{"english": "Girtab"},{"native": "Girtab"}],
    "HIP 86742": [{"english": "Cebalrai"},{"native": "Cebalrai"}],
    "HIP 87585": [{"english": "Grumium"},{"native": "Grumium"}],
    "HIP 87833": [{"english": "Eltanin"},{"native": "Eltanin"}],
    "HIP 87937": [{"english": "Barnard's Star"},{"native": "Barnard's Star"}],
    "HIP 88635": [{"english": "Alnasl"},{"native": "Alnasl"}],
    "HIP 89931": [{"english": "Kaus Media"},{"native": "Kaus Media"}],
    "HIP 90185": [{"english": "Kaus Australis"},{"native": "Kaus Australis"}],
    "HIP 90496": [{"english": "Kaus Borealis"},{"native": "Kaus Borealis"}],
    "HIP 91262": [{"english": "Vega"},{"native": "Vega"}],
    "HIP 92420": [{"english": "Sheliak"},{"native": "Sheliak"}],
    "HIP 92855": [{"english": "Nunki"},{"native": "Nunki"}],
    "HIP 92946": [{"english": "Alya"},{"native": "Alya"}],
    "HIP 93194": [{"english": "Sulafat"},{"native": "Sulafat"}],
    "HIP 93506": [{"english": "Ascella"},{"native": "Ascella"}],
    "HIP 94376": [{"english": "Altais"},{"native": "Altais"}],
    "HIP 95241": [{"english": "Arkab"},{"native": "Arkab"}],
    "HIP 95347": [{"english": "Rukbat"},{"native": "Rukbat"}],
    "HIP 95947": [{"english": "Albireo"},{"native": "Albireo"}],
    "HIP 96757": [{"english": "Sham"},{"native": "Sham"}],
    "HIP 97278": [{"english": "Tarazed"},{"native": "Tarazed"}],
    "HIP 97649": [{"english": "Altair"},{"native": "Altair"}],
    "HIP 98036": [{"english": "Alshain"},{"native": "Alshain"}],
    "HIP 100064": [{"english": "Algedi"},{"native": "Algedi"}],
    "HIP 100345": [{"english": "Dabih"},{"native": "Dabih"}],
    "HIP 100453": [{"english": "Sadr"},{"native": "Sadr"}],
    "HIP 100751": [{"english": "Peacock"},{"native": "Peacock"}],
    "HIP 101769": [{"english": "Rotanev"},{"native": "Rotanev"}],
    "HIP 101958": [{"english": "Sualocin"},{"native": "Sualocin"}],
    "HIP 102098": [{"english": "Deneb"},{"native": "Deneb"}],
    "HIP 102618": [{"english": "Albali"},{"native": "Albali"}],
    "HIP 104987": [{"english": "Kitalpha"},{"native": "Kitalpha"}],
    "HIP 105090": [{"english": "Lacaille 8760"},{"native": "Lacaille 8760"}],
    "HIP 105199": [{"english": "Alderamin"},{"native": "Alderamin"}],
    "HIP 106032": [{"english": "Alfirk"},{"native": "Alfirk"}],
    "HIP 106278": [{"english": "Sadalsuud"},{"native": "Sadalsuud"}],
    "HIP 106985": [{"english": "Nashira"},{"native": "Nashira"}],
    "HIP 107136": [{"english": "Azelfafage"},{"native": "Azelfafage"}],
    "HIP 107259": [{"english": "Herschel's Garnet Star"},{"native": "Herschel's Garnet Star"}],
    "HIP 107315": [{"english": "Enif"},{"native": "Enif"}],
    "HIP 107556": [{"english": "Deneb Algedi"},{"native": "Deneb Algedi"}],
    "HIP 108917": [{"english": "Kurhah"},{"native": "Kurhah"}],
    "HIP 109074": [{"english": "Sadalmelik"},{"native": "Sadalmelik"}],
    "HIP 109268": [{"english": "Al Na'ir"},{"native": "Al Na'ir"}],
    "HIP 109427": [{"english": "Biham"},{"native": "Biham"}],
    "HIP 110003": [{"english": "Ancha"},{"native": "Ancha"}],
    "HIP 110395": [{"english": "Sadachbia"},{"native": "Sadachbia"}],
    "HIP 110893": [{"english": "Krueger 60"},{"native": "Krueger 60"}],
    "HIP 111710": [{"english": "Situla"},{"native": "Situla"}],
    "HIP 112029": [{"english": "Homam"},{"native": "Homam"}],
    "HIP 112158": [{"english": "Matar"},{"native": "Matar"}],
    "HIP 112748": [{"english": "Sadalbari"},{"native": "Sadalbari"}],
    "HIP 113136": [{"english": "Skat"},{"native": "Skat"}],
    "HIP 113368": [{"english": "Fomalhaut"},{"native": "Fomalhaut"}],
    "HIP 113881": [{"english": "Scheat"},{"native": "Scheat"}],
    "HIP 113963": [{"english": "Markab"},{"native": "Markab"}],
    "HIP 114622": [{"english": "Bradley 3077"},{"native": "Bradley 3077"}],
    "HIP 116727": [{"english": "Errai"},{"native": "Errai"}]
}

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
            # The S&T data specifies that the line from nu Pup to Canopus end
            # at a blank spot in the middle of nowhere due to the fact that
            # Canopus is in Carina, not Puppis.  Since Canopus is drawn with
            # an enormous star size due to its brightness, the offset is huge
            # as well, which means our normal search routine fails to locate
            # Canopus and instead locates a mag6 star, HIP 30953, for the
            # line to end at.  So we override that here to force it to end
            # at Canopus.  See https://github.com/Stellarium/stellarium/issues/1438
            elif table['HIP'][0] == 30953:
                return 30438
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

    def get_segments(self):
        '''
        returns a list of segments for this line.  Each segment is
        a 3-tuple of (start, end, weight)
        '''
        segments = [ ]
        last_vertex = None
        for v in self.vertices:
            if last_vertex:
                segments.append( (last_vertex, v, self.weight,) )
            last_vertex = v
        return segments

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
    # So we create a single line for each, using alpha and beta of each one.
    constellations['Men'].append(Line(constellation='Men', weight=4))
    constellations['Men'][-1].add_vertex(29271) # alpha Men
    constellations['Men'][-1].add_vertex(23467) # beta Men
    constellations['Mic'].append(Line(constellation='Mic', weight=4))
    constellations['Mic'][-1].add_vertex(102831) # alpha Mic
    constellations['Mic'][-1].add_vertex(102989) # beta Mic

    print("Generating constellation data...", file=sys.stderr)
    output_json = { "constellations": [ ] }
    for constellation in sorted(constellations.keys()):
        print("{} {} {} {}".format(constellation, constellation_map[constellation], len(constellations[constellation]), " ".join(f"{i}" for i in constellations[constellation])), file=sys.stderr)

        # Start by extracting all the line segments and their weights,
        # skipping segments we have already seen.
        constellation_segments = [ ]
        seen_segments = set()
        for l in constellations[constellation]:
            for s in l.get_segments():
                if (s[0], s[1],) in seen_segments or (s[1], s[0],) in seen_segments:
                    print("  Segment {},{} has been seen, skipping weight {} repeat".format(*s), file=sys.stderr)
                    continue
                seen_segments.add( (s[0], s[1],) )
                constellation_segments.append(s)

        # Now generate line sequences by line weight
        constellation_lines = [ ]
        current_weight = None
        this_line = [ ]
        for s in constellation_segments:
            # 1 = bold
            # 2 = normal
            # 3 = normal
            # 4 = thin
            # 'normal' isn't an actual weight, it's just what happens if you leave off the weight specifier.
            weight = 'normal'
            if s[2] >= 4:
                weight = 'thin'
            elif s[2] <=1:
                weight = 'bold'

            if not this_line:
                # if the current line is empty, start with this segment
                if weight == 'normal':
                    this_line = [ s[0], s[1] ]
                else:
                    this_line = [ weight, s[0], s[1] ]
                current_weight = weight
            elif this_line[-1] == s[0]:
                # continue this line with the current segment
                this_line.append(s[1])
            elif this_line[-1] == s[1]:
                # continue this line with the current segment
                this_line.append(s[0])
            elif weight != current_weight:
                # start a new line if weights have changed
                if this_line:
                    constellation_lines.append(this_line)
                if weight == 'normal':
                    this_line = [ s[0], s[1] ]
                else:
                    this_line = [ weight, s[0], s[1] ]
                current_weight = weight
            else:
                # start a new line if this segment has nothing in common with the current line
                if this_line:
                    constellation_lines.append(this_line)
                if weight == 'normal':
                    this_line = [ s[0], s[1] ]
                else:
                    this_line = [ weight, s[0], s[1] ]
                current_weight = weight

        # append the last line we processed
        constellation_lines.append(this_line)

        output_json["constellations"].append({
            "id": f"CON western_SnT {constellation}",
            "common_name": NoIndent({"english":constellation_map[constellation]}),
            "lines": NoIndent(constellation_lines),
            "iau": constellation
        })

    output_json["id"] = "western_SnT"
    output_json["region"] = "Europe"
    output_json["fallback_to_international_names"] = True
    output_json["highlight"] = "CON western_SnT Ori"
    output_json["common_names"] = star_common_names

    print(json.dumps(output_json, cls=MyEncoder, indent=2, sort_keys=True))
    sys.exit(exitval)
