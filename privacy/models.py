from django.db import models

class BaseContent(models.Model):
    image = models.ImageField(upload_to="content/", null=True, blank=True)
    description = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-last_updated"]

    def __str__(self):
        return self.description[:50]


class PrivacyPolicy(BaseContent):
    class Meta:
        verbose_name = "Privacy Policy"
        verbose_name_plural = "Privacy Policy"


class AboutUs(BaseContent):
    class Meta:
        verbose_name = "About Us"
        verbose_name_plural = "About Us"


class TermsConditions(BaseContent):
    class Meta:
        verbose_name = "Terms & Conditions"
        verbose_name_plural = "Terms & Conditions"