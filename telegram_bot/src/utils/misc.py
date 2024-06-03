from ..rest import get_pathways


def detect_language(text: str):
    text = text.lower()
    for char in text.lower():
        if "a" <= char <= "z":
            return "en"
        elif "а" <= char <= "я":
            return "ru"
        elif "ა" <= char <= "ჰ":
            return "ka"


class Paginator:
    def __init__(self, array: list | tuple, page: int = 1, per_page: int = 1):
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)
        self.pages = self.len // self.per_page + (self.len % self.per_page > 0)

    def _get_slice(self):
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def get_page(self):
        page_items = self._get_slice()
        return page_items

    def has_next(self):
        if self.page < self.pages:
            return self.page + 1
        return False

    def has_previous(self):
        if self.page > 1:
            return self.page - 1
        return False

    def get_next(self):
        if self.page < self.pages:
            self.page += 1
            return self.get_page()
        raise IndexError(f"Next page does not exist. Use has_next() to check before.")

    def get_previous(self):
        if self.page > 1:
            self.page -= 1
            return self._get_slice()
        raise IndexError(
            f"Previous page does not exist. Use has_previous() to check before."
        )


async def get_located_pathways(locale: str):
    pathways = await get_pathways()
    pathways = [
        pathway for pathway in pathways if detect_language(pathway["title"]) == locale
    ]

    return pathways
