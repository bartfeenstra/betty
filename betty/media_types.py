"""
Media type plugins.
"""

from __future__ import annotations

from typing import Final

from betty.content_type import ContentTypeDefinition
from betty.localizables.gettext import _

apple_keynote: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "apple-keynote",
    label="Apple Keynote Presentation",
    media_type="application/vnd.apple.keynote",
    extension=".key",
)

apple_numbers: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "apple-numbers",
    label="Apple Numbers Spreadsheet",
    media_type="application/vnd.apple.numbers",
    extension=".numbers",
)

apple_pages: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "apple-pages",
    label="Apple Pages Document",
    media_type="application/vnd.apple.pages",
    extension=".pages",
)

avif: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "avif", label="AVIF", media_type="image/avif", extension=".avif"
)

bmp: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "bmp", label="Windows Bitmap", media_type="image/bmp", extension=".bmp"
)

css: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "css", label="CSS", media_type="text/css", extension=".css"
)

csv: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "csv", label="CSV", media_type="text/csv", extension=".csv"
)

eps: Final[ContentTypeDefinition] = ContentTypeDefinition(
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

epub: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "epub", label="EPUB", media_type="application/epub+zip", extension=".epub"
)

gedcom: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "gedcom",
    label="GEDCOM",
    media_type="application/vnd.familysearch.gedcom",
    extension=".ged",
)

geneweb: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "geneweb", label="GeneWeb", extension=".gw"
)

gif: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "gif", label="GIF", media_type="image/gif", extension=".gif"
)

gramps_2_database: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "gramps-2-database", label=_("Gramps 2.x database"), extension=".grdb"
)

gramps_xml: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "gramps-xml", label="Gramps XML", extension=".gramps"
)

gramps_xml_package: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "gramps-xml-package", label="Gramps XML package", extension=".gpkg"
)

html: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "html", label="HTML", media_type="text/html", extension=(".html", ".htm")
)

icns: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "icns", label="Apple Icon Image", media_type="image/x-icns", extension=".icns"
)

ico: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "ico", label="ICO", media_type=("image/x-icon", "image/ico"), extension=".ico"
)

jinja: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "jinja", label=_("Jinja template"), extension=".j2"
)

jpeg: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "jpeg", label="JPEG", media_type="image/jpeg", extension=(".jpg", ".jpeg")
)

jpeg_2000: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "jpeg-2000", label="JPEG 2000", media_type="image/jp2", extension=".jp2"
)

jpeg_mpo: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "jpeg-mpo", label="JPEG Multi-Picture", extension=".mpo"
)

jpeg_xl: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "jpeg-xl", label="JPEG XL", media_type="image/jxl", extension=".jxl"
)

javascript: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "javascript", label="JavaScript", media_type="text/javascript", extension=".json"
)

json: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "json", label="JSON", media_type="application/json", extension=".json"
)

markdown: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "markdown",
    label="Markdown",
    media_type="text/markdown",
    extension=(".md", ".markdown"),
)

microsoft_excel: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "microsoft-excel",
    label=_("Microsoft Excel 97-2003 spreadsheet"),
    media_type="application/vnd.ms-excel",
    extension=".xls",
)

microsoft_powerpoint: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "microsoft-powerpoint",
    label=_("Microsoft PowerPoint 97-2003 presentation"),
    media_type="application/vnd.ms-powerpoint",
    extension=".ppt",
)

microsoft_word: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "microsoft-word",
    label=_("Microsoft Word 97-2003 document"),
    media_type="application/msword",
    extension=".doc",
)

office_open_xml_document: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "office-open-xml-document",
    label=_("Microsoft Word document"),
    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    extension=".docx",
)

office_open_xml_presentation: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "office-open-xml-presentation",
    label=_("Microsoft PowerPoint presentation"),
    media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    extension=".pptx",
)

office_open_xml_spreadsheet: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "office-open-xml-spreadsheet",
    label=_("Microsoft Excel spreadsheet"),
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    extension=".xlsx",
)

opendocument_graphics: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "opendocument-graphics",
    label=_("OpenDocument graphics"),
    media_type="application/vnd.oasis.opendocument.graphics",
    extension=".odg",
)

opendocument_presentation: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "opendocument-presentation",
    label=_("OpenDocument presentation"),
    media_type="application/vnd.oasis.opendocument.presentation",
    extension=".odp",
)

opendocument_spreadsheet: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "opendocument-spreadsheet",
    label=_("OpenDocument spreadsheet"),
    media_type="application/vnd.oasis.opendocument.spreadsheet",
    extension=".ods",
)

opendocument_text: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "opendocument-text",
    label=_("OpenDocument text"),
    media_type="application/vnd.oasis.opendocument.text",
    extension=".odt",
)

pdf: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "pdf", label="PDF", media_type="application/pdf", extension=".pdf"
)

photoshop: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "photoshop",
    label=_("Photoshop document"),
    media_type="image/vnd.adobe.photoshop",
    extension=".psd",
)

plain_text: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "plain-text", label=_("Plain text"), media_type="text/plain", extension=".txt"
)

png: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "png",
    label="PNG",
    media_type=("image/png", "image/apng"),
    extension=(".png", ".apng"),
)

pro_gen: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "pro-gen", label="PRO-GEN", extension=".def"
)

rst: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "rst",
    label="RST",
    description="reStructuredText",
    media_type="text/x-rst",
    extension=".rst",
)

rtf: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "rtf",
    label="Rich Text Format",
    media_type=("application/rtf", "text/rtf"),
    extension=".rtf",
)

scss: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "scss", label="SCSS", extension=".scss"
)

svg: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "svg", label="SVG", media_type="image/svg+xml", extension=".svg"
)

tiff: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "tiff", label="TIFF", media_type="image/tiff", extension=".tiff"
)

vcard: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "vcard", label="vCard", media_type="text/vcard", extension=(".vcf", ".vcard")
)

webp: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "webp", label="WebP", media_type="image/webp", extension=".webp"
)

xcf: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "xcf", label="XCF", media_type="image/x-xcf", extension=".xcf"
)

xhtml: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "xhtml", label="XHTML", media_type="applcation/xhtml+xml", extension=".xhtml"
)

xml: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "xml", label="XML", media_type=("application/xml", "text/xml"), extension=".xml"
)

yaml: Final[ContentTypeDefinition] = ContentTypeDefinition(
    "yaml", label="YAML", media_type="application/yaml", extension=(".yaml", ".yml")
)
