import tkinter as tk
import tkinter.font as tkfont
from html.parser import HTMLParser
from tkinter import ttk
from typing import List, Tuple, Any

from thonny import tktextext, ui_utils
from thonny.codeview import get_syntax_options_for_tag

NBSP = "\u00A0"
UL_LI_MARKER = "•" + NBSP
VERTICAL_SPACER = NBSP + "\n"


class HtmlText(tktextext.TweakableText):
    def __init__(self, master, renderer_class, link_and_form_handler, read_only=False, **kw):

        super().__init__(
            master=master,
            read_only=read_only,
            **{
                "font": "TkDefaultFont",
                # "cursor" : "",
                **kw,
            }
        )
        self._renderer_class = renderer_class
        self._link_and_form_handler = link_and_form_handler
        self._configure_tags()
        self._reset_renderer()

    def set_html_content(self, html):
        self.clear()
        self._renderer.feed(html)

    def _configure_tags(self):
        main_font = tkfont.nametofont("TkDefaultFont")

        bold_font = main_font.copy()
        bold_font.configure(weight="bold", size=main_font.cget("size"))

        italic_font = main_font.copy()
        italic_font.configure(slant="italic", size=main_font.cget("size"))

        h1_font = main_font.copy()
        h1_font.configure(size=round(main_font.cget("size") * 1.4), weight="bold")

        h2_font = main_font.copy()
        h2_font.configure(size=round(main_font.cget("size") * 1.3), weight="bold")

        h3_font = main_font.copy()
        h3_font.configure(size=main_font.cget("size"), weight="bold")

        small_font = main_font.copy()
        small_font.configure(size=round(main_font.cget("size") * 0.8))
        small_italic_font = italic_font.copy()
        small_italic_font.configure(size=round(main_font.cget("size") * 0.8))

        # Underline on font looks better than underline on tag
        underline_font = main_font.copy()
        underline_font.configure(underline=True)

        fixed_font = tkfont.nametofont("TkFixedFont")
        fixed_bold_font = fixed_font.copy()
        fixed_bold_font.configure(weight="bold", size=fixed_font.cget("size"))

        self.tag_configure("h1", font=h1_font, spacing3=5)
        self.tag_configure("h2", font=h2_font, spacing3=5)
        self.tag_configure("h3", font=h3_font, spacing3=5)
        # self.tag_configure("p", spacing1=0, spacing3=10, spacing2=0)
        self.tag_configure("line_block", spacing1=0, spacing3=10, spacing2=0)
        self.tag_configure("em", font=italic_font)
        self.tag_configure("strong", font=bold_font)

        # TODO: hyperlink syntax options may require different background as well
        self.tag_configure(
            "a",
            **{**get_syntax_options_for_tag("hyperlink"), "underline": False},
            font=underline_font
        )
        self.tag_configure("small", font=small_font)
        self.tag_configure("light", foreground="gray")
        self.tag_configure("remark", font=small_italic_font)
        self.tag_bind("a", "<ButtonRelease-1>", self._hyperlink_click)
        self.tag_bind("a", "<Enter>", self._hyperlink_enter)
        self.tag_bind("a", "<Leave>", self._hyperlink_leave)

        self.tag_configure(
            "code",
            font=fixed_font,
            # wrap="none", # TODO: needs automatic hor-scrollbar and better padding mgmt
            background="#eeeeee",
            lmargincolor="white"
        )
        self.tag_configure(
            "pre",
            font=fixed_font,
            wrap="none",  # TODO: needs automatic hor-scrollbar and better padding mgmt
            background="#eeeeee",
            rmargincolor="#eeeeee",
            lmargincolor="white"
        )
        # if ui_utils.get_tk_version_info() >= (8,6,6):
        #    self.tag_configure("code", lmargincolor=self["background"])

        li_indent = main_font.measure("m")
        li_bullet_width = main_font.measure(UL_LI_MARKER)
        for i in range(1, 6):
            indent = i * li_indent
            self.tag_configure("list%d" % i, lmargin1=indent,
                               lmargin2=indent + li_bullet_width)

        self.tag_raise("a", "em")

        if ui_utils.get_tk_version_info() >= (8, 6, 6):
            self.tag_configure("sel", lmargincolor=self["background"])
        self.tag_raise("sel")

    def _reset_renderer(self):
        self._renderer = self._renderer_class(self, self._link_and_form_handler)

    def clear(self):
        self.direct_delete("1.0", "mark")
        self.tag_delete("1.0", "mark")
        self._reset_renderer()

    def _hyperlink_click(self, event):
        mouse_index = self.index("@%d,%d" % (event.x, event.y))

        for tag in self.tag_names(mouse_index):
            # formatting tags are alphanumeric
            if self._renderer._is_link_tag(tag):
                self._link_and_form_handler(tag)
                break

    def _hyperlink_enter(self, event):
        self.config(cursor="hand2")

    def _hyperlink_leave(self, event):
        self.config(cursor="")


class HtmlRenderer(HTMLParser):
    def __init__(self, text_widget, link_and_form_handler):
        super().__init__()
        self.widget = text_widget

        # inserting at "end" acts funny, so I'm creating a mark instead
        self.widget.direct_insert("end", "\n")
        self.widget.mark_set("mark", "1.0")

        self._link_and_form_handler = link_and_form_handler
        self._unique_tag_count = 0
        self._context_tags = []
        self._active_lists = []
        self._active_forms = []
        self._block_tags = ["div", "p", "ul", "ol", "li", "pre", "form", "h1", "h2", "summary", "details"]
        self._alternatives = {"b": "strong", "i": "em"}
        self._simple_tags = ["strong", "u", "em"]
        self._ignored_tags = ["span"]
        self._active_attrs_by_tag = {}  # assuming proper close tags

    def handle_starttag(self, tag, attrs):
        tag = self._normalize_tag(tag)
        attrs = dict(attrs)
        if tag in self._ignored_tags:
            return
        else:
            self._active_attrs_by_tag[tag] = attrs

        if tag in self._block_tags:
            self._add_block_divider(tag)

        self._add_tag(tag)

        if tag == "a" and "href" in attrs:
            self._add_tag(attrs["href"])
        elif tag == "ul":
            self._active_lists.append("ul")
        elif tag == "ol":
            self._active_lists.append("ol")
        elif tag == "li":
            if self._active_lists[-1] == "ul":
                self._append_text(UL_LI_MARKER)
            elif self._active_lists[-1] == "ol":
                # TODO:
                self._append_text(UL_LI_MARKER)
        elif tag == "form":
            form = attrs.copy()
            form["inputs"] = []
            self._active_forms.append(form)
        elif tag == "input":
            if not attrs.get("type"):
                attrs["type"] = "text"

            if attrs["type"] == "hidden":
                self._add_hidden_form_variable(attrs)
            elif attrs["type"] == "file":
                self._append_file_input(attrs)
            elif attrs["type"] == "submit":
                self._append_submit_button(attrs)

    def handle_endtag(self, tag):
        tag = self._normalize_tag(tag)
        if tag in self._ignored_tags:
            return
        else:
            self._active_attrs_by_tag[tag] = {}

        if tag == "ul":
            self._close_active_list("ul")
        elif tag == "ol":
            self._close_active_list("ol")
        elif tag == "form":
            self._active_forms.pop()

        self._pop_tag(tag)

        # prepare for next piece of text
        if tag in self._block_tags:
            self._add_block_divider(tag)

    def handle_data(self, data):
        self._append_text(self._prepare_text(data))

    def _is_link_tag(self, tag):
        return ":" in tag or "/" in tag or "!" in tag

    def _create_unique_tag(self):
        self._unique_tag_count += 1
        return "_UT_%s" % self._unique_tag_count

    def _normalize_tag(self, tag):
        return self._alternatives.get(tag, tag)

    def _add_tag(self, tag):
        self._context_tags.append(tag)

    def _add_block_divider(self, tag):
        if tag == "p" and self._context_tags and self._context_tags[-1] == "li":
            return

        # replace all trailing whitespace with a single linebreak
        while self.widget.get("mark-1c", "mark") in ["\r", "\n", "\t", " "]:
            self.widget.direct_delete("mark-1c")

        self.widget.direct_insert("mark", "\n", tags=self.widget.tag_names("mark-1c"))

        # For certain tags add vertical spacer (if it's not there already)
        if (tag in ("p", "ul", "ol", "summary", "details", "table")
                and self.widget.get("mark-2c", "mark") != VERTICAL_SPACER
                and self.widget.index("mark-1c linestart") != "1.0"):
            self.widget.direct_insert("mark", VERTICAL_SPACER)

        # if self.widget.get("mark-1c", "mark") != NBSP:

    def _pop_tag(self, tag):
        while self._context_tags and self._context_tags[-1] != tag:
            # remove unclosed or synthetic other tags
            self._context_tags.pop()

        if self._context_tags:
            assert self._context_tags[-1] == tag
            self._context_tags.pop()

    def _close_active_list(self, tag):
        # TODO: active list may also include list item marker
        while self._active_lists and self._active_lists[-1] != tag:
            # remove unclosed or synthetic other tags
            self._active_lists.pop()

        if self._active_lists:
            assert self._active_lists[-1] == tag
            self._active_lists.pop()

    def _prepare_text(self, text):
        if "pre" not in self._context_tags and "code" not in self._context_tags:
            text = text.replace("\n", " ").replace("\r", " ")
            while "  " in text:
                text = text.replace("  ", " ")

        return text

    def _append_text(self, chars, extra_tags=()):
        # print("APPP", chars, tags)
        # don't put two horizontal whitespaces next to each other
        trailing_space = False
        trailing_tags = set()
        while self.widget.get("mark-1c") in (" ", "\t"):
            trailing_space = True
            trailing_tags.update(self.widget.tag_names("mark-1c"))
            self.widget.direct_delete("mark-1c")

        last_non_horspace = self.widget.get("mark-1c")
        if last_non_horspace in ["\n", NBSP]:
            # don't keep space in the beginning of the line
            trailing_space = False
            chars.lstrip(" \t")

        if (trailing_space and not chars.startswith(" ")
                and not chars.startswith("\t")):
            # Restore the required space
            self.widget.direct_insert("mark", " ", tags=tuple(trailing_tags))

        self.widget.direct_insert("mark", chars, self._get_effective_tags(extra_tags))

    def _append_submit_button(self, attrs):
        form = self._active_forms[-1]

        def handler():
            self._submit_form(form)

        value = attrs.get("value", "Submit")
        btn = ttk.Button(self.widget, text=value, command=handler, width=len(value) + 2)
        btn.html_attrs = attrs
        self._append_window(btn)
        if "name" in attrs:
            form["fields"].append([attrs, value])

    def _submit_form(self, form):
        form_data = FormData()
        print("new_form", form_data)

        for attrs, value_holder in form["inputs"]:
            value = self._expand_field_value(value_holder, attrs)
            if value is False:
                return
            elif value is not None:
                form_data.add(attrs["name"], value)

        # TODO: support default action
        # TODO: support GET forms
        action = form["action"]
        self._link_and_form_handler(action, form_data)

    def _expand_field_value(self, value_holder, attrs):
        if not "name" in attrs:
            return None

        if isinstance(value_holder, tk.Variable):
            return value_holder.get()
        elif isinstance(value_holder, tk.Text):
            return value_holder.get("1.0", "end")
        else:
            return None

    def _add_hidden_form_variable(self, attrs):
        self._active_forms[-1]["inputs"].append([attrs, attrs.get("value")])

    def _append_file_input(self, attrs):
        # TODO: support also "multiple" flag
        cb = ttk.Combobox(self.widget, values=["<active editor>", "main.py", "kala.py"])
        self._append_window(cb)

    def _append_image(self, name, extra_tags=()):
        index = self.widget.index("mark-1c")
        self.widget.image_create(index, image=self._get_image(name))
        for tag in self._get_effective_tags(extra_tags):
            self.widget.tag_add(tag, index)

    def _get_image(self, name):
        raise NotImplementedError()

    def _append_window(self, window, extra_tags=()):
        index = self.widget.index("mark-1c")
        self.widget.window_create(index, window=window)
        for tag in self._get_effective_tags(extra_tags):
            self.widget.tag_add(tag, index)

    def _get_effective_tags(self, extra_tags):
        tags = set(extra_tags) | set(self._context_tags)

        if self._active_lists:
            tags.add("list%d" % min(len(self._active_lists), 5))

        # combine tags
        if "code" in tags and "topic_title" in tags:
            tags.remove("code")
            tags.remove("topic_title")
            tags.add("topic_title_code")

        return tuple(sorted(tags))


class FormData:
    """Used for representing form fields"""

    def __init__(self, pairs: List[Tuple[Any, Any]] = None):
        if pairs is None:
            pairs = []
        self.pairs = pairs

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def add(self, key, value):
        self.pairs.append((key, value))

    def getlist(self, key):
        result = []
        for a_key, value in self.pairs:
            if a_key == key:
                result.append(value)

        return result

    def __getitem__(self, key):
        for a_key, value in self.pairs:
            if a_key == key:
                return value
        raise KeyError(key)

    def __len__(self):
        return len(self.pairs)

    def __contains__(self, key):
        for a_key, _ in self.pairs:
            if a_key == key:
                return True
        return False

    def __str__(self):
        return repr(self.pairs)

    def __bool__(self):
        return bool(len(self.pairs))
