import django_tables2 as tables

from django.utils.safestring import mark_safe


class BaseTable(tables.Table):

    def __init__(self, *args, **kwargs):
        super(BaseTable, self).__init__(*args, **kwargs)

        # Set default empty_text if none was provided
        if self.empty_text is None:
            self.empty_text = 'No {} found.'.format(self._meta.model._meta.verbose_name_plural)

    class Meta:
        attrs = {
            'class': 'table table-hover',
        }


class ToggleColumn(tables.CheckBoxColumn):

    def __init__(self, *args, **kwargs):
        default = kwargs.pop('default', '')
        visible = kwargs.pop('visible', False)
        super(ToggleColumn, self).__init__(*args, default=default, visible=visible, **kwargs)

    @property
    def header(self):
        return mark_safe('<input type="checkbox" name="_all" title="Select all" />')
