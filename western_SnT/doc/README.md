Sky & Telescope Stellarium Skyculture
=====================================

Constellation Shapes
--------------------

### How constellation lines were generated

The constellation shapes (`constellationship.fab`) were originally generated using
a python script, found
[here](https://github.com/Stellarium/stellarium/pull/562/files#diff-d3c90f21d14a04a710c820720bedde465d7bdb1e2984902b400276976bd00cac).

The script queried the VizieR service (http://vizier.u-strasbg.fr/viz-bin/VizieR)
to translate the RA/Dec line endpoints in the S&T data, to Hipparcos
catalog IDs used by Stellarium.

When constellation data was moved out of the main Stellarium repository,
the Stellarium team converted the `contellationship.fab` data into the
`index.json` file you see now.

The original data provided by Sky & Telescope is in this directory:

* `SnT_constellations.txt` - Constellation lines in Sky & Telescope's proprietary format
* `SnT_star_names.docx` - Sky & Telescope's star naming standards

### Constellation translation caveats

#### Line weight

Sky & Telescope draws constellation lines with various line weights.
For example, the "teaspoon" asterism to the east of the "teapot" of
Sagittarius is drawn using lighter lines than the primary constellation.

Stellarium does not have any way to draw different weights of constellation
lines, so our translation simply draws all of them.

#### Non-constellation stars

Sky & Telescope uses a convention of terminating constellation lines
that end at a star outside the constellation (for example, Alpheratz
in Pegasus) a half-degree short of the target star.  Stellarium's
constellation line drawing feature requires that all lines terminate
at stars.

#### Missing constellations

Sky & Telescope does not provide constellation lines for Microscopium
and Mensa.  Thus this `constellationship.fab` file contains
only 86 of the 88 constellations.

Star Names
----------

Sky & Telescope provided a Word document (`SnT_star_names.docx`) that contain
the names of the stars used in Sky & Telescope publications.  A script was 
used [here](https://github.com/Stellarium/stellarium/pull/562/files#diff-1fe68ae0f46adac2234529aa572caa58e3ce279287f785105db6c456b7af2a42)
that extracted the star names from this file, and looked up each star in
the Hipparcos catalog (using VizieR), and returned the `star_names.fab`
used in previous versions of Stellarium.

The Stellarium team translated the `star_names.fab` file into the
`index.json` file you see now.
