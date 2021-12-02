from django import template


register = template.Library()


@register.simple_tag
def use_space(use):
    if use == 0:
        return use
    if use >= 1024 * 1024 * 1024:
        return '%.2f G' % (use / 1024 / 1024 / 1024, )
    return '%.2f M' % (use / 1024 / 1024, )
