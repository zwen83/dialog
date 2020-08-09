#DIALOG VERSION: 2.2.1
class Metric:
    def __init__(self, key, value, meta_data = '', full_metric = '', parts = []):
        self.key = key
        self.value = value
        self.meta_data = meta_data
        self.full_metric = full_metric
        self.parts = parts

    def format(self):
        output = '%s,%s value=' % (self.key, ','.join(['%s=%s' % (key, value) for (key, value) in self.tags.items()]))

        if 'str' in str(type(self.value)) or 'unicode' in str(type(self.value)):
            output = '%s%s\n' % (output, str(self.value))
        else:
            output = '%s"%f"\n' % (output, self.value)

        return output