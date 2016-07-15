class NoDefaultProvided(object):
    pass

def get_dotted_attr(obj, name, default=NoDefaultProvided):
    """
    Same as getattr(), but allows dot notation lookup
    http://stackoverflow.com/a/14324459/710394
    """
    try:
        return reduce(getattr, name.split("."), obj)
    except AttributeError, e:
        if default != NoDefaultProvided:
            return default
        raise


class CSVColumn(object):
    empty_value = ''

    def __init__(self, header=None, source=None, empty_value=None):
        assert all([header, source])
        self.header = header
        self.source = source
        self.empty_value = empty_value or self.empty_value

    def get_data(self, obj):
        return get_dotted_attr(obj, self.source, self.empty_value)


class CSVFormatter(object):
    headers = []
    fields = []
    empty_cell_value = ''

    def get_header_row(self):
        return self.headers

    def get_row(self, obj):
        """
        Return an iterable to be fed to csv.writerow()
        """
        return [getattr(obj, field, self.empty_cell_value) for field in self.fields]
