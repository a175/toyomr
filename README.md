# toyomr
simple omr suite with python and latex

## To make a mark sheet to answer.

Use LaTeX with the style file `src/marksheet/marksheet.sty`.
Copy `marksheet.sty` to the same directory/folder as your LaTeX src.
Put the command `\usepackage{marksheet}` in your preamble,
and use commands,
`\brankmark`,
`\positionmarkerH`,
`\positionmarkerV`,
`\positionmarkerNE` and so on.
See `sample/sample-5x15.tex` for usage of them.
The package `marksheet` requires
packages
`graphicx`,
`qrcode`, and
`makebarcode`.


### Remarks for usage of commands defined in `marksheet.sty`. 

`\brankmark`: `\brankmark{}` makes a brank oval symbol to fill by pen/pencil.
 `\brankmark{hoge}` makes an oval symbol with the hint `hoge`.

`\positionmarkerH`: `\positionmarkerH{HOGE}` makes a barcode (of CODE39) for `HOGE`.
This barcode tells that there exist oval symbols in the row where this barcode lies,
and that the name of the row is `HOGE`.
Since the name of row is encoded as CODE39,
the name should be a string of `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`.
The size of barcode depends on the length of the string.
Each `\brankmark{}` should be contained by at least one `\positionmarkerH`.


`\positionmarkerV`: `\positionmarkerV{FUGA}` makes a barcode (of CODE39) for `FUGA`.
This barcode tells that there exist oval symbols in the column where this barcode lies,
and that the name of the column is `FUGA`.
Since the name of row is encoded as CODE39,
the name should be a string of `0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ`.
The size of barcode depends on the length of the string.
Each `\brankmark{}` should be contained by at least one `\positionmarkerV`.

NOTICE:
All of names of rows and columns in the same page should be different one another.



`\positionmarkerNE`: `\positionmarkerNE{fuga}` makes a QR code for `fuga`.
This QR code tells
that there exist `\positionmarkerV` in the row where this QR code lies,
that  there exist `\positionmarkerH` in the column where this QR code lies,
and that the name of suite of questions is `fuga`.

`\positionmarkerSE`: `\positionmarkerSE{fuga}` makes a QR code for `fuga`.
This QR code tells
that there exist `\positionmarkerV` in the row where this QR code lies,
that  there exist `\positionmarkerH` in the column where this QR code lies,
and that the name of suite of questions is `fuga`.

`\positionmarkerNW`: `\positionmarkerNW{fuga}` makes a QR code for `fuga`.
This QR code tells
that there exist `\positionmarkerV` in the row where this QR code lies,
that  there exist `\positionmarkerH` in the column where this QR code lies,
and that the name of suite of questions is `fuga`.

`\positionmarkerSW`: `\positionmarkerSW{fuga}` makes a QR code for `fuga`.
This QR code tells
that there exist `\positionmarkerV` in the row where this QR code lies,
that  there exist `\positionmarkerH` in the column where this QR code lies,
and that the name of suite of questions is `fuga`.



NOTICE:
Each `\positionmarkerH` should be contained by at least one of `\positionmarkerNE`, `\positionmarkerSE`, `\positionmarkerNW` and `\positionmarkerSW`.

NOTICE:
Each `\positionmarkerV` should be contained by at least one of `\positionmarkerNE`, `\positionmarkerSE`, `\positionmarkerNW` and `\positionmarkerSW`.

NOTICE:
Toyomr recognize the angle of scaned image by QR codes.
At least one of the following is required:
* `\positionmarkerNE` and `\positionmarkerSE` in the same column.
* `\positionmarkerNW` and `\positionmarkerSW` in the same column.
* `\positionmarkerNE` and `\positionmarkerNW` in the same row.
* `\positionmarkerSE` and `\positionmarkerSW` in the same row.


## To read answered mark sheet.


`src/toyomr.py` requires
opencv `cv2`,
zbar `pyzbar` and 
numpy `numpy`.


At this moment, functions to read scaned pdf files are not implemented.
`toyomr.py` reads a image from a document camera, or ELMO.
