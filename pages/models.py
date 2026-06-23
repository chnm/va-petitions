from urllib.parse import urlparse

import markdown
from django.db import models
from django.utils.safestring import mark_safe


class Essay(models.Model):
    """A single long-form interpretive essay (the site Introduction).

    Designed as a singleton: the team edits the one row through the admin.
    Framing fields are discrete; the prose lives in a Markdown ``body`` so
    editors never touch HTML. Use ``>`` for pull quotes and ``[^1]`` footnote
    references — the footnotes render into the NOTES section automatically.
    """

    kicker = models.CharField(
        max_length=120,
        default="Introduction · An Essay",
        help_text="Small label above the title, e.g. 'Introduction · An Essay'.",
    )
    title = models.CharField(max_length=200)
    deck = models.TextField(
        blank=True,
        help_text="Subtitle / standfirst shown in italics below the title.",
    )
    author_name = models.CharField(max_length=120, blank=True)
    author_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g. 'Professor of History, George Mason University'.",
    )
    author_bio = models.TextField(blank=True)
    body = models.TextField(
        help_text=(
            "Markdown. Use '## ' for section headings, '> ' for pull quotes, "
            "and '[^1]' footnote references (defined as '[^1]: text' at the "
            "bottom) for the Notes section."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Essay"
        verbose_name_plural = "Essay"

    def __str__(self):
        return self.title

    def body_html(self):
        """Render the Markdown body to HTML.

        ``extra`` bundles the footnotes extension (the NOTES section);
        ``smarty`` produces curly quotes and em dashes to match the design.
        """
        html = markdown.markdown(self.body, extensions=["extra", "smarty"])
        return mark_safe(html)


class ResourcePage(models.Model):
    """Singleton header content for the Educational Resources page.

    The resource cards themselves are :class:`Resource` rows; this holds only
    the page's kicker, title, and intro paragraph so the team can reword them.
    """

    kicker = models.CharField(max_length=120, default="For the Classroom")
    title = models.CharField(max_length=200, default="Educational Resources")
    intro = models.TextField(
        blank=True,
        help_text=(
            "Markdown. Inline links allowed, e.g. "
            "[TeachingHistory.org](https://teachinghistory.org)."
        ),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Resources page"
        verbose_name_plural = "Resources page"

    def __str__(self):
        return self.title

    def intro_html(self):
        return mark_safe(markdown.markdown(self.intro, extensions=["smarty"]))


class Resource(models.Model):
    """A single teaching resource card linking out to an external lesson."""

    class Category(models.TextChoices):
        LESSON_PLAN = "lesson_plan", "Lesson Plan"
        TEACHING_GUIDE = "teaching_guide", "Teaching Guide"
        STRATEGY = "strategy", "Strategy"
        PRIMARY_SOURCE_SET = "primary_source_set", "Primary Source Set"
        ASSESSMENT = "assessment", "Assessment"

    category = models.CharField(max_length=32, choices=Category.choices)
    title = models.CharField(max_length=200)
    description = models.TextField()
    url = models.URLField(help_text="Where the resource opens (e.g. on teachinghistory.org).")
    link_label = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional. Overrides the auto 'Open at <domain>' link text.",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Lower numbers appear first.",
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    def link_text(self):
        """'Open at teachinghistory.org' — derived from the URL host."""
        if self.link_label:
            return self.link_label
        host = urlparse(self.url).netloc.replace("www.", "")
        return f"Open at {host}"
