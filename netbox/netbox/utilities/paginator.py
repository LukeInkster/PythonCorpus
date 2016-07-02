from django.conf import settings
from django.core.paginator import Paginator, Page


class EnhancedPaginator(Paginator):

    def __init__(self, object_list, per_page, **kwargs):
        per_page = getattr(settings, 'PAGINATE_COUNT', 50)
        super(EnhancedPaginator, self).__init__(object_list, per_page, **kwargs)

    def _get_page(self, *args, **kwargs):
        return EnhancedPage(*args, **kwargs)


class EnhancedPage(Page):

    def smart_pages(self):

        # Show first page, last page, next/previous two pages, and current page
        n = self.number
        pages_wanted = [1, n - 2, n - 1, n, n + 1, n + 2, self.paginator.num_pages]
        page_list = sorted(set(self.paginator.page_range).intersection(pages_wanted))

        # Insert skip markers
        skip_pages = [x[1] for x in zip(page_list[:-1], page_list[1:]) if (x[1] - x[0] != 1)]
        for i in skip_pages:
            page_list.insert(page_list.index(i), False)

        return page_list
