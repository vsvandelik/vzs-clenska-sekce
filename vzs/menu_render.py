from django.urls import resolve, reverse
from django.utils.encoding import escape_uri_path


class MenuItem:
    ITEM_WITHOUT_CHILDREN_HTML = """
<li class="nav-item">
    <a class="nav-link {active_class}" href="{url}">
        <i class="nav-icon {icon}"></i>
        <p>{title}</p>
    </a>
</li>
"""

    ITEM_WITH_CHILDREN_HTML = """
<li class="nav-item {menu_open_class}">
    <a href="#" class="nav-link {active_class}">
        <i class="nav-icon {icon}"></i>
        <p>{title}<i class="right fas fa-angle-left"></i></p>
    </a>
    <ul class="nav nav-treeview">
        {sub_items}
    </ul>
</li>
    """

    SUBITEM_HTML = """
<li class="nav-item">
    <a href="{url}" class="nav-link {active_class}">
        <i class="far fa-circle nav-icon"></i>
        <p>{title}</p>
    </a>
</li>
"""

    def __init__(
        self, title: str, link: str = None, *, icon: str = None, children: list = None
    ):
        self.icon = icon
        self.title = title

        if link is None and children is None:
            raise ValueError("Either item or children must be specified.")
        elif link is not None and children is not None:
            raise ValueError("Only one of item or children must be specified.")

        self.link = link
        self.reverse_link = self._get_reversed_link(link)
        self.children = children

    def render(self, context):
        if self.link is not None:
            return self._render_item(context)
        else:
            return self._render_item_with_children(context)

    def render_as_subitem(self, context):
        is_active = self._is_active(context, self.reverse_link, strict=True)

        data = {
            "url": self.reverse_link,
            "title": self.title,
            "active_class": "active" if is_active else "",
        }

        return self.SUBITEM_HTML.format(**data)

    def _render_item(self, context):
        if not self._has_permission(context, self.reverse_link):
            return ""

        is_active = self._is_active(context, self.reverse_link, strict=True)

        date = {
            "url": self.reverse_link,
            "icon": self.icon,
            "title": self.title,
            "active_class": "active" if is_active else "",
        }

        return self.ITEM_WITHOUT_CHILDREN_HTML.format(**date)

    def _render_item_with_children(self, context):
        permissions = {
            child: self._has_permission(context, child.reverse_link)
            for child in self.children
        }
        if not any(permissions.values()):
            return ""

        children_reverse_links = [child.reverse_link for child in self.children]

        is_active_non_strict = self._is_active(
            context, children_reverse_links, strict=False
        )
        is_active_strict = self._is_active(context, children_reverse_links, strict=True)

        sub_items = [
            child.render_as_subitem(context)
            for child in self.children
            if permissions[child]
        ]

        data = {
            "menu_open_class": "menu-open" if is_active_non_strict else "",
            "active_class": "active" if is_active_strict else "",
            "icon": self.icon,
            "title": self.title,
            "sub_items": "".join(sub_items),
        }

        return self.ITEM_WITH_CHILDREN_HTML.format(**data)

    @staticmethod
    def _get_reversed_link(link):
        if not link:
            return None

        parts = link.split(" ", 1)
        if len(parts) == 1:
            return reverse(parts[0])
        else:
            return reverse(parts[0], args=[parts[1]])

    @staticmethod
    def _has_permission(context, reverse_link: str):
        match = resolve(reverse_link)

        return match.func.view_class.view_has_permission_person(
            "GET", context["active_person"], GET={}, POST={}, **match.kwargs
        )

    @staticmethod
    def _is_active(context, reverse_links: str | list, strict=False):
        request = context.get("request")

        if isinstance(reverse_links, str):
            reverse_links = [reverse_links]

        active = False
        for path in reverse_links:
            request_path = escape_uri_path(request.path)
            if strict:
                active = request_path == path
            else:
                active = request_path.find(path) == 0
            if active:
                break

        return active
