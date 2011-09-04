from django import template
from donations import settings

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
		return '<a href="?sort=' + self.sort_field + '&amp;order=1"><img src="' + settings.MEDIA_URL + 'up.png" /></a><a href="?sort=' + self.sort_field + '&amp;order=-1"><img src="' + settings.MEDIA_URL + 'down.png" /></a>'
