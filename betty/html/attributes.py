"""
Provide the HTML API, for generating HTML pages.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    NotRequired,
    Self,
    TypedDict,
    Unpack,
    cast,
    final,
    overload,
    override,
)

from betty.localizable import Localizable, ResolvableLocalizable
from betty.localizer import default_localizer
from betty.string import kebab_case_to_snake_case, snake_case_to_kebab_case

if TYPE_CHECKING:
    from betty.localizer import Localizer


class _Attribute[AttributeGetT, AttributeSetT](ABC):
    def __init__(self, html_name: str):
        self._html_name = html_name
        self._attr_name = f"html_{kebab_case_to_snake_case(html_name)}"

    @overload
    def __get__(self, instance: None, owner: type[Attributes], /) -> Self:
        pass

    @overload
    def __get__(
        self, instance: Attributes, owner: type[Attributes] | None = None, /
    ) -> AttributeGetT:
        pass

    def __get__(
        self, instance: Attributes | None, owner: type[Attributes] | None = None, /
    ) -> AttributeGetT | Self:
        if instance is None:
            return self
        return self.get(instance)

    def get(self, instance: Attributes) -> AttributeGetT:
        try:
            return cast(AttributeGetT, instance._attributes[self._attr_name])
        except KeyError:
            value = self._new_default()
            instance._attributes[self._attr_name] = value
            return value

    def __set__(self, instance: Attributes, value: AttributeSetT) -> None:
        self.set(instance, value)

    @abstractmethod
    def set(self, instance: Attributes, value: AttributeSetT) -> None:
        pass

    def setdefault(self, instance: Attributes, value: AttributeSetT) -> None:
        if self._attr_name not in instance._attributes:
            self.set(instance, value)

    @abstractmethod
    def _new_default(self) -> AttributeGetT:
        pass

    @abstractmethod
    def format(self, value: AttributeGetT, /, *, localizer: Localizer) -> str:
        """
        Format the attribute to a string.
        """


class _BooleanAttribute(_Attribute[bool, bool]):
    @override
    def set(self, instance: Attributes, value: bool) -> None:
        instance._attributes[self._attr_name] = value

    @override
    def format(self, value: bool, /, *, localizer: Localizer) -> str:
        return self._html_name

    @override
    def _new_default(self) -> bool:
        return False


class _StringAttribute(_Attribute[str, str]):
    @override
    def set(self, instance: Attributes, value: str) -> None:
        instance._attributes[self._attr_name] = value

    @override
    def format(self, value: str, /, *, localizer: Localizer) -> str:
        return f'{self._html_name}="{value.localize(localizer) if isinstance(value, Localizable) else value}"'

    @override
    def _new_default(self) -> str:
        return ""


class _MultipleStringAttribute(_Attribute[MutableSequence[str], Sequence[str]]):
    def __init__(self, html_name: str, separator: str = " "):
        super().__init__(html_name)
        self._separator = separator

    @override
    def set(self, instance: Attributes, value: Sequence[str]) -> None:
        sequence = self.get(instance)
        sequence.clear()
        sequence.extend(value)

    @override
    def format(self, values: Sequence[str], /, *, localizer: Localizer) -> str:
        return f'{self._html_name}="{self._separator.join(value.localize(localizer) if isinstance(value, Localizable) else value for value in values)}"'

    @override
    def _new_default(self) -> MutableSequence[str]:
        return []


class _BooleanOrStringAttribute(_Attribute[bool | str, bool | str]):
    @override
    def set(self, instance: Attributes, value: bool | str) -> None:
        instance._attributes[self._attr_name] = value

    @override
    def format(self, value: bool | str, /, *, localizer: Localizer) -> str:
        if isinstance(value, bool):
            return self._html_name
        return f'{self._html_name}="{value.localize(localizer) if isinstance(value, Localizable) else value}"'

    @override
    def _new_default(self) -> bool | str:
        return False


class AttributesKwargs(TypedDict):
    """
    HTML attributes as keyword arguments.
    """

    html_accept: NotRequired[Sequence[ResolvableLocalizable]]
    html_accept_charset: NotRequired[ResolvableLocalizable]
    html_accesskey: NotRequired[ResolvableLocalizable]
    html_action: NotRequired[ResolvableLocalizable]
    html_allow: NotRequired[ResolvableLocalizable]
    html_alt: NotRequired[ResolvableLocalizable]
    html_aria_controls: NotRequired[Sequence[ResolvableLocalizable]]
    html_aria_expanded: NotRequired[bool]
    html_as: NotRequired[ResolvableLocalizable]
    html_async: NotRequired[bool]
    html_autocapitalize: NotRequired[ResolvableLocalizable]
    html_autocomplete: NotRequired[ResolvableLocalizable]
    html_autoplay: NotRequired[bool]
    html_capture: NotRequired[ResolvableLocalizable]
    html_charset: NotRequired[ResolvableLocalizable]
    html_checked: NotRequired[bool]
    html_cite: NotRequired[ResolvableLocalizable]
    html_class: NotRequired[Sequence[ResolvableLocalizable]]
    html_cols: NotRequired[ResolvableLocalizable]
    html_colspan: NotRequired[ResolvableLocalizable]
    html_content: NotRequired[ResolvableLocalizable]
    html_contenteditable: NotRequired[ResolvableLocalizable]
    html_controls: NotRequired[bool]
    html_coords: NotRequired[ResolvableLocalizable]
    html_crossorigin: NotRequired[ResolvableLocalizable]
    html_data: NotRequired[ResolvableLocalizable]
    html_datetime: NotRequired[ResolvableLocalizable]
    html_decoding: NotRequired[ResolvableLocalizable]
    html_default: NotRequired[bool]
    html_defer: NotRequired[bool]
    html_dir: NotRequired[ResolvableLocalizable]
    html_dirname: NotRequired[ResolvableLocalizable]
    html_disabled: NotRequired[bool]
    html_download: NotRequired[bool | str]
    html_draggable: NotRequired[ResolvableLocalizable]
    html_enctype: NotRequired[ResolvableLocalizable]
    html_enterkeyhint: NotRequired[ResolvableLocalizable]
    html_for: NotRequired[ResolvableLocalizable]
    html_formaction: NotRequired[ResolvableLocalizable]
    html_formenctype: NotRequired[ResolvableLocalizable]
    html_formmethod: NotRequired[ResolvableLocalizable]
    html_formnovalidate: NotRequired[bool]
    html_formtarget: NotRequired[ResolvableLocalizable]
    html_headers: NotRequired[Sequence[ResolvableLocalizable]]
    html_height: NotRequired[ResolvableLocalizable]
    html_hidden: NotRequired[ResolvableLocalizable]
    html_high: NotRequired[ResolvableLocalizable]
    html_href: NotRequired[ResolvableLocalizable]
    html_hreflang: NotRequired[ResolvableLocalizable]
    html_http_equiv: NotRequired[ResolvableLocalizable]
    html_id: NotRequired[ResolvableLocalizable]
    html_integrity: NotRequired[ResolvableLocalizable]
    html_inputmode: NotRequired[ResolvableLocalizable]
    html_ismap: NotRequired[bool]
    html_itemprop: NotRequired[ResolvableLocalizable]
    html_kind: NotRequired[ResolvableLocalizable]
    html_label: NotRequired[ResolvableLocalizable]
    html_lang: NotRequired[ResolvableLocalizable]
    html_loading: NotRequired[ResolvableLocalizable]
    html_list: NotRequired[ResolvableLocalizable]
    html_loop: NotRequired[bool]
    html_low: NotRequired[ResolvableLocalizable]
    html_max: NotRequired[ResolvableLocalizable]
    html_maxlength: NotRequired[ResolvableLocalizable]
    html_minlength: NotRequired[ResolvableLocalizable]
    html_media: NotRequired[ResolvableLocalizable]
    html_method: NotRequired[ResolvableLocalizable]
    html_min: NotRequired[ResolvableLocalizable]
    html_multiple: NotRequired[bool]
    html_muted: NotRequired[bool]
    html_name: NotRequired[ResolvableLocalizable]
    html_novalidate: NotRequired[bool]
    html_open: NotRequired[bool]
    html_optimum: NotRequired[ResolvableLocalizable]
    html_pattern: NotRequired[ResolvableLocalizable]
    html_ping: NotRequired[Sequence[ResolvableLocalizable]]
    html_placeholder: NotRequired[ResolvableLocalizable]
    html_playsinline: NotRequired[bool]
    html_poster: NotRequired[ResolvableLocalizable]
    html_preload: NotRequired[ResolvableLocalizable]
    html_readonly: NotRequired[bool]
    html_referrerpolicy: NotRequired[ResolvableLocalizable]
    html_rel: NotRequired[ResolvableLocalizable]
    html_required: NotRequired[bool]
    html_reversed: NotRequired[bool]
    html_role: NotRequired[ResolvableLocalizable]
    html_rows: NotRequired[ResolvableLocalizable]
    html_rowspan: NotRequired[ResolvableLocalizable]
    html_sandbox: NotRequired[Sequence[ResolvableLocalizable]]
    html_scope: NotRequired[ResolvableLocalizable]
    html_selected: NotRequired[bool]
    html_shape: NotRequired[ResolvableLocalizable]
    html_size: NotRequired[ResolvableLocalizable]
    html_sizes: NotRequired[ResolvableLocalizable]
    html_slot: NotRequired[ResolvableLocalizable]
    html_span: NotRequired[ResolvableLocalizable]
    html_spellcheck: NotRequired[ResolvableLocalizable]
    html_src: NotRequired[ResolvableLocalizable]
    html_srcdoc: NotRequired[ResolvableLocalizable]
    html_srclang: NotRequired[ResolvableLocalizable]
    html_srcset: NotRequired[Sequence[ResolvableLocalizable]]
    html_start: NotRequired[ResolvableLocalizable]
    html_step: NotRequired[ResolvableLocalizable]
    html_style: NotRequired[ResolvableLocalizable]
    html_tabindex: NotRequired[ResolvableLocalizable]
    html_target: NotRequired[ResolvableLocalizable]
    html_title: NotRequired[ResolvableLocalizable]
    html_translate: NotRequired[ResolvableLocalizable]
    html_type: NotRequired[ResolvableLocalizable]
    html_usemap: NotRequired[ResolvableLocalizable]
    html_value: NotRequired[ResolvableLocalizable]
    html_width: NotRequired[ResolvableLocalizable]
    html_wrap: NotRequired[ResolvableLocalizable]


@final
class Attributes:
    """
    Manage attributes for an HTML element.
    """

    __slots__ = ("_attributes", "_data_attributes", "_localizer")

    # Based on https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes.
    html_accept = _MultipleStringAttribute("accept", ", ")
    html_accept_charset = _StringAttribute("accept-charset")
    html_accesskey = _StringAttribute("accesskey")
    html_action = _StringAttribute("action")
    html_allow = _StringAttribute("allow")
    html_alt = _StringAttribute("alt")
    html_aria_controls = _MultipleStringAttribute("aria-controls")
    html_aria_expanded = _BooleanAttribute("aria-expanded")
    html_as = _StringAttribute("as")
    html_async = _BooleanAttribute("async")
    html_autocapitalize = _StringAttribute("autocapitalize")
    html_autocomplete = _StringAttribute("autocomplete")
    html_autoplay = _BooleanAttribute("autoplay")
    html_capture = _StringAttribute("capture")
    html_charset = _StringAttribute("charset")
    html_checked = _BooleanAttribute("checked")
    html_cite = _StringAttribute("cite")
    html_class = _MultipleStringAttribute("class")
    html_cols = _StringAttribute("cols")
    html_colspan = _StringAttribute("colspan")
    html_content = _StringAttribute("content")
    html_contenteditable = _StringAttribute("contenteditable")
    html_controls = _BooleanAttribute("controls")
    html_coords = _StringAttribute("coords")
    html_crossorigin = _StringAttribute("crossorigin")
    # @todo "csp" is not yet documented by MDN.
    html_data = _StringAttribute("data")
    html_datetime = _StringAttribute("datetime")
    html_decoding = _StringAttribute("decoding")
    html_default = _BooleanAttribute("default")
    html_defer = _BooleanAttribute("defer")
    html_dir = _StringAttribute("dir")
    html_dirname = _StringAttribute("dirname")
    html_disabled = _BooleanAttribute("disabled")
    html_download = _BooleanOrStringAttribute("download")
    html_draggable = _StringAttribute("draggable")
    html_enctype = _StringAttribute("enctype")
    html_enterkeyhint = _StringAttribute("enterkeyhint")
    html_for = _StringAttribute("for")
    # @todo "form" is not yet documented by MDN.
    html_formaction = _StringAttribute("formaction")
    html_formenctype = _StringAttribute("formenctype")
    html_formmethod = _StringAttribute("formmethod")
    html_formnovalidate = _BooleanAttribute("formnovalidate")
    html_formtarget = _StringAttribute("formtarget")
    html_headers = _MultipleStringAttribute("headers")
    html_height = _StringAttribute("height")
    html_hidden = _StringAttribute("hidden")
    html_high = _StringAttribute("high")
    html_href = _StringAttribute("href")
    html_hreflang = _StringAttribute("hreflang")
    html_http_equiv = _StringAttribute("http-equiv")
    html_id = _StringAttribute("id")
    html_integrity = _StringAttribute("integrity")
    html_inputmode = _StringAttribute("inputmode")
    html_ismap = _BooleanAttribute("ismap")
    html_itemprop = _StringAttribute("itemprop")
    html_kind = _StringAttribute("kind")
    html_label = _StringAttribute("label")
    html_lang = _StringAttribute("lang")
    html_loading = _StringAttribute("loading")
    html_list = _StringAttribute("list")
    html_loop = _BooleanAttribute("loop")
    html_low = _StringAttribute("low")
    html_max = _StringAttribute("max")
    html_maxlength = _StringAttribute("maxlength")
    html_minlength = _StringAttribute("minlength")
    html_media = _StringAttribute("media")
    html_method = _StringAttribute("method")
    html_min = _StringAttribute("min")
    html_multiple = _BooleanAttribute("multiple")
    html_muted = _BooleanAttribute("muted")
    html_name = _StringAttribute("name")
    html_novalidate = _BooleanAttribute("novalidate")
    html_open = _BooleanAttribute("open")
    html_optimum = _StringAttribute("optimum")
    html_pattern = _StringAttribute("pattern")
    html_ping = _MultipleStringAttribute("ping")
    html_placeholder = _StringAttribute("placeholder")
    html_playsinline = _BooleanAttribute("playsinline")
    html_poster = _StringAttribute("poster")
    html_preload = _StringAttribute("preload")
    html_readonly = _BooleanAttribute("readonly")
    html_referrerpolicy = _StringAttribute("referrerpolicy")
    html_rel = _StringAttribute("rel")
    html_required = _BooleanAttribute("required")
    html_reversed = _BooleanAttribute("reversed")
    html_role = _StringAttribute("role")
    html_rows = _StringAttribute("rows")
    html_rowspan = _StringAttribute("rowspan")
    html_sandbox = _MultipleStringAttribute("sandbox")
    html_scope = _StringAttribute("scope")
    html_selected = _BooleanAttribute("selected")
    html_shape = _StringAttribute("shape")
    html_size = _StringAttribute("size")
    html_sizes = _StringAttribute("sizes")
    html_slot = _StringAttribute("slot")
    html_span = _StringAttribute("span")
    html_spellcheck = _StringAttribute("spellcheck")
    html_src = _StringAttribute("src")
    html_srcdoc = _StringAttribute("srcdoc")
    html_srclang = _StringAttribute("srclang")
    html_srcset = _MultipleStringAttribute("srcset", ", ")
    html_start = _StringAttribute("start")
    html_step = _StringAttribute("step")
    html_style = _StringAttribute("style")
    html_tabindex = _StringAttribute("tabindex")
    html_target = _StringAttribute("target")
    html_title = _StringAttribute("title")
    html_translate = _StringAttribute("translate")
    html_type = _StringAttribute("type")
    html_usemap = _StringAttribute("usemap")
    html_value = _StringAttribute("value")
    html_width = _StringAttribute("width")
    html_wrap = _StringAttribute("wrap")

    # Compile all attributes once for this class, so we do not have to keep doing it runtime, which is expensive (e.g.
    # when using inspect.getmembers()).
    __attributes: Final[Mapping[str, _Attribute[Any, Any]]] = {
        attr_name: attr_value
        for attr_name, attr_value in locals().items()
        if attr_name.startswith("html_")
    }

    def __init__(self, *, localizer: Localizer = default_localizer):
        self._attributes: MutableMapping[str, Any] = {}
        self._data_attributes: MutableMapping[str, str] = {}
        self._localizer = localizer

    def set(self, **attributes: Unpack[AttributesKwargs]) -> Self:
        """
        Set values for the given HTML attributes.
        """
        for attribute_name, attribute_value in attributes.items():
            self.__attributes[attribute_name].set(self, attribute_value)
        return self

    def setdefault(self, **attributes: Unpack[AttributesKwargs]) -> Self:
        """
        Set values for the given HTML attributes, but only for those attributes that do not already have a value set.
        """
        for attribute_name, attribute_value in attributes.items():
            self.__attributes[attribute_name].setdefault(self, attribute_value)
        return self

    def set_data(self, **attributes: str) -> Self:
        """
        Set values for the given HTML data attributes.
        """
        self._data_attributes.update(attributes)
        return self

    def get_data(self, attribute_name: str) -> str | None:
        """
        Get the value for the given HTML data attribute.
        """
        try:
            return self._data_attributes[kebab_case_to_snake_case(attribute_name)]
        except KeyError:
            return None

    def format(self) -> str:
        """
        Format the HTML attributes to a string.
        """
        return " ".join((
            *(
                formatted_attribute
                for formatted_attribute in (
                    self.__attributes[attr_name].format(
                        attr_value, localizer=self._localizer
                    )
                    for attr_name, attr_value in self._attributes.items()
                )
                if formatted_attribute
            ),
            *(
                f'data-{snake_case_to_kebab_case(attribute_name)}="{attribute_value}"'
                for attribute_name, attribute_value in self._data_attributes.items()
            ),
        ))

    @override
    def __str__(self) -> str:
        return self.format()

    def __html__(self) -> str:
        formatted = self.format()
        if formatted:
            return " " + formatted
        return ""
