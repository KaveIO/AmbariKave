##############################################################################
#
# Copyright 2016 KPMG Advisory N.V. (unless otherwise stated)
#
# Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
##############################################################################


class InlineTemplate(object):

    def __init__(self, *args, **kwargs):
        self.text = args[0]
        self.replaces = kwargs
        print self.replaces
        pass

    def get_content(self):
        replace_forformat = {'{{': '%%LFLAG%%', '{': '%%LB%%',
                             '}}': '%%RFLAG%%', '}': '%%RB%%'}
        replace_format = {'%%LFLAG%%': '{', '%%RFLAG%%': '}'}
        todo = self.text
        for k, v in replace_forformat.iteritems():
            todo = todo.replace(k, v)
        for k, v in replace_format.iteritems():
            todo = todo.replace(k, v)
        # then replace stuff
        for k, v in self.replaces.iteritems():
            if type(v) is not str:
                raise TypeError("Mock InlineTeplate class does not know what to do if you're not using a string"
                                "you sent " + k + " " + str(type(v)))
        todo = todo.format(**self.replaces)
        for k, v in replace_format.iteritems():
            todo = todo.replace(v, k)
        for k, v in replace_forformat.iteritems():
            todo = todo.replace(v, k)
        return todo
