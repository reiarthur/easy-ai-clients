"""Public music exceptions."""


class MusicInputLimitError(ValueError):
    """Raised when a music generation request exceeds provider input limits.

    Args:
        provider: Required. Public music provider key.
        model: Required. Provider-native model identifier.
        model_key: Required. Standardized model key.
        fields: Required. Mapping of exceeded fields to JSON-serializable
            limit metadata.

    Returns:
        An exception that exposes safe repair data through `to_dict()`.
    """

    def __init__(self, provider, model, model_key, fields):
        self.provider = provider
        self.model = model
        self.model_key = model_key
        self.fields = {
            field: self._field_data(field, data)
            for field, data in fields.items()
        }
        super().__init__(self._message())

    @property
    def repair_prompts(self):
        """Return repair prompts keyed by exceeded field."""
        return {
            field: data["repair_prompt"]
            for field, data in self.fields.items()
        }

    def to_dict(self):
        """Return JSON-serializable repair data."""
        return {
            "provider": self.provider,
            "model": self.model,
            "model_key": self.model_key,
            "fields": self.fields,
        }

    def _message(self):
        field_names = ", ".join(sorted(self.fields))
        return (
            "Music generation input exceeds provider limits "
            f"for {self.provider} {self.model_key}: {field_names}"
        )

    def _field_data(self, field, data):
        item = dict(data)
        item.setdefault("unit", "characters")
        item.setdefault("maximum", None)
        item.setdefault("observed", None)
        item.setdefault(
            "repair_prompt",
            _repair_prompt(
                field,
                item["unit"],
                item["maximum"],
                item["observed"],
            ),
        )
        return item


def _repair_prompt(field, unit, maximum, observed):
    limit_text = f"at most {maximum} {unit}" if maximum is not None else f"within the {unit} limit"
    observed_text = (
        f" The current field is {observed} {unit}."
        if observed is not None
        else ""
    )
    return (
        f"Rewrite the music generation {field} field so it is {limit_text}."
        f"{observed_text} Preserve the user's intent, lyric meaning, language, "
        "section structure, and important musical details as much as possible. "
        "Return only the replacement content for this one field. Do not return "
        "JSON, Markdown, commentary, labels, or explanations."
    )
