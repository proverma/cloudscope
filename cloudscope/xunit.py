"""This code collects lthe test logs from jenkins and
   stroes those test logs into elasticsearch"""

import requests
from requests.auth import HTTPBasicAuth
import xmltodict
from elasticsearch import Elasticsearch
import datetime
import json
from xunitMapping import xunitMapping
es = Elasticsearch()


class XUnitManager(object):

    """This is the main class."""

    def __init__(self, project, user, password, job_url, last_build_number=0):
        """constructor, for collecting project credentials.
           Project: project name, user: your user_name for jenkins
           password: you password for jenkins, job_url: jenkins job url,
           last_build_number: testlogs will be collected from the provided
           build_number"""
        self.project = project
        self.user = user
        self.password = password
        self.job_url = job_url
        self.last_build_number = last_build_number
        self.es = Elasticsearch()

        # clears cache
        self.es.indices.clear_cache(index=self.project, ignore=400)
        # puts data into elasticsearch
        requests.put(
            "http://localhost:9200/" + self.project,
            data=json.dumps(xunitMapping))

    def post_xunit_reports(self):
        """
        builds url, collects reponses from the jenkins for the testjob.
        Parses xml file to dictionary, checks for testcases under testsuites"""
        build_urls = self.get_new_builds(self.job_url, self.last_build_number)

        for k in build_urls:
            response_json = self.call_jenkins(k + '/api/json')
            self.index_test_job(k, response_json["fullDisplayName"],
                                response_json["id"],
                                response_json["timestamp"],
                                response_json["result"],
                                response_json["duration"],
                                response_json["estimatedDuration"],
                                response_json["changeSet"],
                                response_json["culprits"])
            urls = self.get_xunit_report_urls(k, response_json["artifacts"])
            for u in urls:
                self.testsuite_counter = 0
                report = xmltodict.parse(
                    requests.get(u, auth=HTTPBasicAuth(self.user,
                                                       self.password)).content)
                testSuite = report["testsuites"]["testsuite"]
                print u
                # TODO : fix duplicate code
                if isinstance(testSuite, list):
                    for t in testSuite:
                        id = self.index_test_suite(t, k)
                        try:
                            self.index_testcase(t["testcase"], id)
                        except KeyError:
                            print "no testcase found"
                else:
                    id = self.index_test_suite(testSuite, k)
                    try:
                        self.index_testcase(testSuite["testcase"], id)
                    except KeyError:
                        print "no testcase found"

    def index_testcase(self, testcases, testsuite_id):
        """
        checks for the testcases, if a suite has only when testcase
        then returns an object instead of dictionary.
        """
        self.testcase_counter = 0
        # TODO : fix duplicate code
        if isinstance(testcases, list):
            for t in testcases:
                self.testcase_counter += 1
                testcase_id = testsuite_id + "/testcase/" + \
                    str(self.testcase_counter)
                self.es.index(index=self.project, id=testcase_id,
                              doc_type="testcase", body=t, parent=testsuite_id)
        else:
            self.testcase_counter += 1
            testcase_id = testsuite_id + "/testcase/" + \
                str(self.testcase_counter)
            self.es.index(index=self.project, id=testcase_id,
                          doc_type="testcase", body=testcases,
                          parent=testsuite_id)

    def index_test_job(self, url, name, id, time, result, duration,
                       estimatedDuration, changeSet, culprits):
        """defines testjob index which includes: testjob name, id,
           timestamp: when the test was run, test execution duration,
           estimatedDuration, changeSet: person who created the build,
           culprits: person who contributed in the build."""

        author_list = [item['author']['fullName']
                       for item in changeSet['items']]
        culprit_list = [each['fullName'] for each in culprits]
        testJob = {
            "name": name,
            "id": int(id),
            "time": datetime.datetime.fromtimestamp(int(time) / 1000).
            strftime('%Y-%m-%dT%H:%M:%S'), "result": result,
            "duration": duration,
            "estimatedDuration": estimatedDuration,
            "changeSet": author_list,
            "culprits": culprit_list
        }

        self.es.index(
            index=self.project, doc_type="testjob", id=url, body=testJob)

    def index_test_suite(self, testsuite, build_url):
        """creates the index for testsuites and checks
           for the testcase in testsuites."""
        try:
            # testSuite.pop("testcase")
            self.testsuite_counter += 1
            testsuite_id = build_url + "testsuite/" + \
                str(self.testsuite_counter)

            self.es.index(index=self.project, id=testsuite_id,
                          doc_type="testsuite", body=testsuite,
                          parent=build_url)
            return testsuite_id
        except KeyError:
            print "No Testcase found"

        # self.es.index()

    def call_jenkins(self, url):
        """
        connects to jenkins by passing jenkin job url, username and password
        """
        r = requests.get(url, auth=HTTPBasicAuth(self.user, self.password))
        return r.json()

    def get_new_builds(self, job_url, last_build_number):
        """
        checks for the new builds in jenkins and append
        the url whenever there is new build.
        """
        builds = []
        response_json = self.call_jenkins(job_url + 'api/json')
        for b in response_json["builds"]:
            if int(b["number"]) > int(last_build_number):
                builds.append(b["url"])

        return builds

    def get_xunit_report_urls(self, job_url, artifacts):
        """
        checks for the artifacts and append url with the
        artifacts and xml files.
        """
        urls = []

        for a in artifacts:
            if ".xml" in a["relativePath"]:
                urls.append(job_url + "artifact/" + a["relativePath"])

        return urls
