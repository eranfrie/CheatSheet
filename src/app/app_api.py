import logging
from enum import Enum

from flask import Flask, request
from markdown import markdown

from utils import opts, version
from utils.html_utils import highlight
from app.app_sections import AddBookmarkSection


INC_URL_DEFAULT = "false"
IS_FUZZY_DEFAULT = "true"

logger = logging.getLogger()


class Route (Enum):
    INDEX = "/"
    BOOKMARKS = "/bookmarks"
    ADD_BOOKMARK = "/add_bookmark"
    DELETE_BOOKMARK = "/delete_bookmark"
    ABOUT = "/about"


class Page (Enum):
    HOME = "Home"
    ABOUT = "About"


page_to_route = {
    Page.HOME: Route.INDEX.value,
    Page.ABOUT: Route.ABOUT.value,
}
assert len(Page) == len(page_to_route)


class AppAPI:
    # pylint: disable=R0915, R0914 (too-many-statements, too-many-locals)
    def __init__(self, app):
        self.app = app
        self.app_api = Flask(__name__)

        def _status_to_color(status):
            return "green" if status.success else "red"

        def _add_bookmark_form(add_bookmark_section, sections):
            if not add_bookmark_section:
                add_bookmark_section = AddBookmarkSection("", "")

            html = '<h4>Add a new snippet</h4>'
            html += f'<form action="/add_bookmark" method="post">' \
                    f'<input type="text" name="section" list="sections" placeholder="Section" ' \
                    f'size="80" value="{add_bookmark_section.last_section}"><br>' \
                    f'<datalist id="sections">'
            for s in sections:
                html += f'<option>{s}</option>'
            html += '</datalist>' \
                    '<textarea name="title" rows="15" cols="80" placeholder="Snippet"></textarea><br>' \
                    '<input onclick="this.form.submit();this.disabled = true;" type="submit">' \
                    '</form>' \
                    "<hr>"
            return html

        def _search_section():
            return """
                <br>
                Search: <input type="search" id="searchBookmark" placeholder="pattern"><br>

                <input type="checkbox" id="fuzzy" checked>
                <label for="fuzzy"> Fuzzy search</label><br>

                <br>

                <script type="text/javascript">
                  function searchEvent()
                  {
                    pattern = document.getElementById("searchBookmark").value;
                    fuzzy = document.getElementById("fuzzy").checked;

                    const xhttp = new XMLHttpRequest();
                    xhttp.onload = function() {
                      document.getElementById("bookmarks_div").innerHTML = this.responseText;
                    }
                    xhttp.open("GET", "/bookmarks?pattern=" + pattern +
                      "&fuzzy=" + fuzzy);
                    xhttp.send();
                  }

                  fuzzy.addEventListener("input", searchEvent);
                  searchBookmark.addEventListener("input", searchEvent);

                  window.onkeydown = function(e) {
                    if (e.keyCode == 65 && e.ctrlKey) {
                      document.getElementById("searchBookmark").focus();
                      document.getElementById("searchBookmark").select();
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

        def _bookmarks_section(display_bookmarks_section):
            bookmarks_section = '<div id="bookmarks_div">'

            if display_bookmarks_section.bookmarks is not None:
                # icon library
                bookmarks_section += '<link rel="stylesheet" ' \
                    'href="https://cdnjs.cloudflare.com' \
                    '/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">'
                # delete bookmark function
                bookmarks_section += """
                    <script>
                      function deleteBookmark(bookmark_id)
                      {
                        if (confirm('Delete bookmark?')) {
                          var delete_form = document.createElement('form');
                          delete_form.action='/delete_bookmark';
                          delete_form.method='POST';

                          var inpt=document.createElement('input');
                          inpt.type='hidden';
                          inpt.name='bookmark_id';
                          inpt.value=bookmark_id
                          delete_form.appendChild(inpt);

                          document.body.appendChild(delete_form);
                          delete_form.submit();
                        } else {
                          return False
                        }
                      }
                    </script>
                """

                bookmarks_section += f"Total: {len(display_bookmarks_section.bookmarks)}<br><br>"

                prev_section = None
                for b in display_bookmarks_section.bookmarks:
                    # not using escaping and highlight
                    # because markdown() does escaping
                    md_title = markdown(b.title, extensions=["extra"])
                    md_title = md_title.replace("<pre>",
                        '<pre style="background-color:LightGray; max-width:80%; white-space: pre-wrap;">')
                    section = highlight(b.escaped_chars_section, b.section_indexes)

                    if b.section and b.section != prev_section:
                        prev_section = b.section
                        bookmarks_section += "<hr><hr>"
                        bookmarks_section += f"<br><u><b><h1>{section}</h1></b></u>"

                    bookmarks_section += "<hr>"
                    bookmarks_section += f"<b>{md_title}</b><br>"
                    bookmarks_section += f'<button class="btn" onclick="deleteBookmark({b.id})">' \
                        '<i class="fa fa-trash"></i></button>'
            else:
                bookmarks_section = \
                    f'<div style="color:red">{display_bookmarks_section.display_bookmarks_err}</div>'

            bookmarks_section += '<br></div>'

            return bookmarks_section

        def _status_section(status_section):
            if not status_section:
                return ""
            return f'<div style="color:{_status_to_color(status_section)}">{status_section.msg}</div>'

        def _main_page(status_section, display_bookmarks_section, add_bookmark_section):
            # prepare list of sections
            sections = []
            if display_bookmarks_section.bookmarks:
                prev_section = None
                for b in display_bookmarks_section.bookmarks:
                    if b.section != prev_section:
                        if not b.section:
                            continue
                        prev_section = b.section
                        sections.append(b.section)

            return _header() + \
                _menu(Page.HOME) + \
                _status_section(status_section) + \
                _add_bookmark_form(add_bookmark_section, sections) + \
                _search_section() + \
                _bookmarks_section(display_bookmarks_section)

        @self.app_api.route(Route.BOOKMARKS.value)
        def bookmark():
            pattern = request.args.get("pattern")
            is_fuzzy = request.args.get("fuzzy", IS_FUZZY_DEFAULT)
            is_fuzzy = is_fuzzy.lower() == "true"
            return _bookmarks_section(self.app.display_bookmarks(pattern, is_fuzzy))

        @self.app_api.route(Route.INDEX.value)
        def index():
            pattern = request.args.get("pattern")
            is_fuzzy = request.args.get("fuzzy", IS_FUZZY_DEFAULT)
            is_fuzzy = is_fuzzy.lower() == "true"
            return _main_page(None, self.app.display_bookmarks(pattern, is_fuzzy), None)

        @self.app_api.route(Route.ADD_BOOKMARK.value, methods=["POST"])
        def add_bookmark():
            title = request.form.get("title")
            section = request.form.get("section")

            status_section, display_bookmarks_section, add_bookmark_section = \
                self.app.add_bookmark(title, section)
            return _main_page(status_section, display_bookmarks_section, add_bookmark_section)

        @self.app_api.route(Route.DELETE_BOOKMARK.value, methods=["POST"])
        def delete_bookmark():
            bookmark_id = request.form.get("bookmark_id")
            status_section, display_section = self.app.delete_bookmark(bookmark_id)
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
