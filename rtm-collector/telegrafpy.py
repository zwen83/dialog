#DIALOG VERSION: 2.2.1
# Helper functions and classes for PyGraf.
import time
import ntc_tools

class TMetric:
    def __init__(self, name, gtime = 0, tags = {}, fields = {}):
        self.name = name
        tmptime = gtime
        if gtime == 0:
            tmptime = time.time()            
        self.time = int(tmptime) * 1000000000
        self.tags = tags

        #add the hostname tag if not present
        if 'host' not in self.tags:
            self.tags['host'] = ntc_tools.get_host_name()
        self.fields = fields
    def __repr__(self):
        return "{0} {1} {2} {3}".format(self.time, self.name, self.tags, self.fields)

    def format(self):
        return '%s,%s %s %d' % (self.name,
                                ",".join(['%s=%s' % (key,value) for (key,value) in self.tags.iteritems()]),
                                ",".join(['%s=%s' % (key,value) for (key,value) in self.fields.iteritems()]),
                                self.time)
