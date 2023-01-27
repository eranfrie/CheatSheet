import logging
from enum import Enum
from urllib.parse import unquote_plus

from flask import Flask, request
from markdown import markdown

from utils import opts, version
from utils.html_utils import highlight
from app.app_sections import CheatsheetSection


INC_URL_DEFAULT = "false"
IS_FUZZY_DEFAULT = "true"

logger = logging.getLogger()


class Route (Enum):
    INDEX = "/"
    CHEATSHEETS = "/snippets"
    ADD_CHEATSHEET = "/add_snippet"
    EDIT_FORM = "/edit"  # edit form (GET)
    EDIT_SNIPPET = "/edit_snippet"  # edit and display all (POST)
    DELETE_CHEATSHEET = "/delete_snippet"
    PREVIEW = "/preview"
    ABOUT = "/about"


class Page (Enum):
    HOME = "Home"
    ABOUT = "About"


class CheatsheetFormType (Enum):
    ADD = "Add"
    EDIT = "Edit"


page_to_route = {
    Page.HOME: Route.INDEX.value,
    Page.ABOUT: Route.ABOUT.value,
}
assert len(Page) == len(page_to_route)


def to_markdown(snippet):
    # not using escaping and highlight
    # because markdown() does escaping
    md_snippet = markdown(snippet, extensions=["extra"])
    md_snippet = md_snippet.replace(
        "<pre>",
        '<pre style="background-color:LightGray; max-width:80%; white-space: pre-wrap;">')
    md_snippet = md_snippet.replace(
        "<code>",
        '<code style="background-color:LightGray;">')
    return md_snippet


class AppAPI:
    # pylint: disable=R0915, R0914 (too-many-statements, too-many-locals)
    def __init__(self, app):
        self.app = app
        self.app_api = Flask(__name__)

        def _status_to_color(status):
            return "green" if status.success else "red"

        def _cheatsheet_form(cheatsheet_form_type, cheatsheet_section, sections):
            """A form to add/edit a cheatsheet."""
            if not cheatsheet_section:
                cheatsheet_section = CheatsheetSection("", "", None)

            html = """
                <script type="text/javascript">
                  function preview()
                  {
                    snippet = document.getElementById("snippettextarea").value;

                    const xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                      document.getElementById("preview_div").innerHTML = this.responseText;
                    }
                    xhttp.open("GET", "/preview?snippet=" + encodeURIComponent(snippet));
                    xhttp.send();
                  }
                </script>
            """

            html += f'<h3>{cheatsheet_form_type.value} a snippet</h3>'
            html += f'<form action="/{cheatsheet_form_type.value.lower()}_snippet" method="post">'
            if cheatsheet_section.snippet_id is not None:
                html += '<input type="hidden" id="snippet_id" name="snippet_id" ' \
                        f'value="{cheatsheet_section.snippet_id}" />'
            html += f'<input type="text" name="section" list="sections" placeholder="Section" ' \
                    f'size="80" value="{cheatsheet_section.last_section}"><br>' \
                    f'<datalist id="sections">'
            for s in sections:
                html += f'<option>{s}</option>'
            html += '</datalist>' \
                    '<textarea id="snippettextarea" name="snippet" rows="15" cols="80" ' \
                    f'placeholder="Snippet"  oninput=preview()>{cheatsheet_section.last_snippet}' \
                    '</textarea><br>' \
                    '<h3>Preview:</h3>' \
                    '<div id="preview_div"></div><br>' \
                    '<input onclick="this.form.submit();this.disabled = true;" type="submit">' \
                    '</form>'
            return html

        def _search_section():
            return """
                <br>
                Search: <input type="search" id="searchCheatsheet" placeholder="pattern"><br>

                <input type="checkbox" id="fuzzy" checked>
                <label for="fuzzy"> Fuzzy search</label><br>

                <br>

                <script type="text/javascript">
                  function searchEvent()
                  {
                    pattern = document.getElementById("searchCheatsheet").value;
                    fuzzy = document.getElementById("fuzzy").checked;

                    const xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                      document.getElementById("cheatsheets_div").innerHTML = this.responseText;
                    }
                    xhttp.open("GET", "/snippets?pattern=" + pattern +
                      "&fuzzy=" + fuzzy);
                    xhttp.send();
                  }

                  fuzzy.addEventListener("input", searchEvent);
                  searchCheatsheet.addEventListener("input", searchEvent);

                  window.onkeydown = function(e) {
                    if (e.keyCode == 66 && e.ctrlKey) {
                      document.getElementById("searchCheatsheet").focus();
                      document.getElementById("searchCheatsheet").select();
                    }
                  }
                </script>
            """

        def _header():
            return f'<h1 style="text-align:center">' \
                   f'<a href="/" style="color:black; text-decoration: none;">{opts.PROD_NAME}</a>' \
                   f'</h1>'

        def _menu(curr_page):
            html = '<p style="text-align:center"><b>'

            first_page = True
            for page, url in page_to_route.items():
                if first_page:
                    first_page = False
                else:
                    html += ' | '

                if page == curr_page:
                    html += page.value
                else:
                    html += f'<a href={url} style="color:black">' + page.value + '</a>'

            html += '</b></h1>'
            return html

        def _cheatsheets_section(display_cheatsheets_section):
            cheatsheets_section = '<div id="cheatsheets_div">'

            if display_cheatsheets_section.cheatsheets is not None:
                # icon library
                cheatsheets_section += '<link rel="stylesheet" ' \
                    'href="https://cdnjs.cloudflare.com' \
                    '/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">'
                # delete cheatsheet function
                cheatsheets_section += """
                    <script>
                      function deleteCheatsheet(cheatsheet_id)
                      {
                        if (confirm('Delete cheatsheet?')) {
                          var delete_form = document.createElement('form');
                          delete_form.action='/delete_snippet';
                          delete_form.method='POST';

                          var inpt=document.createElement('input');
                          inpt.type='hidden';
                          inpt.name='cheatsheet_id';
                          inpt.value=cheatsheet_id
                          delete_form.appendChild(inpt);

                          document.body.appendChild(delete_form);
                          delete_form.submit();
                        } else {
                          return False
                        }
                      }
                    </script>
                """

                cheatsheets_section += f"Total: {len(display_cheatsheets_section.cheatsheets)}<br><br>"

                prev_section = None
                for b in display_cheatsheets_section.cheatsheets:
                    md_snippet = to_markdown(b.snippet)
                    section = highlight(b.escaped_chars_section, b.section_indexes)

                    if b.section and b.section != prev_section:
                        prev_section = b.section
                        cheatsheets_section += "<hr><hr>"
                        cheatsheets_section += f"<br><u><b><h1>{section}</h1></b></u>"

                    cheatsheets_section += "<hr>"
                    cheatsheets_section += f"{md_snippet}<br>"
                    cheatsheets_section += '<button class="btn" ' \
                        f'onclick="window.location.href=\'{Route.EDIT_FORM.value}?id={b.id}\'">' \
                        '<i class="fa fa-edit"></i></button>'
                    cheatsheets_section += f'<button class="btn" onclick="deleteCheatsheet({b.id})">' \
                        '<i class="fa fa-trash"></i></button>'
            else:
                cheatsheets_section = \
                    f'<div style="color:red">{display_cheatsheets_section.display_cheatsheets_err}</div>'

            cheatsheets_section += '<br></div>'

            return cheatsheets_section

        def _status_section(status_section):
            if not status_section:
                return ""
            return f'<div style="color:{_status_to_color(status_section)}">{status_section.msg}</div>'

        def _main_page(status_section, display_cheatsheets_section, add_cheatsheet_section):
            # prepare list of sections
            sections = []
            if display_cheatsheets_section.cheatsheets:
                prev_section = None
                for b in display_cheatsheets_section.cheatsheets:
                    if b.section != prev_section:
                        if not b.section:
                            continue
                        prev_section = b.section
                        sections.append(b.section)

            return _header() + \
                _menu(Page.HOME) + \
                _status_section(status_section) + \
                _cheatsheet_form(CheatsheetFormType.ADD, add_cheatsheet_section, sections) + \
                "<hr>" + \
                _search_section() + \
                _cheatsheets_section(display_cheatsheets_section)

        @self.app_api.route(Route.CHEATSHEETS.value)
        def cheatsheet():
            pattern = request.args.get("pattern")
            is_fuzzy = request.args.get("fuzzy", IS_FUZZY_DEFAULT)
            is_fuzzy = is_fuzzy.lower() == "true"
            return _cheatsheets_section(self.app.display_cheatsheets(pattern, is_fuzzy))

        @self.app_api.route(Route.INDEX.value)
        def index():
            pattern = request.args.get("pattern")
            is_fuzzy = request.args.get("fuzzy", IS_FUZZY_DEFAULT)
            is_fuzzy = is_fuzzy.lower() == "true"
            return _main_page(None, self.app.display_cheatsheets(pattern, is_fuzzy), None)

        @self.app_api.route(Route.ADD_CHEATSHEET.value, methods=["POST"])
        def add_cheatsheet():
            snippet = request.form.get("snippet")
            section = request.form.get("section")

            status_section, display_cheatsheets_section, cheatsheet_section = \
                self.app.add_cheatsheet(snippet, section)
            return _main_page(status_section, display_cheatsheets_section, cheatsheet_section)

        @self.app_api.route(Route.PREVIEW.value)
        def preview():
            snippet = request.args.get("snippet", "")
            snippet = unquote_plus(snippet)
            md_snippet = to_markdown(snippet)
            return f"{md_snippet}<br>"

        def _display_edit_form(snippet, section, snippet_id, status_section):
            cheatsheet_section = CheatsheetSection(snippet, section, snippet_id)
            sections = {}
            return _header() + \
                _menu(None) + \
                _status_section(status_section) + \
                _cheatsheet_form(CheatsheetFormType.EDIT, cheatsheet_section, sections)

        @self.app_api.route(Route.EDIT_FORM.value)
        def edit_form():
            cheatsheet_id = request.args.get("id")
            cheatsheet = self.app.edit_cheatsheet_form(cheatsheet_id)
            if not cheatsheet:
                return _main_page(None, self.app.display_cheatsheets(None, False), None)

            return _display_edit_form(cheatsheet.snippet, cheatsheet.section, cheatsheet_id, None)

        @self.app_api.route(Route.EDIT_SNIPPET.value, methods=["POST"])
        def edit_cheatsheet():
            snippet_id = request.form.get("snippet_id")
            snippet = request.form.get("snippet")
            section = request.form.get("section")
            status_section, display_cheatsheets_section, cheatsheet_section = \
                self.app.edit_cheatsheet(snippet_id, snippet, section)

            if not status_section.success:
                return _display_edit_form(snippet, section, snippet_id, status_section)
            return _main_page(status_section, display_cheatsheets_section, cheatsheet_section)

        @self.app_api.route(Route.DELETE_CHEATSHEET.value, methods=["POST"])
        def delete_cheatsheet():
            cheatsheet_id = request.form.get("cheatsheet_id")
            status_section, display_section = self.app.delete_cheatsheet(cheatsheet_id)
            return _main_page(status_section, display_section, None)

        @self.app_api.route(Route.ABOUT.value)
        def about():
            about_section = '<h4>About</h4>'

            ver = version.get_version()
            about_section += f'{opts.PROD_NAME} Version {ver}<br/>'

            home_page = "https://github.com/eranfrie/CheatSheet"
            about_section += f'Home page: <a href="{home_page}" target="_blank">{home_page}</a>'

            return _header() + _menu(Page.ABOUT) + about_section

    def run(self, host, port):
        self.app_api.run(host=host, port=port)  # blocking
