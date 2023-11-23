import sqlite3
from yaml import safe_load as yload
from googletrans import Translator

# # connect yaml file with sql expressions
with open("creation_query.yml", encoding="utf8") as file:
    req = yload(file)

# # turn on save data
# connection = sqlite3.connect(':memory:')

# # also save, but i don't know why
connection = sqlite3.connect("test.db")
cursor = connection.cursor()


def execute_query_yaml(path: str):
    try:
        cursor.executescript(req["sql"][path])
        connection.commit()
        print("Query executed successfully")
    except Exception as e:
        print(str(e))
        print("Execute failed")


def create_database():
    try:
        cursor.executescript(req["sql"]["create_tables"])
        connection.commit()
        print("Database created successfully")

        cursor.executescript(req["sql"]["insert_startup_data"])
        connection.commit()
        print("Default data executed successfully")

    except Exception as e:
        print(str(e))
        print("Create database failed")


def check_duplicate_text_content(list: list):  # list must be [m, n, k]
    find = 0
    for x in list:
        cursor.execute(
            """SELECT text_content_id 
                 FROM text_content 
                WHERE text_translation = ? 
             ORDER BY 1 DESC
                LIMIT 1""",
            [x],
        )
        results = cursor.fetchall()
        if results != []:
            find += 1
    if find > 0:
        return False
    else:
        return True


def add_teacher(lang1: str, name1: str, lang2: str, name2: str, lang3: str, name3: str):
    teacher = [
        (lang1, name1, lang2, name2, lang3, name3),
    ]

    if check_duplicate_text_content(teacher[0][1::2]):
        try:
            cursor.executemany(
                """INSERT INTO text_content (text_content_id, language_id, text_translation)
                        VALUES ((SELECT MAX(text_content_id) + 1 FROM text_content), ?, ?),
                               ((SELECT MAX(text_content_id) + 1 FROM text_content), ?, ?),
                               ((SELECT MAX(text_content_id) + 1 FROM text_content), ?, ?); """,
                teacher,
            )

            cursor.execute(
                """INSERT INTO teacher (text_content_id)
                        VALUES ((SELECT MAX(text_content_id) FROM text_content))"""
            )
            connection.commit()
            print("Add_teacher executed successfully")
        except Exception as e:
            print(str(e))
            print("Execute add_teacher failed")
    else:
        print("Duplicate error, 0 rows affected")


def add_faculty(lang1: str, name1: str, lang2: str, name2: str, lang3: str, name3: str):
    faculty = [
        (lang1, name1, lang2, name2, lang3, name3),
    ]

    if check_duplicate_text_content(faculty[0][1::2]):
        try:
            cursor.executemany(
                """INSERT INTO text_content (text_content_id, language_id, text_translation)
                        VALUES ((SELECT MAX(text_content_id) + 1 FROM text_content), ?, ?),
                               ((SELECT MAX(text_content_id) + 1 FROM text_content), ?, ?),
                               ((SELECT MAX(text_content_id) + 1 FROM text_content), ?, ?); """,
                faculty,
            )

            cursor.execute(
                """INSERT INTO faculty (text_content_id)
                        VALUES ((SELECT MAX(text_content_id) FROM text_content))"""
            )
            connection.commit()
            print("Add_faculty executed successfully")
        except Exception as e:
            print(str(e))
            print("Execute add_faculty failed")
    else:
        print("Duplicate error, 0 rows affected")


def add_subject_type(
    lang1: str, name1: str, lang2: str, name2: str, lang3: str, name3: str
):
    subject_type = [
        (lang1, name1, lang2, name2, lang3, name3),
    ]

    if check_duplicate_text_content(subject_type[0][1::2]):
        try:
            cursor.executemany(
                """INSERT INTO text_content (text_content_id, language_id, text_translation)
                        VALUES ((SELECT MAX(text_content_id) + 1 FROM text_content), ?, ?),
                               ((SELECT MAX(text_content_id) + 1 FROM text_content), ?, ?),
                               ((SELECT MAX(text_content_id) + 1 FROM text_content), ?, ?); """,
                subject_type,
            )

            cursor.execute(
                """INSERT INTO subject_type (text_content_id)
                        VALUES ((SELECT MAX(text_content_id) FROM text_content))"""
            )
            connection.commit()
            print("Add_subject_type executed successfully")
        except Exception as e:
            print(str(e))
            print("Execute add_subject_type failed")
    else:
        print("Duplicate error, 0 rows affected")


def translate_to_ru(txt: str):
    translator = Translator()
    txt = translator.translate(text=txt, dest="ru")
    return txt.text


def translate_to_ka(txt: str):
    translator = Translator()
    txt = translator.translate(text=txt, dest="ka")
    return txt.text


def translate_to_en(txt: str):
    translator = Translator()
    txt = translator.translate(text=txt, dest="en")
    return txt.text


def translate_to_en_ru_ka(txt: str) -> list:
    # detect a language
    translator = Translator()
    detect_lang = translator.detect(txt)
    detect_lang = detect_lang.lang

    # group by alphabets
    cyrillic = ["ru", "bg"]
    latin = ["en"]
    mkhedruli = ["ka"]

    # translate to other 2 lang
    txt_en = txt_ka = txt_ru = txt
    if any(lang == detect_lang for lang in mkhedruli):
        txt_en = translate_to_en(txt)
        txt_ru = translate_to_ru(txt)
    elif any(lang == detect_lang for lang in latin):
        txt_ka = translate_to_ka(txt)
        txt_ru = translate_to_ru(txt)
    elif any(lang == detect_lang for lang in cyrillic):
        txt_ka = translate_to_ka(txt)
        txt_en = translate_to_en(txt)
    else:
        print("Detected language: ", detect_lang)
        raise ValueError(
            f"Detect language failed \nWord: {text}, detected language: {detect_lang}"
        )
    return ["en", txt_en, "ru", txt_ru, "ka", txt_ka]


if __name__ == "__main__":
    text = "Практика"
    print(translate_to_en_ru_ka(text))
    add_subject_type(*translate_to_en_ru_ka("Практика"))

    faculty_1 = [
        "en",
        "Lecture",
        "ru",
        "Лекция",
        "ka",
        "ლექცია",
    ]

    # commit command
    connection.commit()

    # close connection
    connection.close()

# add_subject_type(*faculty_1)

# """INSERT INTO teacher (text_content_id)
#         VALUES ((SELECT MAX(text_content_id) FROM text_content))"""

# # how insert variable in query
# day = "Jopa"
# cursor.execute(f"INSERT INTO Week (day) VALUES ('{day}')")

# whole_week = [
#     ("Monday"),
#     ("Tuesday"),
#     ("Wednesday"),
#     ("Thursday"),
#     ("Friday"),
#     ("Saturday"),
#     ("Sunday"),
# ]

# cursor.executemany("INSERT INTO Week (day) VALUES (?)", zip(whole_week))

# cursor.execute("DELETE FROM Week")

# # reset autoincrement for Week table
# cursor.execute(
#     """
#     UPDATE sqlite_sequence
#        SET seq = 0
#      WHERE name = 'week'  # instead of 'week' paste table name
# """
# )

# # Query the Database without yml
# cursor.execute("SELECT * FROM week")
# results = cursor.fetchall()
# for result in results:
#     print(result)


# print(req["sql"]["select_week_all"])
# cursor.execute(req["sql"]["select_week_all"])
# results = cursor.fetchall()
# for result in results:
#     print(result)
