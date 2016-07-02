from markdown import markdown

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


#
# Filters
#

@register.filter()
def oneline(value):
    """
    Replace each line break with a single space
    """
    return value.replace('\n', ' ')


@register.filter()
def getlist(value, arg):
    """
    Return all values of a QueryDict key
    """
    return value.getlist(arg)


@register.filter(is_safe=True)
def gfm(value):
    """
    Render text as GitHub-Flavored Markdown
    """
    html = markdown(value, extensions=['mdx_gfm'])
    return mark_safe(html)


@register.filter()
def startswith(value, arg):
    """
    Test whether a string starts with the given argument
    """
    return str(value).startswith(arg)


@register.filter()
def user_can_add(model, user):
    perm_name = '{}:add_{}'.format(model._meta.app_label, model.__class__.__name__.lower())
    return user.has_perm(perm_name)


@register.filter()
def user_can_change(model, user):
    perm_name = '{}:change_{}'.format(model._meta.app_label, model.__class__.__name__.lower())
    return user.has_perm(perm_name)


@register.filter()
def user_can_delete(model, user):
    perm_name = '{}:delete_{}'.format(model._meta.app_label, model.__class__.__name__.lower())
    return user.has_perm(perm_name)


#
# Tags
#

@register.simple_tag()
def querystring_toggle(request, multi=True, page_key='page', **kwargs):
    """
    Add or remove a parameter in the HTTP GET query string
    """
    new_querydict = request.GET.copy()

    # Remove page number from querystring
    try:
        new_querydict.pop(page_key)
    except KeyError:
        pass

    # Add/toggle parameters
    for k, v in kwargs.items():
        values = new_querydict.getlist(k)
        if k in new_querydict and v in values:
            values.remove(v)
            new_querydict.setlist(k, values)
        elif not multi:
            new_querydict[k] = v
        else:
            new_querydict.update({k: v})

    querystring = new_querydict.urlencode()
    if querystring:
        return '?' + querystring
    else:
        return ''
