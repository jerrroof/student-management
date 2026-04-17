"""
自定义模板过滤器
"""
from django import template

register = template.Library()


@register.filter
def div(value, arg):
    """除法过滤器"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def mul(value, arg):
    """乘法过滤器"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def sub(value, arg):
    """减法过滤器"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """计算百分比"""
    try:
        if float(total) == 0:
            return 0
        return round(float(value) / float(total) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
