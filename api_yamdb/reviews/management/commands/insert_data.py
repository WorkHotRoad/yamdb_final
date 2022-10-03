import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from reviews import models

FILES_MODELS = {
    "category.csv": "Category",
    "genre.csv": "Genre",
    "titles.csv": "Title",
    "review.csv": "Review",
    "comments.csv": "Comment",
    "users.csv": "User",
    "genre_title.csv": "GenreTitle",
}

PK_FIELDS = {"author": "User", "category": "Category"}


class Command(BaseCommand):
    def send_to_db(self, fields, values, model_name):
        model = getattr(models, model_name)
        model.objects.all().delete()

        # Заменим числа на объекты, где встречаются ForeignKey
        # Если название поля есть в PK_FIELDS, то это ключ, а не просто число
        fks = []
        for word in fields:
            if word in PK_FIELDS and len(word) > 2:
                fk_index = fields.index(word)
                fk_obj = getattr(models, PK_FIELDS.get(word))
                fks.append((fk_index, fk_obj))

        for row in values:
            # Если список ключей не пуст, надо найти объекты и записать по
            # нужным индексам
            if fks:
                for fk in fks:
                    fk_ind = fk[0]
                    fk_obj = fk[1]
                    found_obj = fk_obj.objects.get(pk=row[fk_ind])
                    row[fk_ind] = found_obj

            new_row = dict(zip(fields, row))
            model.objects.create(**new_row)

    def handle(self, *args, **kwargs):
        files_dir = os.path.join(settings.STATICFILES_DIRS[0], "data")
        # Надежнее вручную установить порядок обработки файлов,
        # т.к. они могут зависеть от данных в других файлах
        # Сначала хотел брать их из аргументов, но не нашел смысла в этом.
        filenames = [
            "users.csv",
            "review.csv",
            "comments.csv",
            "category.csv",
            "titles.csv",
            "genre.csv",
            "genre_title.csv",
        ]
        for filename in filenames:
            model_name = FILES_MODELS.get(filename)
            # Добавляем данные только в модели, которые уже созданы в БД
            if not hasattr(models, model_name):
                continue

            file_path = os.path.join(files_dir, filename)
            with open(file_path, encoding="UTF-8") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=",")
                fields, values = [], []
                for idx, row in enumerate(csv_reader):
                    if row == "":
                        continue
                    # Названия полей сохраняем отдельно
                    if idx == 0:
                        fields = [word.strip() for word in row]
                        continue
                    values.append([word.strip() for word in row])

                self.send_to_db(fields, values, model_name)
