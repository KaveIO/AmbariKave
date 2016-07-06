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
import os

from resource_management import *
from kavecommon import ApacheScript
from resource_management.core.exceptions import ComponentIsNotRunning


class KaveLanding(ApacheScript):
    # status file is needed to know if this service was started, stores the name of the index file
    status_file = '/etc/kave/kavelanding_started'

    def install(self, env):
        print "installing KaveLanding"
        import params
        import kavecommon as kc
        super(KaveLanding, self).install(env)
        Execute('yum clean all')
        Package('python-devel')
        Package('python-pip')
        import os
        Execute('pip install requests')
        Execute('cp ' + os.path.dirname(__file__) + '/KAVE-logo-thin.png ' + params.www_folder + '/')
        Execute('chmod 0644 ' + params.www_folder + '/KAVE-logo-thin.png')
        self.configure(env)

    def configure(self, env):
        import params
        import os
        import kavecommon as kc
        env.set_params(params)
        self.write_html(env)
        super(KaveLanding, self).configure(env)

    def write_html(self, env):
        import params
        import kavecommon as kc
        env.set_params(params)
        if os.path.exists(params.www_folder + '/index.html'):
            os.remove(params.www_folder + '/index.html')
        File(params.www_folder + '/index.html',
             content=Template("kavelanding.html.j2"),
             mode=0644
             )
        File(params.www_folder + '/bootstrap.min.css',
             content=Template("bootstrap.min.css"),
             mode=0644
             )
        File(params.www_folder + '/LICENSE',
             content=Template("LICENSE"),
             mode=0644
             )
        File(params.www_folder + '/LICENSE-DOCUMENTATION-IMAGE-SUBCLAUSE',
             content=Template("LICENSE-DOCUMENTATION-IMAGE-SUBCLAUSE"),
             mode=0644
             )
        File(params.www_folder + '/NOTICE',
             content=Template("NOTICE"),
             mode=0644
             )
        # HINT: Use this in future: http://jinja.pocoo.org/docs/dev/templates/
        import kavescan as ls
        ls.ambari_user = params.AMBARI_ADMIN
        ls.ambari_password = params.AMBARI_ADMIN_PASS
        cluster_service_host, cluster_host_service, cluster_service_link = ls.collect_config_data(
            params.AMBARI_SHORT_HOST, user=params.AMBARI_ADMIN, passwd=params.AMBARI_ADMIN_PASS)
        bodyhtml = ls.pretty_print(cluster_service_host, cluster_host_service, cluster_service_link, format="html")
        import json
        clinks = json.loads(params.customlinks)
        if len(clinks.keys()):
            custom_html = "<b>Custom Links</b><p><ul>"
            klist = clinks.keys()
            klist.sort()
            for lname in klist:
                custom_html = custom_html + '\n    <li><a href="' + clinks[lname] + '">' + lname + '</a></li>'
            custom_html = custom_html + "</ul><p>\n"
            bodyhtml.replace('<b>Servers</b>', custom_html + '<b>Servers</b>')
        # HINT: this can be replaced by the correct template language in future
        HUE_LINK_IF_KNOWN = ""
        all_links = []
        for cluster in cluster_service_link:
            if "HUE_SERVER" in cluster_service_link[cluster]:
                HUE_LINK_IF_KNOWN = "<li>" + cluster_service_link[cluster]["HUE_SERVER"][0] + "</li>"
        for cluster in cluster_service_link:
            for service in cluster_service_link[cluster]:
                if len(cluster_service_link[cluster][service]) > 2:
                    continue
                all_links = all_links + ["<li>" + l + "</li>" for l in cluster_service_link[cluster][service]]
        f = open(params.www_folder + '/index.html')
        content = f.read()
        f.close()
        f = open(params.www_folder + '/index.html', 'w')
        if len(cluster_service_link.keys()) == 1:
            content = content.replace("<title>KAVE:", "<title>" + cluster_service_link.keys()[0] + "-KAVE:")
        f.write(content.replace("THEPAGE!!",
                                bodyhtml).replace("HUE_LINK_IF_KNOWN",
                                                  HUE_LINK_IF_KNOWN).replace("ALL_OTHER_LINKS", "\n".join(all_links)))
        f.close()
        kc.chown_r(params.www_folder, "apache")

    def start(self, env):
        if not os.path.exists(os.path.dirname(self.status_file)):
            os.makedirs(os.path.dirname(self.status_file))
        import params
        self.configure(env)
        super(KaveLanding, self).start(env)
        # Write the location of the index file into the status file
        if os.path.exists(params.www_folder + '/index.html'):
            with open(self.status_file, 'w') as fp:
                fp.write(params.www_folder + '/index.html')

    def stop(self, env):
        import params

        super(KaveLanding, self).stop(env)
        if os.path.exists(params.www_folder + '/index.html'):
            os.remove(params.www_folder + '/index.html')
        if os.path.exists(self.status_file):
            os.remove(self.status_file)

    def status(self, env):
        # Read from the status file, and check the index exists
        if not os.path.exists(self.status_file):
            raise ComponentIsNotRunning()
        klfile = None
        with open(self.status_file) as fp:
            klfile = fp.read().split()[0].strip()
        if len(klfile) < 5 or (not os.path.exists(klfile)):
            raise ComponentIsNotRunning()
        super(KaveLanding, self).status(env)


if __name__ == "__main__":
    KaveLanding().execute()
