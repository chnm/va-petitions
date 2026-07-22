from django.db import models


class County(models.Model):
    STATE_CHOICES = [
        ("VA", "Virginia"),
        ("WV", "West Virginia"),
        ("KY", "Kentucky"),
        ("PA", "Pennsylvania"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    state = models.CharField(max_length=2, choices=STATE_CHOICES, default="VA")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "counties"
        ordering = ["state", "name"]

    def __str__(self):
        return f"{self.name}, {self.get_state_display()}"


class Subject(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Petition(models.Model):
    PETITION_TYPES = [
        ("legislative", "Legislative petition"),
        ("pension", "Declaration for Revolutionary War pension"),
    ]

    KIND_CHOICES = [
        ("Petition", "Petition"),
        ("Remonstrance", "Remonstrance"),
        ("Counter-Petition", "Counter-Petition"),
    ]

    THEME_CHOICES = [
        ("property", "Property & commerce"),
        ("restrict", "Restriction & repeal"),
        ("capital", "Capital case & loss"),
        ("freedom", "Freedom & manumission"),
        ("estate", "Estate & property"),
        ("war", "Wartime loss"),
    ]

    serial = models.IntegerField(unique=True)
    mms_id = models.CharField(max_length=50, blank=True)
    rosetta_ie = models.CharField("Rosetta IE", max_length=50, blank=True)
    title = models.CharField(max_length=500)
    petition_type = models.CharField(max_length=20, choices=PETITION_TYPES)
    kind = models.CharField(
        max_length=20,
        choices=KIND_CHOICES,
        default="Petition",
        blank=True,
    )
    primary_theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        blank=True,
        help_text="Thematic classification for petitions",
    )
    date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    locality_raw = models.CharField(
        "Original locality",
        max_length=200,
        blank=True,
        help_text="Locality as recorded in the source data",
    )
    permalink = models.URLField(max_length=500, blank=True)

    counties = models.ManyToManyField(County, blank=True, related_name="petitions")
    subjects = models.ManyToManyField(Subject, blank=True, related_name="petitions")

    class Meta:
        ordering = ["date", "serial"]

    def __str__(self):
        return self.title
