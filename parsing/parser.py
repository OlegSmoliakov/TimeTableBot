import asyncio
import hashlib
import json
import logging as log
import math
import os
import re
import time

from datetime import datetime, timedelta

import aiohttp
import bs4
import requests
import uvloop

from bs4 import BeautifulSoup
from tabula import read_pdf

# Get environment variables
USER_AGENT = os.environ["USER_AGENT"]
ACCEPT = os.environ["ACCEPT"]
MY_HEADERS = {"User-Agent": USER_AGENT, "Accept": ACCEPT}
TAG_STRONG_GROUPS = os.environ["TAG_STRONG_GROUPS"]
TAG_STRONG_TEACHERS = os.environ["TAG_STRONG_TEACHERS"]
TAG_STRONG_INFORMATICS = os.environ["TAG_STRONG_INFORMATICS"]
URL_LEQTORI = os.environ["URL_LEQTORI"]
URL_REST = os.environ["URL_REST"]
MAX_CONNECTIONS = int(os.environ["MAX_CONNECTIONS"])
FORCE_TO_COLLECT = os.environ["FORCE_TO_COLLECT"]

# Settings
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# For debug
N_FIRST_TABLES_TO_COLLECT = int(os.environ["N_FIRST_TABLES_TO_COLLECT"])


class Leqtori:
    def __init__(self, url_leqtori=URL_LEQTORI):
        self.url_leqtori = url_leqtori
        self.leqtori_text = self.get_page_text(url_leqtori)
        self.leqtori_soup = BeautifulSoup(self.leqtori_text, "lxml")

    def get_page_text(self, url):
        with requests.get(url, headers=MY_HEADERS) as response:
            response.encoding = "utf-8"
            response.raise_for_status()
            page_text = response.text

        return page_text

    def get_page_soup(self, url):
        page_text = self.get_page_text(url)
        page_soup = BeautifulSoup(page_text, "lxml")

        return page_soup

    def get_page_url_from_leqtori(self, strong_tag):
        for a in self.leqtori_soup.find_all("a", href=True):
            if a.find("strong", string=strong_tag):
                return a["href"]


class Lesson:
    __slots__ = [
        "subjectName",
        "group",
        "subgroup",
        "lessonType",
        "professor",
        "classroom",
        "weekDay",
        "startTime",
        "hoursSpan",
    ]

    def __init__(
        self,
        subjectName="",
        group="",
        subgroup="",
        lessonType="",
        professor="",
        classroom="",
        weekDay="",
        startTime="",
        hoursSpan=0,
    ):
        self.subjectName = subjectName
        self.group = group
        self.subgroup = subgroup
        self.lessonType = lessonType
        self.professor = professor
        self.classroom = classroom
        self.weekDay = weekDay
        self.startTime = startTime
        self.hoursSpan = hoursSpan

    def to_dict(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def __repr__(self):
        return f"Lesson: {self.to_dict()}"

    def __str__(self):
        return f"Lesson: {self.to_dict()}"


class Timetable:
    __slots__ = ["_group", "lessons"]

    def __init__(self, group=""):
        self._group = group
        self.lessons = []

    def add_lesson(self, lesson: Lesson):
        self.lessons.append(lesson)

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, new_group):
        if self.lessons:
            self._update_group(new_group)

        self._group = new_group

    def _update_group(self, new_group):
        for lesson in self.lessons:
            lesson.group = new_group
            # if lesson.subgroup:
            #     pattern = rf"{new_group}\.(\d+-\d+)"
            #     match = re.search(pattern, lesson.subgroup)
            #     lesson.subgroup = match.group(1)

    def __repr__(self):
        return f"Timetable(group={self._group}, lessons={self.lessons})"

    def __str__(self):
        return f"Timetable(group={self._group}, lessons={self.lessons})"

    def __iter__(self):
        return iter(self.lessons)

    def __len__(self):
        return len(self.lessons)

    def __add__(self, other):
        if not isinstance(other, Timetable):
            raise TypeError(
                f"Unsupported operand type for +: 'Timetable' and {type(other)}"
            )
        if self.group != other.group:
            raise ValueError("Timetables must have the same group to be combined.")
        combined_timetable = Timetable(group=self.group)
        combined_timetable.lessons.extend(self.lessons)
        combined_timetable.lessons.extend(other.lessons)
        return combined_timetable

    def to_dict(self):
        return {self.group: [lesson.to_dict() for lesson in self.lessons]}

    def combine_common_lessons(self):
        # Group lessons by common fields
        grouped_lessons = {}
        for lesson in self.lessons:
            key = (
                lesson.subjectName,
                lesson.group,
                lesson.subgroup,
                lesson.lessonType,
                lesson.weekDay,
            )
            if key not in grouped_lessons:
                grouped_lessons[key] = []
            grouped_lessons[key].append(lesson)

        # Sort and combine lessons
        combined_lessons = []
        for key, group in grouped_lessons.items():
            group.sort(key=lambda lesson: lesson.startTime)
            combined_group = [group[0]]
            for lesson in group[1:]:
                last_lesson = combined_group[-1]
                last_lesson_time = datetime.strptime(last_lesson.startTime, "%H:%M:%S")
                lesson_time = datetime.strptime(lesson.startTime, "%H:%M:%S")
                if lesson_time - last_lesson_time <= timedelta(hours=1):
                    last_lesson.hoursSpan += lesson.hoursSpan
                else:
                    combined_group.append(lesson)
            combined_lessons.extend(combined_group)

        self.lessons = combined_lessons


class Schedule_Service_API:
    amount_pathways = 0
    amount_groups = 0
    amount_lessons = 0

    sent_groups = 0
    sent_pathways = 0
    sent_lessons = 0

    def __init__(self, url_rest=URL_REST, max_connections=MAX_CONNECTIONS) -> None:
        self.url_rest = url_rest
        self.session = aiohttp.ClientSession()
        self.semaphore = asyncio.Semaphore(max_connections)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def send_group(self, group_name: str, pathway_name: str):
        group = {"title": group_name, "pathwayTitle": pathway_name}
        url_group = self.url_rest + "/groups"

        async with self.semaphore:
            async with self.session.post(url_group, data=group) as response:
                if response.status == 200:
                    self.sent_groups += 1
                    log.debug(
                        f"Group {group_name}, {pathway_name} sent to REST. {self.sent_groups}/{self.amount_groups} groups sent."
                    )
                else:
                    log.error(
                        f"Group {group_name} with pathway_name {pathway_name} NOT sent to REST."
                    )
                    response_json = await response.json()
                    response_json["group_name"] = group_name
                    response_json["pathway_name"] = pathway_name
                    response_json = json.dumps(
                        response_json, indent=4, ensure_ascii=False
                    )

                    exit(f"Error response: {response_json}")

    async def send_pathway(self, pathway: str):
        pathway = {"title": str(pathway)}
        url_pathways = self.url_rest + "/pathways"

        async with self.semaphore:
            async with self.session.post(url_pathways, data=pathway) as response:
                if response.status == 200:
                    self.sent_pathways += 1
                    log.debug(
                        f"Pathway {pathway['title']} sent to REST. {self.sent_pathways}/{self.amount_pathways} pathways sent."
                    )
                else:
                    log.error(f"Pathway {pathway} NOT sent to REST.")
                    try:
                        response_json = await response.json()
                    except:
                        response_json = await response.text()
                        response_json = {"error": response_json}
                    response_json["pathway"] = pathway
                    response_json = json.dumps(
                        response_json, indent=4, ensure_ascii=False
                    )
                    exit(f"Error response: {response_json}")

    async def send_timetable_recreate(self):
        url_recreate = self.url_rest + "/timetable/recreate"
        async with self.session.post(url_recreate) as response:
            if response.status == 200:
                log.debug("Recreate request sent to REST.")
            else:
                log.error("Recreate request NOT sent to REST.")
                response_json = await response.json()
                response_json = json.dumps(response_json, indent=4, ensure_ascii=False)
                exit(f"Error response: {response_json}")

    async def send_lesson(self, lesson: dict):
        url_lessons = self.url_rest + "/lessons"
        retries = 3

        for i in range(retries):
            try:
                if self.session.closed:
                    await self.session.close()
                    self.session = aiohttp.ClientSession()

                async with self.semaphore:
                    async with self.session.post(url_lessons, json=lesson) as response:
                        if response.status == 200:
                            self.sent_lessons += 1

                            log.debug(
                                f"Group {lesson['group']} lesson sent to REST. {self.sent_lessons}/{self.amount_lessons} lessons sent."
                            )
                            break
                        elif response.status != 500:
                            log.error(f"Lesson {lesson} NOT sent to REST.")
                            response_json = await response.json()
                            response_json["lesson"] = lesson
                            response_json = json.dumps(
                                response_json, indent=4, ensure_ascii=False
                            )
                            log.error(f"Error response: {response_json}")
                        else:
                            response_text = await response.text()
                            lesson["error_code"] = 500
                            lesson["response_text"] = response_text
                            lesson = json.dumps(lesson, indent=4, ensure_ascii=False)
                            exit(f"Error response: {lesson}")
            except (
                aiohttp.ServerDisconnectedError,
                aiohttp.ClientOSError,
                aiohttp.ClientConnectionError,
            ):
                if i < retries:
                    await asyncio.sleep(2**i)
                    continue
                else:
                    raise

    async def send_pathways(self, headers: dict[str, dict[str, dict]]):
        tasks = []
        for pathways in headers.values():
            for pathway_title in pathways:
                task = asyncio.create_task(self.send_pathway(pathway_title))
                tasks.append(task)

        self.amount_pathways = len(tasks)
        await asyncio.gather(*tasks)
        return log.info("Pathways successfully sent to REST.")

    async def send_groups(self, amount_to_send, headers: dict[str, dict[str, dict]]):
        tasks = []
        for pathways in headers.values():
            for pathway_title, groups in pathways.items():
                for group_name in groups.values():
                    task = asyncio.create_task(
                        self.send_group(group_name, pathway_title)
                    )
                    tasks.append(task)

                    if amount_to_send > 1:
                        amount_to_send -= 1
                    else:
                        self.amount_groups = len(tasks)
                        await asyncio.gather(*tasks)
                        return log.info("Groups successfully sent to REST.")

    async def send_lessons(self, timetables: list[Timetable]):
        tasks = []
        for timetable in timetables:
            for lesson in timetable:
                task = asyncio.create_task(self.send_lesson(lesson.to_dict()))
                tasks.append(task)

        self.amount_lessons = len(tasks)
        await asyncio.gather(*tasks)
        log.info("All data successfully sent to REST.")

    async def send_data_to_rest(
        self, timetables: list[Timetable], headers: dict[str, dict[str, dict]]
    ):
        await self.send_timetable_recreate()
        amount_to_send = len(timetables)

        await self.send_pathways(headers)
        await self.send_groups(amount_to_send, headers)
        await self.send_lessons(timetables)


class Scraper:

    WEEK_DICT = {
        0: "Mon",
        1: "Tue",
        2: "Wed",
        3: "Thu",
        4: "Fri",
        5: "Sat",
    }

    def __init__(self, url_leqtori=URL_LEQTORI):
        self.url_leqtori = url_leqtori

    @staticmethod
    def get_first_n_timetables_dict(timetables_dict, n: int = -1):
        if n == -1 or n > len(timetables_dict):
            return timetables_dict
        return dict(list(timetables_dict.items())[:n])

    @staticmethod
    def li_processing(li: BeautifulSoup) -> dict[str, str]:
        a = li.a
        group_title = a.string.strip()
        table_id = a["href"].split("#")[1]
        group = {table_id: group_title}

        return group

    @staticmethod
    def parse_groups(ul: BeautifulSoup) -> dict[str, str]:
        second_level_li = ul.li
        groups = {}

        li_siblings = [second_level_li] + [
            sibling for sibling in second_level_li.next_siblings if sibling.name == "li"
        ]

        for sibling in li_siblings:
            group = Scraper.li_processing(sibling)
            groups.update(group)

        return groups

    @staticmethod
    def parse_pathway_titles(pathway_header: str) -> tuple[str, str]:
        text_to_remove = ["Программа", "პროგრამა", "'s Program"]

        try:
            degree_title, pathway_title = pathway_header.split("-", 1)

            for substring in text_to_remove:
                degree_title = degree_title.replace(substring, "").strip()
            if degree_title == "ბაკალავრი":
                degree_title = "ბაკალავრიატი"

            pathway_title = pathway_title
        except ValueError:
            log.debug(f"No '-' in pathway_header {pathway_header.strip()}")
            degree_title = None
            pathway_title = pathway_header

        for substring in text_to_remove:
            pathway_title = pathway_title.replace(substring, "").strip()

        return degree_title, pathway_title

    @staticmethod
    def parse_pathway(first_level_li: BeautifulSoup):
        pathway_header = next(first_level_li.strings)
        degree_title, pathway_title = Scraper.parse_pathway_titles(pathway_header)
        groups = Scraper.parse_groups(first_level_li.ul)
        pathway = {pathway_title: groups}

        return degree_title, pathway

    @staticmethod
    def headers_processing(
        timetable_page_soup: bs4.BeautifulSoup,
    ) -> dict[str, dict[str, dict]]:
        li_first_level = timetable_page_soup.body.ul.li
        degrees = {}

        li_siblings = [li_first_level] + [
            sibling for sibling in li_first_level.next_siblings if sibling.name == "li"
        ]

        for sibling in li_siblings:
            degree_title, pathway = Scraper.parse_pathway(sibling)
            try:
                degrees[degree_title].update(pathway)
            except KeyError:
                degrees[degree_title] = pathway

        return degrees

    def headers_to_timetables_dict(self):
        timetables_id_names = {}
        for pathways in self.headers.values():
            for groups in pathways.values():
                timetables_id_names.update(groups)

        return timetables_id_names

    def row_collecting(self, table: BeautifulSoup) -> Timetable:
        """processes all tr tags"""

        self.group_name = table.thead.tr.th.get_text(strip=True)
        sibling = table.tbody.tr
        timetable = Timetable()

        while sibling is not None:
            if sibling.name == "tr":
                row_timetable = self.cell_collecting(sibling)
                timetable += row_timetable

            sibling = sibling.next_sibling

        timetable.group = self.group_name
        return timetable

    @staticmethod
    def time_processing(row: BeautifulSoup) -> str:
        time = row.find("th").get_text(strip=True)
        time = re.sub(r"\d+-", "", time)
        time = datetime.strptime(time, "%H:%M").strftime("%H:%M:%S")

        return time

    def cell_collecting(self, row: BeautifulSoup) -> Timetable:
        """proces all td tags"""

        time = Scraper.time_processing(row)
        shift = 0
        day = 0
        sibling = row.th.next_sibling
        timetable = Timetable()

        while sibling is not None:
            name = sibling.name
            if name == "td":
                if "class" in sibling.attrs.keys():
                    day -= 1
                    continue

                lessons = self.cell_processing(sibling)

                if lessons is not None:
                    for lesson in lessons:
                        lesson.startTime = time
                        lesson.weekDay = Scraper.WEEK_DICT[day + shift]
                        timetable.add_lesson(lesson)
                day += 1
            elif sibling == " span ":
                # elif sibling.name == "span":
                shift += 1

            sibling = sibling.next_sibling

        return timetable

    @staticmethod
    def count_td_tag(table_tr: BeautifulSoup) -> int:
        """count td tags in tr tag"""
        td = table_tr.find_all("td")
        return len(td)

    @staticmethod
    def cell_table_processing(cell: BeautifulSoup):
        """processes table inside <td> tag of other table"""
        table = cell.table

        trs = table.find_all("tr")
        count = Scraper.count_td_tag(trs[0])
        contents = [[] for _ in range(count)]

        for tr in trs:
            tds = tr.find_all("td")
            for i, td in enumerate(tds):
                contents[i].append(td.get_text(strip=True))

        return contents

    @staticmethod
    def separate_subjectName(subjectName: str) -> tuple[str, str]:
        subjectName, lessonType = re.findall(r"(.+\(.+\))(.+)", subjectName, re.DOTALL)[
            0
        ]
        lessonType = lessonType.strip()
        return subjectName, lessonType

    def get_lesson(self, tag_content: list) -> Lesson:
        tag_len = len(tag_content)
        subgroup = None

        if tag_len > 4:
            log.warning(f"Cell contain more than 4 element: {tag_content}")
        elif tag_len == 4:
            # if len(tag_content[-4]) > 20:
            #     log.warning(
            #         f"Cell contain more than 20 symbols in subgroup field: {tag_content[-4]}"
            #     )
            subgroup = tag_content[-4]
            pattern = rf"{self.group_name}\.(\d+-\d+)"
            match = re.search(pattern, subgroup)
            if match:
                subgroup = match.group(1)
            else:
                log.warning(f"Subgroup field doesn't match pattern: {tag_content[-4]}")
                subgroup = None
        elif tag_len < 3:
            log.warning(f"Cell contain less than 3 element: {tag_content}")
            assert not re.findall(r"\b\d{2}-[\w.]+", tag_content[-1])
            tag_content.append(None)

        subjectName, lessonType = Scraper.separate_subjectName(tag_content[-3])
        professor = tag_content[-2]
        classroom = tag_content[-1]

        lesson = Lesson(subjectName, None, subgroup, lessonType, professor, classroom)

        return lesson

    def cell_processing(self, cell: BeautifulSoup) -> list[Lesson]:
        # skip non info cell
        text = cell.get_text(strip=True)
        if not text or text == "---":
            return None

        if "rowspan" in cell.attrs.keys():
            hoursSpan = int(cell.attrs["rowspan"])
        else:
            hoursSpan = 1

        lessons = []

        if cell.table is None:
            content = [
                x.get_text(strip=True)
                for x in cell.contents
                if x.name != "br" and x != "\n"
            ]
            lesson = self.get_lesson(content)
            lesson.hoursSpan = hoursSpan
            lessons.append(lesson)
        else:
            contents = Scraper.cell_table_processing(cell)
            for content in contents:
                lesson = self.get_lesson(content)
                lesson.hoursSpan = hoursSpan
                lessons.append(lesson)

        return lessons

    # NOTE check is useful or not
    def save_soup_to_txt(self):
        with open("text.txt", "w") as f:
            f.write(self.timetable_page_soup.text)

    def timetables_processing(
        self, soup_timetables: dict[str, bs4.NavigableString], timetables_id_name: dict
    ) -> list[Timetable]:
        groups = []

        for table_id, group_name in timetables_id_name.items():
            log.debug(f"Processing table: '{group_name}', id: '{table_id}'")
            try:
                timetable_data = self.row_collecting(soup_timetables[table_id])
                timetable_data.combine_common_lessons()
                groups.append(timetable_data)
            except Exception as e:
                log.error(
                    f"Error processing table (group: '{group_name}', id: '{table_id}'): {e}"
                )

        amount_parsed = len(groups)
        amount_not_parsed = len(timetables_id_name) - amount_parsed

        log.info(f"{amount_parsed} tables have been parsed.")
        if amount_not_parsed:
            log.error(f"{amount_not_parsed} tables weren't been parsed.")

        return groups

    def recreate_timetable(self):
        with aiohttp.ClientSession as session:
            session.post(f"{self.url_rest}/timetable/recreate")

    def collect_soup_timetables(self, first_table_id: str):
        """
        Collects soup timetables from a BeautifulSoup object based on the provided first_table_id.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the HTML.
            first_table_id (str): The id of the table to search for.

        Returns:
            dict: A dictionary containing the soup timetables, where the keys are the table ids and the values are the corresponding tables.
        """
        first_table = self.timetable_page_soup.find("table", id=first_table_id)
        soup_timetables = {first_table_id: first_table}
        sibling = first_table.next_sibling

        while sibling is not None:
            if "table" == sibling.name and "_DETAILED" in sibling.attrs["id"]:
                soup_timetables[sibling.attrs["id"]] = sibling

            sibling = sibling.next_sibling

        return soup_timetables

    def collect_timetables(self, tables_to_collect: int = -1):
        timetables_dict = self.headers_to_timetables_dict()
        timetables_id_name = self.get_first_n_timetables_dict(
            timetables_dict, tables_to_collect
        )
        soup_timetables = self.collect_soup_timetables(next(iter(timetables_id_name)))
        timetables = self.timetables_processing(soup_timetables, timetables_id_name)

        return timetables

    # FIXME: finish it later
    def pdf_processing(filename):

        df = read_pdf(
            filename,
            pages="all",
            output_format="dataframe",
            multiple_tables=True,
            lattice=True,
        )
        df = pd.DataFrame(
            df[0].values, columns=["group", "subject", "lector", "date", "time", "room"]
        )
        for i in range(16, 19):  # df.shape[0]):
            room = df.iloc[i, -1]
            if isinstance(room, float) and math.isnan(room):
                df.iloc[i, :] = df.iloc[i, :].shift()
        # df.to_csv(f"{filename}.csv", index=False)

        timetables = {}

        return timetables

    def get_timetables_from_webpage(self, page_url, tables_to_collect: int = -1):

        if ".pdf" in page_url:
            filename = download_pdf(page_url)
            timetables = self.pdf_processing(filename)
        else:
            log.info(f"Download data from {page_url}")
            response = requests.get(page_url)
            response.encoding = "utf-8"
            timetable_page_text = response.text

            log.info(f"Making soup from {page_url}...")
            self.timetable_page_soup = BeautifulSoup(timetable_page_text, "lxml")
            log.info(f"Start processing {page_url}...")
            self.headers = self.headers_processing(self.timetable_page_soup)
            timetables = self.collect_timetables(tables_to_collect)

        return timetables, self.headers

    def get_timetables_from_file(self, file_path, tables_to_collect: int = -1):
        with open(file_path, "r", encoding="utf-8") as f:
            timetable_page_text = f.read()

        self.timetable_page_soup = BeautifulSoup(timetable_page_text, "lxml")
        self.headers = self.headers_processing(self.timetable_page_soup)
        timetables = self.collect_timetables(tables_to_collect)

        return timetables, self.headers


def measure_execution_time(func):
    start_time = time.time()
    result = func()
    end_time = time.time()
    print(f"Execution time of {func.__name__}: {end_time - start_time} seconds")
    return result


def save_timetables_to_json(timetables: list[Timetable], filename="timetables.json"):
    timetables = [timetable.to_dict() for timetable in timetables]

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(timetables, f, indent=4, ensure_ascii=False)
    log.info(f"Timetables saved to {filename}")


def check_website_for_changes(webpage_text: str):
    current_hash = calculate_hash(webpage_text)
    prev_hash = read_hash_from_file()

    if prev_hash is None:
        log.info("Hash file not found. Creating a new one.")
        save_hash_to_file(current_hash)
        return True
    elif current_hash != prev_hash:
        log.info("Website content has changed!")
        save_hash_to_file(current_hash)
        return True
    else:
        log.info("Website content has not changed. Aborting...")
        return False


# FIXME
def download_pdf(timetable_link):
    filename = timetable_option.split("/")[1]
    filename = filename.replace(" ", "_")
    filename = f"{filename}.pdf"

    if os.path.exists(filename):
        print("Timetable is already downloaded.")
    else:
        print("Timetable is in PDF format. Downloading...")
        response = requests.get(timetable_link)

        pdf = open(filename, "wb")
        pdf.write(response.content)
        pdf.close()

    return filename


def calculate_hash(content):
    sha256_hash = hashlib.sha256()
    sha256_hash.update(content.encode())
    return sha256_hash.hexdigest()


def read_hash_from_file(filename="hash.txt"):
    try:
        with open(filename, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        return None


# FIXME: finish it later
def send_hash_outside_the_docker(hash_value):
    print(hash_value)


def save_hash_to_file(hash_value, filename="hash.txt"):
    path = os.path.join(os.getcwd(), filename)
    log.info(f"Saving hash to file: {path}")
    with open(filename, "w") as file:
        file.write(hash_value)


def calc_max_length_headers(headers: dict[list[dict]]):
    max_length = {
        "degree_title": 0,
        "pathway_title": 0,
        "group_title": 0,
    }
    for degree in headers:
        if degree is None:
            continue
        length = len(degree)
        if length > max_length["degree_title"]:
            max_length["degree_title"] = length
        for program in headers[degree]:
            for program_name, groups in program.items():
                length = len(program_name)
                if length > max_length["pathway_title"]:
                    max_length["pathway_title"] = length
                for group in groups.values():
                    length = len(group)
                    if length > max_length["group_title"]:
                        max_length["group_title"] = length
    print(json.dumps(max_length, indent=4))

    return max_length


def calc_max_length_timetables(timetables):
    max_length = {
        "subjectName": 0,
        "group": 0,
        "subgroup": 0,
        "lessonType": 0,
        "professor": 0,
        "classroom": 0,
        "weekDay": 0,
        "startTime": 0,
        "hoursSpan": 0,
    }
    for timetable in timetables:
        for lesson in timetable:
            data = lesson.to_dict()
            for key, value in data.items():
                length = len(str(value))
                if length > max_length[key]:
                    max_length[key] = length
    print(json.dumps(max_length, indent=4))

    return max_length


async def send_data_to_rest(timetables: list[Timetable], headers: dict[list[dict]]):
    log.info("Sending pathways, groups and sessons to REST API...")
    async with Schedule_Service_API() as api:
        await api.send_data_to_rest(timetables, headers)


async def main():
    log.info("Starting the program...")
    start_time = time.time()
    leqtori = Leqtori()

    if FORCE_TO_COLLECT == "true" or check_website_for_changes(leqtori.leqtori_text):
        scraper = Scraper()
        page_url = leqtori.get_page_url_from_leqtori(TAG_STRONG_GROUPS)
        timetables, headers = scraper.get_timetables_from_webpage(
            page_url, N_FIRST_TABLES_TO_COLLECT
        )

        await send_data_to_rest(timetables, headers)

    execute_time = time.time() - start_time
    hours, remainder = divmod(execute_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    log.info(f"Execution time: {int(hours):02}:{int(minutes):02}:{seconds:06.3f}")


if __name__ == "__main__":
    log_level = os.environ["LOG_LEVEL"]
    log_level = getattr(log, log_level.upper())
    log.basicConfig(
        level=log_level,
        format="%(asctime)s: %(levelname)s: %(message)s",
    )

    asyncio.run(main())
