from datetime import datetime


def parse_czech_date(date_str):
    return datetime.strptime(date_str, "%d. %m. %Y")
