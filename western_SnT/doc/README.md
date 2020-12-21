Sky & Telescope Stellarium Skyculture
=====================================

Constellation Shapes
--------------------

### How constellation lines were generated

The constellation shapes are generated using the
`generate_constellations.py` script found in this directory.
The script takes the `SnT_constellations.txt` file as input on
`STDIN` and returns the computed constellations JSON blob
to `STDOUT`.  Diagnostic messages are printed to `STDERR`.

The generated JSON blob is then manually inserted into the
`index.json` file in the parent directory.

The script queries the VizieR service (http://vizier.u-strasbg.fr/viz-bin/VizieR)
to translate the RA/Dec line endpoints in the S&T data, to Hipparcos
catalog IDs used by Stellarium.

The original data provided by Sky & Telescope is in this directory:

* `SnT_constellations.txt` - Constellation lines in Sky & Telescope's proprietary format
* `SnT_star_names.docx` - Sky & Telescope's star naming standards

Note that the `generate_constellations.py` script generates
a cache file so that it doesn't have to query VizieR every time
it is executed.  To force re-computing star identities, remove
the `.hip_cache` file and re-run the script.

### Constellation translation caveats

#### Line weight

Sky & Telescope draws constellation lines with various line weights.
For example, the "teaspoon" asterism to the east of the "teapot" of
Sagittarius is drawn using lighter lines than the primary constellation.

Stellarium will (eventually) draw lines with heavier weights if they
are repeated in the constellation line data.  The generation script
thus repeats the line paths several times (up to 4) to accurately
render the line weights as shown in the Sky & Telescope atlases.

#### Non-constellation stars

Sky & Telescope uses a convention of terminating constellation lines
that end at a star outside the constellation (for example, Alpheratz
in Pegasus) a half-degree short of the target star.  Stellarium's
constellation line drawing feature requires that all lines terminate
at stars.

#### Missing constellations

Sky & Telescope does not provide constellation lines for Microscopium
and Mensa.  These are hard-coded into the generation script.

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
