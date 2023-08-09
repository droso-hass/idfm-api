from io import StringIO
from html.parser import HTMLParser

# from https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python


class MLStripper(HTMLParser):
    """
    Class used to remove HTML tags from a string
    """

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d):
        self.text.write(d)

    def get_data(self):
        return self.text.getvalue()


def strip_html(html):
    """
    Removes HTML tags from the specified string
    Args:
        html: the string that contains the HTML tags to remove
    Returns:
        The specified string without the HTML tags
    """
    s = MLStripper()
    s.feed(html)
    return s.get_data()
