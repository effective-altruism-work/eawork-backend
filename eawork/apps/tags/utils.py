from typing import Type

from django.db import models
from django.db.models import Model
from enumfields import Enum


class add_tag_fields_and_methods:
    def __init__(self, tag_enum: Type[Enum], tag_model: Type[Model]):
        self.tag_enum = tag_enum
        self.tag_model = tag_model

    def __call__(self, model_cls: Type[Model]):
        for tag_type_enum in self.tag_enum:
            model_field = models.ManyToManyField(
                self.tag_model,
                limit_choices_to={"types__type": tag_type_enum},
                blank=True,
                related_name=f"tags_{tag_type_enum.value}",
            )
            setattr(model_cls, f"tags_{tag_type_enum.value}", model_field)

            tag_getter_method = lambda self: [
                tag.name for tag in getattr(self, f"tags_{tag_type_enum.value}").all()
            ]
            setattr(model_cls, f"tags_{tag_type_enum.value}", tag_getter_method)

        return model_cls
