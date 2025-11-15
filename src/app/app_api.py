import base64
import json
import logging
import json
from enum import Enum
from urllib.parse import unquote_plus

from flask import Flask, request, redirect, url_for, flash, get_flashed_messages
from markdown import markdown

from utils import opts, version
from utils.html_utils import html_escape
from app.app_sections import CheatsheetSection, StatusSection


INC_URL_DEFAULT = "false"
IS_FUZZY_DEFAULT = "true"
FAVORITES_ONLY_DEFAULT = "false"

logger = logging.getLogger()


class Route (Enum):
    INDEX = "/"
    CHEATSHEETS = "/snippets"
    SEMANTIC_SEARCH = "/semanticSearch"
    GEN_ANSWER = "/genAnswer"
    ADD_CHEATSHEET = "/add_snippet"
    EDIT_FORM = "/edit"  # edit form (GET)
    EDIT_SNIPPET = "/edit_snippet"  # edit and display all (POST)
    TOGGLE_FAVORITED = "/toggleFavorited"
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


def get_favorite_star_color(is_favorited):
    if is_favorited:
        return "red"
    else:
        return "lightgray"


class AppAPI:
    # pylint: disable=R0915, R0914 (too-many-statements, too-many-locals)
    def __init__(self, app, default_fuzzy_search, enable_ai):
        self.app = app
        self.default_fuzzy_search = default_fuzzy_search
        self.enable_ai = enable_ai
        self.app_api = Flask(__name__)
        self.app_api.secret_key = 'secretkey'

        def _status_to_color(status):
            return "green" if status.success else "red"

        def _cheatsheet_form(cheatsheet_form_type, cheatsheet_section, sections):
            """A form to add/edit a cheatsheet."""
            if not cheatsheet_section:
                cheatsheet_section = CheatsheetSection("", "", None, None)

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
                    f'size="80" value="{html_escape(cheatsheet_section.last_section)}"><br>' \
                    f'<datalist id="sections">'
            for s in sections:
                html += f'<option>{s}</option>'
            html += '</datalist>' \
                    '<textarea id="snippettextarea" name="snippet" rows="15" cols="80" ' \
                    f'placeholder="Snippet"  oninput=preview()>{cheatsheet_section.last_snippet}' \
                    '</textarea><br>' \
                    '<h3>Preview:</h3>' \
                    '<div id="preview_div">'
            if cheatsheet_section.preview_snippet:
                html += cheatsheet_section.preview_snippet
            html += '</div><br>' \
                    '<input onclick="this.form.submit();this.disabled = true;" type="submit">' \
                    '</form>'
            return html

        def _get_snippet_actions(cheatsheet):
            """Shared code to return JS code for delete / edit / favorite a snippet."""
            response = '<button class="btn" ' \
                f'onclick="window.location.href=\'{Route.EDIT_FORM.value}?id={cheatsheet.id}\'">' \
                '<i class="fa fa-edit"></i></button> '
            response += f'<button class="btn" onclick="deleteCheatsheet({cheatsheet.id})">' \
                '<i class="fa fa-trash"></i></button>'

            star_color = get_favorite_star_color(cheatsheet.is_favorited)
            response += f'<span id="favoriteStar_{cheatsheet.id}" style="color:{star_color}; cursor:pointer;">&#9733;</span> <!-- Star symbol -->'
            response += '<script>' \
                f'document.getElementById("favoriteStar_{cheatsheet.id}").addEventListener("click", function()' \
                '{' \
                f'  toggle_favorited({cheatsheet.id});' \
                '});' \
              '</script>'

            return response

        def _search_section():
            checked = "checked" if self.default_fuzzy_search else ""
            fuzzy_checkbox = f'<input type="checkbox" id="fuzzy" {checked}>'
            return """
                <br>
                Search:
                <br>
                <textarea id="searchCheatsheet" name="searchCheatsheet" rows="3" cols="30"></textarea><br>

                """ \
                + fuzzy_checkbox + \
                """
                <label for="fuzzy"> Fuzzy search</label><br>

                <input type="checkbox" id="favoritesonly">
                <label for="favoritesonly"> Favorites only</label><br>

                <br>

                <input type="text" id="searchSection" placeholder="Search section" size="30"><br>

                <br>

                <script type="text/javascript">
                  function searchEvent()
                  {
                    patterns = document.getElementById("searchCheatsheet").value;
                    fuzzy = document.getElementById("fuzzy").checked;
                    favorites_only = document.getElementById("favoritesonly").checked;
                    section_pattern = document.getElementById("searchSection").value;

                    const xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                      document.getElementById("cheatsheets_div").innerHTML = this.responseText;

                      // eval the scripts
                      const scripts = document.querySelectorAll('#cheatsheets_div script');
                      scripts.forEach(script => {
                        eval(script.textContent);
                      });
                    }
                    xhttp.open("GET", "/snippets?pattern=" + btoa(patterns).replace(/\\+/g, '-').replace(/\\//g, '_') +
                      "&fuzzy=" + fuzzy +
                      "&favoritesonly=" + favorites_only +
                      "&sectionPattern=" + btoa(section_pattern));
                    xhttp.send();
                  }

                  fuzzy.addEventListener("input", searchEvent);
                  favoritesonly.addEventListener("input", searchEvent);
                  searchCheatsheet.addEventListener("input", searchEvent);
                  searchSection.addEventListener("input", searchEvent);

                  window.onkeydown = function(e) {
                    // ctrl-b - set focus on search input
                    if (e.keyCode == 66 && e.ctrlKey) {
                      document.getElementById("searchCheatsheet").focus();
                      document.getElementById("searchCheatsheet").select();
                    }
                    // ESC - reset search
                    else if (e.key === "Escape") {
                      document.getElementById("searchCheatsheet").value = '';
                      document.getElementById("searchSection").value = '';
                      searchEvent()
                    }
                  }

                  function toggle_favorited(cheatsheet_id)
                  {
                    const xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                      document.getElementById("favoriteStar_" + cheatsheet_id).style.color = this.responseText;
                    }
                    xhttp.open("POST", "/toggleFavorited?cheatsheet_id=" + cheatsheet_id);
                    xhttp.send();
                  }
                </script>
            """

        def _semantic_search_section():
            return """
                <br>
                Semantic search:
                <br>
                <textarea id="semanticSearchCheatsheet" name="semanticSearchCheatsheet" rows="3" cols="30"></textarea><br>
                <br>

                <script type="text/javascript">
                  function semanticSearch(idx)
                  {
                    query = document.getElementById("semanticSearchCheatsheet").value;
                    const xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                      const response = JSON.parse(this.responseText);
                      document.getElementById("semantic_search_result_div").innerHTML = response.div;
                      document.getElementById("generated_answer_div").innerHTML = "<h1>Generated answer:</h1><h2>Loading ...</h2>";

                      // eval the scripts
                      const scripts = document.querySelectorAll('#semantic_search_result_div script');
                      scripts.forEach(script => {
                        eval(script.textContent);
                      });

                      // second request - to generate an answer based on the semantic search result
                      const xhttp_2 = new XMLHttpRequest();
                      xhttp_2.onload = function() {
                        document.getElementById("generated_answer_div").innerHTML = this.responseText;
                      }

                      xhttp_2.open("GET", "/genAnswer?context=" + btoa(response.snippet).replace(/\\+/g, '-').replace(/\\//g, '_') + "&query=" + btoa(query).replace(/\\+/g, '-').replace(/\\//g, '_'));
                      xhttp_2.send();
                    }

                    document.getElementById("semantic_search_result_div").innerHTML = "<h2>Loading ...</h2>";
                    document.getElementById("generated_answer_div").innerHTML = "";
                    xhttp.open("GET", "/semanticSearch?index=" + idx + "&query=" + btoa(query).replace(/\\+/g, '-').replace(/\\//g, '_'));
                    xhttp.send();
                  }

                  function semanticSearchClear()
                  {
                    document.getElementById("semantic_search_result_div").innerHTML = "";
                    document.getElementById("generated_answer_div").innerHTML = "";
                  }
                </script>

                <button class="btn" onclick="semanticSearch(0)">Search</button>
                <button class="btn" onclick="semanticSearchClear()">Clear</button>
                <div id="semantic_search_result_div"></div>
                <div id="generated_answer_div"></div>
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
            cheatsheets_section = '<body style="overflow-wrap: break-word;">'
            cheatsheets_section += '<div id="cheatsheets_div">'

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

                if self.enable_ai:
                    cheatsheets_section += "<br><br><hr><br>"
                cheatsheets_section += f"Total: {len(display_cheatsheets_section.cheatsheets)}<br><br>"

                prev_section = None
                for b in display_cheatsheets_section.cheatsheets:
                    md_snippet = to_markdown(b.snippet)

                    if b.section and b.section != prev_section:
                        prev_section = b.section
                        cheatsheets_section += "<hr><hr>"
                        cheatsheets_section += f"<br><u><b><h1>{b.section}</h1></b></u>"

                    cheatsheets_section += "<hr>"
                    cheatsheets_section += f"{md_snippet}<br>"
                    cheatsheets_section += _get_snippet_actions(b)

            else:
                cheatsheets_section = \
                    f'<div style="color:red">{display_cheatsheets_section.display_cheatsheets_err}</div>'

            cheatsheets_section += '<br></div>'

            cheatsheets_section += '</body>'
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

            ai_section = ""
            if self.enable_ai:
                ai_section = "<hr>" + \
                    _semantic_search_section()

            return _header() + \
                _menu(Page.HOME) + \
                _status_section(status_section) + \
                _cheatsheet_form(CheatsheetFormType.ADD, add_cheatsheet_section, sections) + \
                "<hr>" + \
                _search_section() + \
                ai_section + \
                _cheatsheets_section(display_cheatsheets_section)

        @self.app_api.route(Route.CHEATSHEETS.value)
        def cheatsheet():
            patterns = request.args.get("pattern")
            if patterns:
                patterns = base64.urlsafe_b64decode(patterns).decode('utf-8')
                patterns = patterns.splitlines()
            else:
                patterns = []

            is_fuzzy = request.args.get("fuzzy", IS_FUZZY_DEFAULT)
            is_fuzzy = is_fuzzy.lower() == "true"

            favorites_only = request.args.get("favoritesonly", FAVORITES_ONLY_DEFAULT)
            favorites_only = favorites_only.lower() == "true"

            section_pattern = request.args.get("sectionPattern", "")
            if section_pattern:
                section_pattern = base64.b64decode(section_pattern).decode('utf-8')
            else:
                section_pattern = None

            return _cheatsheets_section(self.app.display_cheatsheets(patterns, is_fuzzy, favorites_only, section_pattern))

        @self.app_api.route(Route.SEMANTIC_SEARCH.value)
        def semantic_search():
            query = request.args.get("query")
            if not query:
                return ""
            search_res_idx = request.args.get("index")
            if not search_res_idx:
                return ""
            try:
                search_res_idx = int(search_res_idx)
            except:
                logger.exception("invalid index argument: index=%s", search_res_idx)
                return ""

            query = base64.urlsafe_b64decode(query).decode('utf-8')
            # search_res_idx may be different than requested if it's out of valid boundaries
            search_res_idx, cheatsheet = self.app.do_semantic_search(search_res_idx, query)
            if not cheatsheet:
                return ""

            # there is a result - render the html

            response = to_markdown("# Most relevant cheatsheet:")

            # left and right arrows to get prev/next semantic search result
            response += """
                <div style="font-size:50px;">
                  <span id="left-arrow" style="cursor:pointer;">&#8592;</span> <!-- Left arrow -->
            """
            response += f"""
                  <span id="searchResIdx" style="font-size:30px;">{search_res_idx+1}</span> <!-- Search result index -->
            """
            response += """
                  <span id="right-arrow" style="cursor:pointer;">&#8594;</span> <!-- Right arrow -->
                </div>

                <script>
                  function decreaseNumber() {
            """
            response += f"semanticSearch({search_res_idx} - 1);"
            response += """
                  }

                  function increaseNumber() {
            """
            response += f"semanticSearch({search_res_idx} + 1);"
            response += """
                  }

                  // add event listeners to the arrows
                  document.getElementById('left-arrow').addEventListener('click', decreaseNumber);
                  document.getElementById('right-arrow').addEventListener('click', increaseNumber);
                </script>
            """

            response += to_markdown(cheatsheet.snippet)
            response += '<br>'
            response += _get_snippet_actions(cheatsheet)

            j = {
                "div": response,
                "snippet": cheatsheet.snippet,
            }

            return json.dumps(j)

        @self.app_api.route(Route.GEN_ANSWER.value)
        def gen_answer():
            context = request.args.get("context")
            context = base64.urlsafe_b64decode(context).decode('utf-8')
            query = request.args.get("query")
            query = base64.urlsafe_b64decode(query).decode('utf-8')

            generated_answer = self.app.generate_answer(context, query)

            response = to_markdown("# Generated answer:")
            response += generated_answer
            return response

        @self.app_api.route(Route.INDEX.value)
        def index():
            pattern = request.args.get("pattern")
            patterns = [pattern] if pattern else []

            is_fuzzy = request.args.get("fuzzy", IS_FUZZY_DEFAULT)
            is_fuzzy = is_fuzzy.lower() == "true"

            favorites_only = request.args.get("favoritesonly", FAVORITES_ONLY_DEFAULT)
            favorites_only = favorites_only.lower() == "true"

            section_pattern = request.args.get("sectionPattern", None)

            status_section = None
            status_msg = get_flashed_messages()
            if status_msg:
                status_json = json.loads(status_msg[0])
                status_section = StatusSection(status_json["success"], status_json["msg"])

            return _main_page(status_section, self.app.display_cheatsheets(patterns, is_fuzzy, favorites_only, section_pattern), None)

        def flash_status_and_redirect(status_section):
            status_json = {
                "success": status_section.success,
                "msg": status_section.msg
            }
            flash(json.dumps(status_json))
            return redirect(url_for('index'))

        @self.app_api.route(Route.ADD_CHEATSHEET.value, methods=["POST"])
        def add_cheatsheet():
            snippet = request.form.get("snippet")
            section = request.form.get("section")

            status_section, display_cheatsheets_section, cheatsheet_section = \
                self.app.add_cheatsheet(snippet, section)

            if status_section.success:
                return flash_status_and_redirect(status_section)
            else:
                # if request failed, we don't redirect in order to preserve the input fields
                return _main_page(status_section, display_cheatsheets_section, cheatsheet_section)

        @self.app_api.route(Route.PREVIEW.value)
        def preview():
            snippet = request.args.get("snippet", "")
            snippet = unquote_plus(snippet)
            md_snippet = to_markdown(snippet)
            return f"{md_snippet}<br>"

        def _display_edit_form(snippet, section, snippet_id, status_section):
            md_snippet = to_markdown(snippet)
            cheatsheet_section = CheatsheetSection(snippet, section, snippet_id, md_snippet)
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
                return _main_page(None, self.app.display_cheatsheets(None, False, False), None)

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

            return flash_status_and_redirect(status_section)

        @self.app_api.route(Route.TOGGLE_FAVORITED.value, methods=["POST"])
        def toggle_facorited():
            cheatsheet_id = request.args.get("cheatsheet_id")
            is_favorited = self.app.toggle_favorited(cheatsheet_id)
            return get_favorite_star_color(is_favorited)

        @self.app_api.route(Route.DELETE_CHEATSHEET.value, methods=["POST"])
        def delete_cheatsheet():
            cheatsheet_id = request.form.get("cheatsheet_id")
            status_section, display_section = self.app.delete_cheatsheet(cheatsheet_id)
            return flash_status_and_redirect(status_section)

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
