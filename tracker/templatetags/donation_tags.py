from django import template
from donations import settings
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
import datetime
import locale

register = template.Library()

@register.tag("sort")
def do_sort(parser, token):
	try:
		tag_name, sort_field = token.split_contents()
	except ValueError:
		raise template.TemplateSyntaxError('%r tag requires a single argument' % token.contents.split()[0])
	if not (sort_field[0] == sort_field[-1] and sort_field[0] in ('"', "'")):
		raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % token.contents.split()[0])
	return SortNode(sort_field[1:-1])

class SortNode(template.Node):
	def __init__(self, sort_field):
		self.sort_field = sort_field
	def render(self, context):
		return '<a href="?sort=' + self.sort_field + '&amp;order=1"><img src="' + settings.MEDIA_URL + 'up.png" alt="Asc"/></a><a href="?sort=' + self.sort_field + '&amp;order=-1"><img src="' + settings.MEDIA_URL + 'down.png" alt="Dsc"/></a>'
		
@register.tag("rendertime")
def do_rendertime(parser, token):
	try:
		tag_name, time = token.split_contents()
	except ValueError:
		raise template.TemplateSyntaxError('%r tag requires a single argument' % token.contents.split()[0])
	return RenderTimeNode(time)
	
class RenderTimeNode(template.Node):
	def __init__(self, time):
		self.time = template.Variable(time)
	def render(self, context):
		try:
			time = self.time.resolve(context)
			try:
				now = datetime.datetime.now() - time
			except TypeError:
				return ''
			return '%d.%d seconds' % (now.seconds,now.microseconds)
		except template.VariableDoesNotExist:
			return ''

@register.filter("forumfilter")
def forumfilter(value,autoescape=None):
	if autoescape:
		esc = conditional_escape
	else:
		esc = lambda x: x
	return mark_safe(esc(value).replace('\n', '<br />'))
forumfilter.is_safe = True
forumfilter.needs_autoescape = True

@register.filter("money")
def money(value):
	locale.setlocale( locale.LC_ALL, '')
	if not value:
		return locale.currency(0.0)
	return locale.currency(value, symbol=True, grouping=True)
money.is_safe = True