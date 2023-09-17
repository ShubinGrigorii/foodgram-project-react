import os
import json
from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Tag


def read_ingredients():
    with open(os.path.join(settings.BASE_DIR, 'data', 'ingredients.json'),
              'r', encoding='utf-8') as f:
        data = json.load(f)
        for i in range(len(data)):
            Ingredient.objects.get_or_create(
                name=data[i].get("name"),
                measurement_unit=data[i].get("measurement_unit")
            )
    print('Данные из файла ingredients.json загружены')


def read_tags():
    with open(os.path.join(settings.BASE_DIR, 'data', 'tags.json'),
              'r', encoding='utf-8') as f:
        data = json.load(f)
        for i in range(len(data)):
            Tag.objects.get_or_create(
                name=data[i].get("name"),
                slug=data[i].get("slug"),
                color=data[i].get("color")
            )
    print('Данные из файла tags.json загружены')


class Command(BaseCommand):

    def handle(self, *args, **options):
        read_ingredients()
        read_tags()
