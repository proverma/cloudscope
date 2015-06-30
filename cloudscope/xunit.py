"""code that collects logs from jenkins."""

import requests
from requests.auth import HTTPBasicAuth
import xmltodict
from elasticsearch import Elasticsearch
import datetime
import json
from xunitMapping import xunitMapping
es = Elasticsearch()


class XUnitManager(object):

    """main class"""

    def __init__(self, project, user, password, job_url, last_build_number=0):
        """defining constructor for getting the credentials."""
        self.project = project
        self.user = user
        self.password = password
        self.job_url = job_url
        self.last_build_number = last_build_number
        self.es = Elasticsearch()

        self.es.indices.clear_cache(index=self.project)
        r = requests.put(
            "http://localhost:9200/" + self.project,
            data=json.dumps(xunitMapping))

        self.es.indices.put_mapping(index=self.project,
                                    doc_type=json,
                                    body=xunitMapping,
                                    ignore=400)
        print r.json()

    def post_xunit_reports(self):
        """
        building url, gettting reponse from jenkins
        and parsing from xml to python dictionary
        """
        build_urls = self.get_new_builds(self.job_url, self.last_build_number)
        print build_urls
        for k in build_urls:
            response_json = self.call_jenkins(k + '/api/json')
            self.index_test_job(k, response_json["fullDisplayName"],
                                response_json["id"], response_json["timestamp"],
                                response_json["result"], response_json["duration"],
                                response_json["estimatedDuration"], response_json["changeSet"],
                                response_json["culprits"])
            urls = self.get_xunit_report_urls(k, response_json["artifacts"])
            for u in urls:
                self.testsuite_counter = 0
                report = xmltodict.parse(
                    requests.get(u, auth=HTTPBasicAuth(self.user, self.password)).content)
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
        checking the number of test cases
        and displaying the testcases details
        """
        # if a suite has just one testcase, cml2dict returns an object instead
        # of dict, handling that scenario
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
                          doc_type="testcase", body=testcases, parent=testsuite_id)

    def index_test_job(self, url, name, id, time, result, duration, estimated_duration,
                       changeSet, culprits):
        """defining testjob index"""
        author_list = [item['author']['fullName'] for item in changeSet['items']]
        culprit_list = [each['fullName'] for each in culprits]
        testJob = {
            "name": name,
            "id": int(id),
            "time": datetime.datetime.fromtimestamp(int(time) / 1000).
            strftime('%Y-%m-%dT%H:%M:%S'), "result": result,
            "duration": duration,
            "estimatedDuration": estimated_duration,
            "changeSet": author_list,
            "culprits": culprit_list
        }

        self.es.index(
            index=self.project, doc_type="testjob", id=url, body=testJob)

    def index_test_suite(self, testsuite, build_url):
        """defining testsuit index"""
        try:
            # testSuite.pop("testcase")
            self.testsuite_counter += 1
            testsuite_id = build_url + "testsuite/" + \
                str(self.testsuite_counter)

            self.es.index(index=self.project, id=testsuite_id,
                          doc_type="testsuite", body=testsuite, parent=build_url)
            return testsuite_id
        except KeyError:
            print "No Testcase found"

        # self.es.index()

    def call_jenkins(self, url):
        """
        calling jenkins by passing credentials
        """
        r = requests.get(url, auth=HTTPBasicAuth(self.user, self.password))
        return r.json()

    def get_new_builds(self, job_url, last_build_number):
        """
        getting new bulds from jenkins
        """
        builds = []
        response_json = self.call_jenkins(job_url + 'api/json')
        for b in response_json["builds"]:
            if int(b["number"]) > int(last_build_number):
                builds.append(b["url"])

        return builds

    def get_xunit_report_urls(self, job_url, artifacts):
        """
        checking for the xml and appending url with artifacts
        and relativepath
        """
        urls = []

        for a in artifacts:
            if ".xml" in a["relativePath"]:
                urls.append(job_url + "artifact/" + a["relativePath"])

        return urls
