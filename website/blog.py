from glob import glob

import datetime
import markdown
import os
import re
import yaml

from flask import *
from jinja2.filters import do_truncate, do_striptags

# Regex matching valid blog post files
_FILE_PATTERN = re.compile(r'(\d{4})-(\d{2})-(\d{2})-(.+)\.mdown\Z')

_posts = []

class Post(object):
    """Represents one post on the blog.

    Parameters:
        title : The "raw title" of the blog post. Used as a fallback when no
        title metadata is found.

        date : The "raw date" of the blog post. Used as a fallback when no date
        metadata is found.

        content : The text of the blog post. Can contain html tags.

        metadata : Optional. A dictionary containing additional data describing
        the post. Accepted fields are 'title', 'date', 'categories', and 'tags'

    """

    def __init__(self, title, date, content, metadata):
        self._title = title
        self.date = date
        self._content = content
        self.metadata = metadata or {}

    @property
    def url(self):
        return url_for( 'show_post',  year=self.date.year,
                month=self.date.month, day=self.date.day, title=self._title)

    @property
    def title(self):
        """Returns a displayable title for the post."""
        try:
            return self.metadata['title']
        except KeyError:
            return self._title.replace('-', ' ').title()

    @property
    def preview(self):
        """HTML representing a short preview of the post.

        Contains the first 200 characters of the post's content, followed by a
        link to the post itself.

        """
        preview_text = do_striptags(self._content)
        link = '... <a href="{}">Continue&rarr;</a>'.format(self.url)
        preview_html = do_truncate(preview_text, length=200, end=link)
        return preview_html

    @property
    def content(self):
        """The content of the blog post."""
        return self._content

    @property
    def pretty_date(self):
        """Returns a formatted version of the date."""
        return self.date.strftime('%B %d, %Y')

def get_post(date, title):
    """Returns a Post representing a given blog post.

    Each post is uniquely identified by its date and title.

    """
    post = (post for post in _posts
            if post.date == date and post._title == title)
    return next(post)

def posts():
    return iter(_posts)

def parse_post(abs_path):
    """Parses a Post object from a file name."""
    END_METADATA = '!END\n'

    with open(abs_path) as f:
        lines = f.readlines()

    metadata_yaml = None
    try:
        metadata_end_index = lines.index(END_METADATA)
    except ValueError:
        # If no metadata is found, then the entire file is Markdown
        content_markdown = ''.join(lines)
    else:
        metadata_yaml = ''.join(lines[:metadata_end_index])
        content_markdown = ''.join(lines[metadata_end_index+1:])

    metadata = yaml.load(metadata_yaml) if metadata_yaml else None
    content = markdown.markdown(content_markdown)

    # Extract the raw data from the file name
    file_name = os.path.basename(abs_path)
    year, month, day, title = _FILE_PATTERN.match(file_name).groups()
    date = datetime.date(int(year), int(month), int(day))

    return Post(date=date, content=content, title=title, metadata=metadata)

def parse_posts(directory):
    """Parses all of the blog posts from the blog/ directory into Post objects.

    Parameters:
        url: The relative url from the application root to the blog posts

    """
    file_names = glob(os.path.join(directory, '*.mdown'))
    for file_name in file_names:
        _posts.append(parse_post(file_name))
    _posts.sort(key=lambda p: p.date, reverse=True)
