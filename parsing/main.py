import requests
import copy
import gettext
import lxml
import re
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd

url = "http://leqtori.gtu.ge:9000/public/groups_X_%E1%83%99%E1%83%95%E1%83%98%E1%83%A0%E1%83%90_04.05.html"
my_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.68",
    "Accept": "text/html,application/xhtml+xml,"
    "application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}

response = requests.get(url, headers=my_headers)
response.encoding = "utf-8"

soup = BeautifulSoup(response.text, "lxml")
# with open("text.txt", "w") as f:
#     f.write(soup.text)

data = soup.find("table", id="table_1635_DETAILED")
group_name = data.find("th").text
table_body = data.find("tbody")
fst_lessons = table_body.find("tr")
first_row_table = table_body.tr


def repeat_next_sib(times, page):
    for i in range(times):
        page = page.next_sibling.next_sibling
    return page


def day_handling(_data_lesson, _cur_day):
    # processing string
    str_cur_day = str(_cur_day)
    if "<br/>" in str_cur_day:  # in case <br> tag
        mod_string = re.sub('<.+">|<\/td>', "", str_cur_day)  # delete open td teg
        mod_string = re.sub(" *<br\/> *", "<br/>", mod_string)  # delete extra spaces
        mod_string = re.split("<br\/>", mod_string, 3)  # spliting by the <br/>
        mod_string = mod_string[:-1]
        for d in range(2, 5):  # insert formated data
            _data_lesson[d] = mod_string[d - 2]

    elif hasattr(_cur_day, "table"):
        if _cur_day.table is not None:  # in case <table> tag
            lst = _cur_day.table.find_all("td")
            for d in range(1, 5):
                _data_lesson[d] = re.sub(" *$", "", lst[d - 1].text)
        else:
            for d in range(1, 5):  # erase all elements except time
                _data_lesson[d] = ""
    else:
        for d in range(1, 5):  # erase all elements except time
            _data_lesson[d] = ""
    return _data_lesson


# days_lesson = repeat_next_sib(3, time_lessons).td

# show all lesson on this time
# i = 4   # choose time
# test_page = repeat_next_sib(i, time_lessons)
# mon_lesson = repeat_next_sib(1, test_page.th)
#
# prev_test_page = repeat_next_sib(i - 1, time_lessons)
# prev_mon_lesson = repeat_next_sib(1, prev_test_page.th)
#
# for k in range(5):
#     cur_day = repeat_next_sib(k, mon_lesson)
#     str_days_lesson = str(cur_day)
#
#     if ' span' in str_days_lesson:
#         prev_row_page = copy.copy(repeat_next_sib(k, prev_mon_lesson))
#         cur_day.replace_with(prev_row_page)
#         if k == 0:
#             mon_lesson = repeat_next_sib(1, test_page.th)
# print(test_page)

# def row_handling(first_row_table):

# show each subject in one hour per week
hours_per_day = 14  # index - teaching hours in the table (0 - 13)
days_per_week = 6

data_lesson = [""] * 5  # main list for capturing data from table
my_column = ["lesson time", "sub-group", "subject", "teacher's name", "Audience"]
df = [None] * days_per_week  # arrays of data frames
for i in range(hours_per_day):
    cur_row_in_table = repeat_next_sib(i, first_row_table)  # select time row
    mon_lesson = repeat_next_sib(1, cur_row_in_table.th)  # select monday in this row

    # same variable for previous day (is used in the case of rowspan)
    if i > 0:
        prev_cur_row_in_table = repeat_next_sib(i - 1, first_row_table)
        prev_mon_lesson = repeat_next_sib(1, prev_cur_row_in_table.th)

    for k in range(days_per_week):  # change k to day
        cur_day = repeat_next_sib(
            k, mon_lesson
        )  # select the day by the index k in the row   #detect comment
        str_days_lesson = str(cur_day)
        # change name str_days to str cur day or change way without text
        # insert the selected time into data_lesson
        data_lesson[0] = re.sub(
            ".*-", "", str(cur_row_in_table.th.text)
        )  # move this out of loop

        if (
            " span" in str_days_lesson
        ):  # copy previous page in case <-- span -->   # maybe ignore this on 9:00
            prev_row_page = copy.copy(
                repeat_next_sib(k, prev_mon_lesson)
            )  # rename this to prev_sub_in_column
            cur_day.replace_with(prev_row_page)
            if k == 0:
                mon_lesson = repeat_next_sib(
                    1, cur_row_in_table.th
                )  # need to update the mon_lesson if found <-- span -->
            cur_day = repeat_next_sib(k, mon_lesson)

        data_lesson = day_handling(data_lesson, cur_day)

        cur_df = pd.DataFrame(
            [data_lesson], columns=my_column
        )  # pack all lessons on current time into week_df
        df[k] = pd.concat([df[k], cur_df], sort=False, ignore_index=True)


with pd.ExcelWriter("output.xlsx") as writer:
    week = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    for i in range(days_per_week):
        df[i].to_excel(writer, sheet_name=week[i])

###################################################
# some problems with monday (don't duplicate 2 row)
# sometimes forget delete tag <td>
# sometimes don't clear sub-group
###################################################
