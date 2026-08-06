# =============================================================
# Agri LMS — Material Model
# =============================================================
# File    : app/models/material.py
# Purpose : Defines the Material database model representing
#           every learning resource uploaded to a module.
#
#           Materials are the actual content that learners
#           consume inside a module. A single module can
#           contain multiple materials of different types.
#
#           Supported material types:
#               video    — MP4, WebM, MKV files
#                          Learners can stream online and
#                          download if allowed by admin.
#               pdf      — PDF documents
#                          Rendered in the browser viewer
#                          with optional download.
#               document — Word, PowerPoint, Excel files
#                          Downloadable only.
#               image    — PNG, JPG, GIF files
#                          Displayed inline in the module.
#               other    — ZIP, RAR, and any other files
#                          Downloadable only.
#
#           Each material has its own order number within
#           its parent module, allowing the admin to arrange
#           materials in any desired sequence.
#
# Relationships:
#   Material >── Module     (many materials belong to one module)
#
# Learning Hierarchy:
#   Course
#     └── Module
#           └── Material 1  (order_number=1, type=video)
#           └── Material 2  (order_number=2, type=pdf)
#           └── Material 3  (order_number=3, type=document)
# =============================================================

from datetime import datetime
from app.extensions import db


# =============================================================
# MATERIAL TYPE CONSTANTS
# =============================================================
# These constants define all valid material types.
# Used for validation, filtering, and display logic.

MATERIAL_TYPE_VIDEO    = 'video'
MATERIAL_TYPE_PDF      = 'pdf'
MATERIAL_TYPE_DOCUMENT = 'document'
MATERIAL_TYPE_IMAGE    = 'image'
MATERIAL_TYPE_OTHER    = 'other'

MATERIAL_TYPES = [
    MATERIAL_TYPE_VIDEO,
    MATERIAL_TYPE_PDF,
    MATERIAL_TYPE_DOCUMENT,
    MATERIAL_TYPE_IMAGE,
    MATERIAL_TYPE_OTHER,
]

# File extension to material type mapping
# Used by the upload handler to auto-detect material type
EXTENSION_TYPE_MAP = {
    # Video formats
    'mp4':  MATERIAL_TYPE_VIDEO,
    'webm': MATERIAL_TYPE_VIDEO,
    'mkv':  MATERIAL_TYPE_VIDEO,
    'avi':  MATERIAL_TYPE_VIDEO,
    'mov':  MATERIAL_TYPE_VIDEO,

    # PDF
    'pdf':  MATERIAL_TYPE_PDF,

    # Document formats
    'doc':  MATERIAL_TYPE_DOCUMENT,
    'docx': MATERIAL_TYPE_DOCUMENT,
    'ppt':  MATERIAL_TYPE_DOCUMENT,
    'pptx': MATERIAL_TYPE_DOCUMENT,
    'xls':  MATERIAL_TYPE_DOCUMENT,
    'xlsx': MATERIAL_TYPE_DOCUMENT,
    'txt':  MATERIAL_TYPE_DOCUMENT,

    # Image formats
    'png':  MATERIAL_TYPE_IMAGE,
    'jpg':  MATERIAL_TYPE_IMAGE,
    'jpeg': MATERIAL_TYPE_IMAGE,
    'gif':  MATERIAL_TYPE_IMAGE,
    'webp': MATERIAL_TYPE_IMAGE,

    # Archive and other formats
    'zip':  MATERIAL_TYPE_OTHER,
    'rar':  MATERIAL_TYPE_OTHER,
    '7z':   MATERIAL_TYPE_OTHER,
}


# =============================================================
# MATERIAL MODEL
# =============================================================

class Material(db.Model):
    """
    Represents a single learning resource file within a Module.

    Materials are uploaded by admins and consumed by learners.
    Each material belongs to exactly one module and has an
    order number that determines its display sequence within
    that module.

    The allow_download flag gives admins control over whether
    learners can download the material to their local device,
    or only view it online through the browser.

    For videos — the platform streams them using the HTML5
    video player. If allow_download is True, a download
    button is shown below the player.

    For PDFs — the platform renders them using the browser's
    native PDF viewer embedded in an iframe. If allow_download
    is True, a download link is shown alongside the viewer.

    For documents, images, and other files — these are
    always download-only since they cannot be rendered inline.
    """

    __tablename__ = 'materials'

    # ── Table-level constraints ───────────────────────────────
    __table_args__ = (
        # Enforce unique ordering within each module
        # No two materials in the same module share an order number
        db.UniqueConstraint(
            'module_id',
            'order_number',
            name='uq_material_module_order'
        ),
    )

    # ── Primary Key ───────────────────────────────────────────
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique material identifier — auto-incremented primary key'
    )

    # ── Foreign Key — Parent Module ───────────────────────────
    module_id = db.Column(
        db.Integer,
        db.ForeignKey('modules.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment=(
            'Foreign key — ID of the module this material belongs to. '
            'CASCADE: deleting a module deletes all its materials.'
        )
    )

    # ── Material Identity ─────────────────────────────────────
    title = db.Column(
        db.String(300),
        nullable=False,
        comment=(
            'Display title of the material shown to learners — '
            'e.g. "Introduction Video", "Week 1 Reading PDF", '
            '"Soil Testing Guide"'
        )
    )

    description = db.Column(
        db.Text,
        nullable=True,
        comment=(
            'Optional description of the material — '
            'explains what the learner will get from it'
        )
    )

    # ── Material Type ─────────────────────────────────────────
    material_type = db.Column(
        db.String(20),
        nullable=False,
        default=MATERIAL_TYPE_OTHER,
        comment=(
            'Type of material — determines how it is rendered. '
            'video: streamed in HTML5 player | '
            'pdf: rendered in iframe PDF viewer | '
            'document: download only | '
            'image: displayed inline | '
            'other: download only'
        )
    )

    # ── File Information ──────────────────────────────────────
    file_name = db.Column(
        db.String(255),
        nullable=False,
        comment=(
            'Original filename as uploaded by the admin — '
            'stored for display purposes only'
        )
    )

    stored_file_name = db.Column(
        db.String(255),
        nullable=False,
        comment=(
            'Actual filename used on the server filesystem — '
            'UUID-prefixed to prevent collisions and directory traversal. '
            'File is stored in static/uploads/materials/'
        )
    )

    file_extension = db.Column(
        db.String(20),
        nullable=True,
        comment='Lowercase file extension without dot — e.g. mp4, pdf, docx'
    )

    file_size_bytes = db.Column(
        db.BigInteger,
        nullable=True,
        comment='File size in bytes — used for display and storage management'
    )

    mime_type = db.Column(
        db.String(100),
        nullable=True,
        comment=(
            'MIME type of the file — '
            'e.g. video/mp4, application/pdf, '
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    )

    # ── Sequencing ────────────────────────────────────────────
    order_number = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        comment=(
            'Position of this material within its module. '
            'Materials are displayed in ascending order_number sequence. '
            'Must be unique within a module — enforced by uq_material_module_order.'
        )
    )

    # ── External Content ──────────────────────────────────────
    external_url = db.Column(
        db.String(1000),
        nullable=True,
        comment=(
            'Optional external URL for this material — '
            'used when the content is hosted externally '
            'e.g. YouTube, Google Drive, OneDrive. '
            'If set and stored_file_name is NULL, the platform '
            'links to this URL instead of a local file.'
        )
    )

    is_external = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'True if this material points to an external URL '
            'rather than a locally uploaded file'
        )
    )

    # ── Access Control ────────────────────────────────────────
    allow_download = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment=(
            'Download permission flag — '
            'True: learners can download this material to their device | '
            'False: learners can only view it online. '
            'For videos and PDFs this controls the download button. '
            'Documents, images, and other files are always downloadable.'
        )
    )

    # ── Video-Specific Fields ─────────────────────────────────
    video_duration_seconds = db.Column(
        db.Integer,
        nullable=True,
        comment=(
            'Duration of a video material in seconds — '
            'used to display formatted video length to learners. '
            'Only applicable when material_type is video.'
        )
    )

    video_thumbnail = db.Column(
        db.String(255),
        nullable=True,
        comment=(
            'Filename of the video thumbnail image — '
            'displayed before the video is played. '
            'Stored in static/uploads/thumbnails/. '
            'Only applicable when material_type is video.'
        )
    )

    # ── Publishing Status ─────────────────────────────────────
    is_published = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment=(
            'Publication flag — '
            'False: material is a draft visible only to admins | '
            'True: material is visible to enrolled learners'
        )
    )

    # ── Timestamps ────────────────────────────────────────────
    date_uploaded = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment='UTC timestamp of when this material was uploaded by the admin'
    )

    date_updated = db.Column(
        db.DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
        comment='UTC timestamp of the most recent update to this material record'
    )

    # ==========================================================
    # FILE SIZE HELPERS
    # ==========================================================

    def get_file_size_display(self):
        """
        Convert raw file_size_bytes into a human-readable
        string with appropriate unit.

        Returns:
            str: Formatted file size string.

        Examples:
            500        → '500 B'
            15360      → '15.0 KB'
            2097152    → '2.0 MB'
            1073741824 → '1.0 GB'
        """
        if not self.file_size_bytes:
            return 'Unknown size'

        size = self.file_size_bytes

        if size < 1024:
            return f'{size} B'
        elif size < 1024 ** 2:
            return f'{size / 1024:.1f} KB'
        elif size < 1024 ** 3:
            return f'{size / (1024 ** 2):.1f} MB'
        else:
            return f'{size / (1024 ** 3):.1f} GB'

    # ==========================================================
    # VIDEO DURATION HELPERS
    # ==========================================================

    def get_video_duration_display(self):
        """
        Convert video_duration_seconds into a human-readable
        hours:minutes:seconds string.

        Returns:
            str: Formatted duration string or 'N/A' if not set.

        Examples:
            45    → '0:45'
            90    → '1:30'
            3661  → '1:01:01'
        """
        if not self.video_duration_seconds:
            return 'N/A'

        total = self.video_duration_seconds
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60

        if hours > 0:
            return f'{hours}:{minutes:02d}:{seconds:02d}'
        else:
            return f'{minutes}:{seconds:02d}'

    # ==========================================================
    # FILE PATH HELPERS
    # ==========================================================

    def get_file_url(self):
        """
        Build the URL path for accessing this material's file
        through the Flask static file serving route.

        Returns:
            str: Relative URL path to the material file.
                 Returns the external_url if is_external is True.
                 Returns None if neither file nor URL is available.

        Examples:
            Local  → 'uploads/materials/uuid_filename.mp4'
            External → 'https://youtu.be/example'
        """
        if self.is_external and self.external_url:
            return self.external_url
        if self.stored_file_name:
            return f'uploads/materials/{self.stored_file_name}'
        return None

    def get_video_thumbnail_url(self):
        """
        Build the URL path for accessing the video thumbnail
        image through the Flask static file serving route.

        Returns:
            str or None: Relative URL path to the thumbnail,
                         or None if no thumbnail is set.
        """
        if self.video_thumbnail:
            return f'uploads/thumbnails/{self.video_thumbnail}'
        return None

    # ==========================================================
    # TYPE DETECTION HELPERS
    # ==========================================================

    def is_video(self):
        """
        Check whether this material is a video.

        Returns:
            bool: True if material_type is 'video'.
        """
        return self.material_type == MATERIAL_TYPE_VIDEO

    def is_pdf(self):
        """
        Check whether this material is a PDF document.

        Returns:
            bool: True if material_type is 'pdf'.
        """
        return self.material_type == MATERIAL_TYPE_PDF

    def is_document(self):
        """
        Check whether this material is an office document.

        Returns:
            bool: True if material_type is 'document'.
        """
        return self.material_type == MATERIAL_TYPE_DOCUMENT

    def is_image(self):
        """
        Check whether this material is an image.

        Returns:
            bool: True if material_type is 'image'.
        """
        return self.material_type == MATERIAL_TYPE_IMAGE

    def is_viewable_online(self):
        """
        Determine whether this material can be viewed
        directly in the browser without downloading.

        Videos and PDFs are viewable online.
        Documents, images uploaded as type 'other', and
        archives require downloading.

        Returns:
            bool: True if the material renders inline.
        """
        return self.material_type in (
            MATERIAL_TYPE_VIDEO,
            MATERIAL_TYPE_PDF,
            MATERIAL_TYPE_IMAGE,
        )

    def get_type_icon(self):
        """
        Return an emoji or icon identifier corresponding
        to the material type for use in templates.

        Returns:
            str: Icon string for the material type.
        """
        icons = {
            MATERIAL_TYPE_VIDEO:    '🎬',
            MATERIAL_TYPE_PDF:      '📄',
            MATERIAL_TYPE_DOCUMENT: '📝',
            MATERIAL_TYPE_IMAGE:    '🖼️',
            MATERIAL_TYPE_OTHER:    '📦',
        }
        return icons.get(self.material_type, '📁')

    def get_type_label(self):
        """
        Return a human-readable label for the material type.

        Returns:
            str: Capitalized type label.
        """
        labels = {
            MATERIAL_TYPE_VIDEO:    'Video',
            MATERIAL_TYPE_PDF:      'PDF Document',
            MATERIAL_TYPE_DOCUMENT: 'Document',
            MATERIAL_TYPE_IMAGE:    'Image',
            MATERIAL_TYPE_OTHER:    'File',
        }
        return labels.get(self.material_type, 'File')

    # ==========================================================
    # STATIC UTILITY METHODS
    # ==========================================================

    @staticmethod
    def detect_type_from_extension(extension):
        """
        Detect and return the material type string based on
        a file extension using the EXTENSION_TYPE_MAP.

        Args:
            extension (str): Lowercase file extension without
                             the leading dot — e.g. 'mp4', 'pdf'

        Returns:
            str: Corresponding material type constant string.
                 Returns MATERIAL_TYPE_OTHER if not recognized.

        Example:
            Material.detect_type_from_extension('mp4') → 'video'
            Material.detect_type_from_extension('pdf') → 'pdf'
            Material.detect_type_from_extension('xyz') → 'other'
        """
        return EXTENSION_TYPE_MAP.get(
            extension.lower().strip(),
            MATERIAL_TYPE_OTHER
        )

    @staticmethod
    def generate_stored_filename(original_filename):
        """
        Generate a unique server-side filename for a newly
        uploaded file by prepending a UUID4 to the original
        filename. This prevents filename collisions and
        eliminates directory traversal vulnerabilities.

        Args:
            original_filename (str): The original filename
                                     as provided by the uploader.

        Returns:
            str: UUID-prefixed safe filename.

        Example:
            'soil guide.pdf' → 'a3f1c2d4_soil_guide.pdf'
        """
        import uuid
        import re

        # Sanitize — replace spaces and special characters
        safe_name = re.sub(r'[^\w\-.]', '_', original_filename)
        unique_id = uuid.uuid4().hex[:8]
        return f'{unique_id}_{safe_name}'

    # ==========================================================
    # SERIALIZATION
    # ==========================================================

    def to_dict(self):
        """
        Serialize the Material object to a plain dictionary
        suitable for JSON responses and template rendering.

        Returns:
            dict: Material data with all computed fields included.
        """
        return {
            'id':                       self.id,
            'module_id':                self.module_id,
            'title':                    self.title,
            'description':              self.description,
            'material_type':            self.material_type,
            'type_label':               self.get_type_label(),
            'type_icon':                self.get_type_icon(),
            'file_name':                self.file_name,
            'stored_file_name':         self.stored_file_name,
            'file_extension':           self.file_extension,
            'file_size_bytes':          self.file_size_bytes,
            'file_size_display':        self.get_file_size_display(),
            'mime_type':                self.mime_type,
            'order_number':             self.order_number,
            'external_url':             self.external_url,
            'is_external':              self.is_external,
            'allow_download':           self.allow_download,
            'video_duration_seconds':   self.video_duration_seconds,
            'video_duration_display':   self.get_video_duration_display(),
            'video_thumbnail':          self.video_thumbnail,
            'video_thumbnail_url':      self.get_video_thumbnail_url(),
            'file_url':                 self.get_file_url(),
            'is_viewable_online':       self.is_viewable_online(),
            'is_video':                 self.is_video(),
            'is_pdf':                   self.is_pdf(),
            'is_document':              self.is_document(),
            'is_image':                 self.is_image(),
            'is_published':             self.is_published,
            'date_uploaded':            self.date_uploaded.strftime('%Y-%m-%d %H:%M:%S'),
            'date_updated':             self.date_updated.strftime('%Y-%m-%d %H:%M:%S')
                                        if self.date_updated else None,
        }

    # ==========================================================
    # STRING REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return (
            f'<Material id={self.id} '
            f'module_id={self.module_id} '
            f'type={self.material_type!r} '
            f'title={self.title!r}>'
        )