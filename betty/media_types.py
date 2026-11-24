"""
Media type plugins.
"""

from __future__ import annotations

from typing import Final

from betty.localizables.gettext import _
from betty.media_type import MediaTypeDefinition

apple_keynote: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "apple-keynote",
    label="Apple Keynote Presentation",
    media_type="application/vnd.apple.keynote",
    extension=".key",
)

apple_numbers: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "apple-numbers",
    label="Apple Numbers Spreadsheet",
    media_type="application/vnd.apple.numbers",
    extension=".numbers",
)

apple_pages: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "apple-pages",
    label="Apple Pages Document",
    media_type="application/vnd.apple.pages",
    extension=".pages",
)

avif: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "avif", label="AVIF", media_type="image/avif", extension=".avif"
)

bmp: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "bmp", label="Windows Bitmap", media_type="image/bmp", extension=".bmp"
)

css: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "css", label="CSS", media_type="text/css", extension=".css"
)

csv: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "csv", label="CSV", media_type="text/csv", extension=".csv"
)

eps: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "eps",
    label="EPS",
    media_type=(
        "application/postscript",
        "application/eps",
        "application/x-eps",
        "image/eps",
        "image/x-eps",
    ),
    extension=(".eps", ".epsf", ".epsi"),
)

epub: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "epub", label="EPUB", media_type="application/epub+zip", extension=".epub"
)

gedcom: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "gedcom",
    label="GEDCOM",
    media_type="application/vnd.familysearch.gedcom",
    extension=".ged",
)

geneweb: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "geneweb", label="GeneWeb", extension=".gw"
)

gif: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "gif", label="GIF", media_type="image/gif", extension=".gif"
)

gramps_2_database: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "gramps-2-database", label=_("Gramps 2.x database"), extension=".grdb"
)

gramps_xml: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "gramps-xml", label="Gramps XML", extension=".gramps"
)

gramps_xml_package: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "gramps-xml-package", label="Gramps XML package", extension=".gpkg"
)

html: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "html", label="HTML", media_type="text/html", extension=(".html", ".htm")
)

icns: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "icns", label="Apple Icon Image", media_type="image/x-icns", extension=".icns"
)

ico: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "ico", label="ICO", media_type=("image/x-icon", "image/ico"), extension=".ico"
)

jinja: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "jinja", label=_("Jinja template"), extension=".j2"
)

jpeg: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "jpeg", label="JPEG", media_type="image/jpeg", extension=(".jpg", ".jpeg")
)

jpeg_2000: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "jpeg-2000", label="JPEG 2000", media_type="image/jp2", extension=".jp2"
)

jpeg_mpo: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "jpeg-mpo", label="JPEG Multi-Picture", extension=".mpo"
)

jpeg_xl: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "jpeg-xl", label="JPEG XL", media_type="image/jxl", extension=".jxl"
)

javascript: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "javascript", label="JavaScript", media_type="text/javascript", extension=".json"
)

json: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "json", label="JSON", media_type="application/json", extension=".json"
)

markdown: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "markdown",
    label="Markdown",
    media_type="text/markdown",
    extension=(".md", ".markdown"),
)

microsoft_excel: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "microsoft-excel",
    label=_("Microsoft Excel 97-2003 spreadsheet"),
    media_type="application/vnd.ms-excel",
    extension=".xls",
)

microsoft_powerpoint: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "microsoft-powerpoint",
    label=_("Microsoft PowerPoint 97-2003 presentation"),
    media_type="application/vnd.ms-powerpoint",
    extension=".ppt",
)

microsoft_word: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "microsoft-word",
    label=_("Microsoft Word 97-2003 document"),
    media_type="application/msword",
    extension=".doc",
)

office_open_xml_document: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "office-open-xml-document",
    label=_("Microsoft Word document"),
    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    extension=".docx",
)

office_open_xml_presentation: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "office-open-xml-presentation",
    label=_("Microsoft PowerPoint presentation"),
    media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    extension=".pptx",
)

office_open_xml_spreadsheet: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "office-open-xml-spreadsheet",
    label=_("Microsoft Excel spreadsheet"),
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    extension=".xlsx",
)

opendocument_graphics: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "opendocument-graphics",
    label=_("OpenDocument graphics"),
    media_type="application/vnd.oasis.opendocument.graphics",
    extension=".odg",
)

opendocument_presentation: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "opendocument-presentation",
    label=_("OpenDocument presentation"),
    media_type="application/vnd.oasis.opendocument.presentation",
    extension=".odp",
)

opendocument_spreadsheet: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "opendocument-spreadsheet",
    label=_("OpenDocument spreadsheet"),
    media_type="application/vnd.oasis.opendocument.spreadsheet",
    extension=".ods",
)

opendocument_text: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "opendocument-text",
    label=_("OpenDocument text"),
    media_type="application/vnd.oasis.opendocument.text",
    extension=".odt",
)

pdf: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "pdf", label="PDF", media_type="application/pdf", extension=".pdf"
)

photoshop: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "photoshop",
    label=_("Photoshop document"),
    media_type="image/vnd.adobe.photoshop",
    extension=".psd",
)

plain_text: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "plain-text", label=_("Plain text"), media_type="text/plain", extension=".txt"
)

png: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "png",
    label="PNG",
    media_type=("image/png", "image/apng"),
    extension=(".png", ".apng"),
)

pro_gen: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "pro-gen", label="PRO-GEN", extension=".def"
)

rst: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "rst",
    label="RST",
    description="reStructuredText",
    media_type="text/x-rst",
    extension=".rst",
)

rtf: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "rtf",
    label="Rich Text Format",
    media_type=("application/rtf", "text/rtf"),
    extension=".rtf",
)

scss: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "scss", label="SCSS", extension=".scss"
)

svg: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "svg", label="SVG", media_type="image/svg+xml", extension=".svg"
)

tiff: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "tiff", label="TIFF", media_type="image/tiff", extension=".tiff"
)

vcard: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "vcard", label="vCard", media_type="text/vcard", extension=(".vcf", ".vcard")
)

webp: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "webp", label="WebP", media_type="image/webp", extension=".webp"
)

xcf: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "xcf", label="XCF", media_type="image/x-xcf", extension=".xcf"
)

xhtml: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "xhtml", label="XHTML", media_type="applcation/xhtml+xml", extension=".xhtml"
)

xml: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "xml", label="XML", media_type=("application/xml", "text/xml"), extension=".xml"
)

yaml: Final[MediaTypeDefinition] = MediaTypeDefinition(
    "yaml", label="YAML", media_type="application/yaml", extension=(".yaml", ".yml")
)
