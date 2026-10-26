# =============================================================
# Agri LMS — Helper Utilities
# =============================================================
# File    : app/utils/helpers.py
# Purpose : General-purpose helper functions used across
#           the platform including pagination, formatting,
#           file handling, and data processing utilities.
# =============================================================

import os
import math
from datetime import datetime
from flask import current_app


# =============================================================
# PAGINATION HELPER
# =============================================================

class Pagination:
    """
    Simple pagination helper for manual query pagination
    when Flask-SQLAlchemy's built-in paginate() is not used.

    Usage:
        items = MyModel.query.all()
        paginator = Pagination(items, page=1, per_page=10)
        visible_items = paginator.items
    """

    def __init__(self, items, page, per_page):
        """
        Initialize the paginator.

        Args:
            items (list): Full list of items to paginate.
            page (int): Current page number (1-indexed).
            per_page (int): Number of items per page.
        """
        self.total    = len(items)
        self.per_page = per_page
        self.page     = max(1, page)
        self.pages    = math.ceil(self.total / per_page) if per_page else 1

        start       = (self.page - 1) * per_page
        end         = start + per_page
        self.items  = items[start:end]

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def prev_num(self):
        return self.page - 1 if self.has_prev else None

    @property
    def next_num(self):
        return self.page + 1 if self.has_next else None

    def iter_pages(self, left_edge=2, right_edge=2,
                   left_current=2, right_current=2):
        """
        Generate page numbers for pagination UI rendering.
        Returns None where ellipsis (...) should appear.

        Yields:
            int or None: Page numbers or None for gaps.
        """
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or
                (self.page - left_current - 1 < num <
                 self.page + right_current) or
                    num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num


# =============================================================
# FILE SIZE FORMATTING
# =============================================================

def format_file_size(size_bytes):
    """
    Convert a file size in bytes to a human-readable string.

    Args:
        size_bytes (int): File size in bytes.

    Returns:
        str: Formatted file size string.

    Examples:
        500        → '500 B'
        15360      → '15.0 KB'
        2097152    → '2.0 MB'
        1073741824 → '1.0 GB'
    """
    if not size_bytes or size_bytes == 0:
        return '0 B'

    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size  = float(size_bytes)
    unit  = 0

    while size >= 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1

    if unit == 0:
        return f'{int(size)} B'
    return f'{size:.1f} {units[unit]}'


# =============================================================
# CURRENCY FORMATTING
# =============================================================

def format_naira(amount):
    """
    Format a numeric amount as Nigerian Naira currency.

    Args:
        amount: Numeric value to format.

    Returns:
        str: Formatted Naira string.

    Examples:
        1500.0  → '₦1,500.00'
        250000  → '₦250,000.00'
    """
    try:
        return f'₦{float(amount):,.2f}'
    except (ValueError, TypeError):
        return '₦0.00'


# =============================================================
# DATE AND TIME FORMATTING
# =============================================================

def format_date(dt, fmt='%d %b %Y'):
    """
    Format a datetime object to a readable date string.

    Args:
        dt (datetime): Datetime to format.
        fmt (str): strftime format string.

    Returns:
        str: Formatted date string or 'N/A'.
    """
    if not dt:
        return 'N/A'
    try:
        return dt.strftime(fmt)
    except AttributeError:
        return 'N/A'


def format_datetime(dt, fmt='%d %b %Y at %I:%M %p'):
    """
    Format a datetime object to a readable date-time string.

    Args:
        dt (datetime): Datetime to format.
        fmt (str): strftime format string.

    Returns:
        str: Formatted datetime string or 'N/A'.
    """
    if not dt:
        return 'N/A'
    try:
        return dt.strftime(fmt)
    except AttributeError:
        return 'N/A'


def time_since(dt):
    """
    Return a human-readable relative time string describing
    how long ago a datetime was.

    Args:
        dt (datetime): The past datetime.

    Returns:
        str: Relative time string.

    Examples:
        30 seconds ago → 'Just now'
        5 minutes ago  → '5 minutes ago'
        2 days ago     → '2 days ago'
    """
    if not dt:
        return 'Unknown'

    try:
        now   = datetime.utcnow()
        delta = now - dt
        secs  = int(delta.total_seconds())

        if secs < 60:
            return 'Just now'
        elif secs < 3600:
            m = secs // 60
            return f'{m} minute{"s" if m != 1 else ""} ago'
        elif secs < 86400:
            h = secs // 3600
            return f'{h} hour{"s" if h != 1 else ""} ago'
        elif secs < 604800:
            d = secs // 86400
            return f'{d} day{"s" if d != 1 else ""} ago'
        elif secs < 2592000:
            w = secs // 604800
            return f'{w} week{"s" if w != 1 else ""} ago'
        else:
            return format_date(dt)

    except Exception:
        return 'Unknown'


# =============================================================
# TEXT UTILITIES
# =============================================================

def truncate_words(text, num_words=20, suffix='...'):
    """
    Truncate text to a maximum number of words.

    Args:
        text (str): Text to truncate.
        num_words (int): Maximum number of words.
        suffix (str): String appended when truncated.

    Returns:
        str: Truncated text with suffix if needed.
    """
    if not text:
        return ''
    words = str(text).split()
    if len(words) <= num_words:
        return text
    return ' '.join(words[:num_words]) + suffix


def truncate_chars(text, length=150, suffix='...'):
    """
    Truncate text to a maximum character length.

    Args:
        text (str): Text to truncate.
        length (int): Maximum character length.
        suffix (str): String appended when truncated.

    Returns:
        str: Truncated text with suffix if needed.
    """
    if not text:
        return ''
    text = str(text)
    if len(text) <= length:
        return text
    return text[:length].rstrip() + suffix


def slugify(text):
    """
    Convert a string to a URL-friendly slug.

    Converts to lowercase, replaces spaces and special
    characters with hyphens, and removes consecutive hyphens.

    Args:
        text (str): Text to slugify.

    Returns:
        str: URL-safe slug string.

    Examples:
        'Introduction to Crop Science'
        → 'introduction-to-crop-science'
    """
    import re
    if not text:
        return ''
    text = text.lower().strip()
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'[^\w-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def parse_comma_list(text):
    """
    Parse a comma-separated string into a clean list.

    Args:
        text (str): Comma-separated string.

    Returns:
        list[str]: List of non-empty stripped strings.

    Examples:
        'maize, rice, cassava' → ['maize', 'rice', 'cassava']
    """
    if not text:
        return []
    return [item.strip() for item in text.split(',') if item.strip()]


def parse_newline_list(text):
    """
    Parse a newline-separated string into a clean list.

    Args:
        text (str): Newline-separated string.

    Returns:
        list[str]: List of non-empty stripped strings.
    """
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


# =============================================================
# GRADE CALCULATION
# =============================================================

def calculate_percentage(score, total):
    """
    Calculate a percentage score safely.

    Args:
        score (float): Score achieved.
        total (float): Maximum possible score.

    Returns:
        float: Percentage rounded to 2 decimal places.
               Returns 0.0 if total is zero.
    """
    try:
        if not total or float(total) <= 0:
            return 0.0
        return round((float(score) / float(total)) * 100, 2)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0


def get_grade_letter(percentage):
    """
    Convert a percentage score to a letter grade.

    Grade scale:
        A — 70% and above   (Distinction)
        B — 60% to 69%      (Merit)
        C — 50% to 59%      (Pass)
        D — 40% to 49%      (Below Pass)
        F — Below 40%       (Fail)

    Args:
        percentage (float): Score percentage.

    Returns:
        str: Single letter grade.
    """
    try:
        pct = float(percentage)
        if pct >= 70: return 'A'
        if pct >= 60: return 'B'
        if pct >= 50: return 'C'
        if pct >= 40: return 'D'
        return 'F'
    except (ValueError, TypeError):
        return 'F'


def get_grade_label(letter):
    """
    Return a descriptive label for a grade letter.

    Args:
        letter (str): Grade letter (A, B, C, D, F).

    Returns:
        str: Full grade label.
    """
    labels = {
        'A': 'Distinction',
        'B': 'Merit',
        'C': 'Pass',
        'D': 'Below Pass',
        'F': 'Fail',
    }
    return labels.get(str(letter).upper(), 'Unknown')


# =============================================================
# UPLOAD DIRECTORY HELPERS
# =============================================================

def ensure_upload_dirs():
    """
    Create all required upload subdirectories if they
    do not exist. Called at application startup.
    """
    base = current_app.config.get(
        'UPLOAD_FOLDER', 'app/static/uploads')
    subdirs = ['materials', 'submissions', 'thumbnails', 'profiles']

    for subdir in subdirs:
        path = os.path.join(base, subdir)
        os.makedirs(path, exist_ok=True)


def get_upload_path(subdir, filename):
    """
    Build the full filesystem path for an uploaded file.

    Args:
        subdir (str): Upload subdirectory name.
        filename (str): Stored filename.

    Returns:
        str: Full filesystem path to the file.
    """
    base = current_app.config.get(
        'UPLOAD_FOLDER', 'app/static/uploads')
    return os.path.join(base, subdir, filename)


def file_exists(subdir, filename):
    """
    Check whether an uploaded file exists on the filesystem.

    Args:
        subdir (str): Upload subdirectory name.
        filename (str): Stored filename.

    Returns:
        bool: True if the file exists.
    """
    if not filename:
        return False
    path = get_upload_path(subdir, filename)
    return os.path.isfile(path)


def delete_upload_file(subdir, filename):
    """
    Safely delete an uploaded file from the filesystem.

    Args:
        subdir (str): Upload subdirectory name.
        filename (str): Stored filename to delete.

    Returns:
        bool: True if deleted, False if not found or error.
    """
    if not filename:
        return False
    try:
        path = get_upload_path(subdir, filename)
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(
            f'Failed to delete file {filename}: {e}'
        )
        return False