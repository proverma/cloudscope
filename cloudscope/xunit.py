"""code that collects logs from jenkins."""

import requests
from requests.auth import HTTPBasicAuth
import xmltodict
from elasticsearch import Elasticsearch
import datetime
import json


class XUnitManager(object):

    """main class"""

    def __init__(self, project, user, password, jobUrl, lastBuildNumber=0):
        """defining constructor for getting the credentials."""
        self.project = project
        self.user = user
        self.password = password
        self.jobUrl = jobUrl
        self.lastBuildNumber = lastBuildNumber
        self.es = Elasticsearch()

        xunitMapping = {"mappings": {
            "testjob": {
                "properties": {
                    "duration": {
                        "type": "long"
                    },
                    "id": {
                        "type": "long"
                    },
                    "name": {
                        "type": "string"
                    },
                    "result": {
                        "type": "string"
                    },
                    "time": {
                        "type": "date"
                    }
                }
            },
            "testsuite": {
                "_parent": {
                    "type": "testjob"
                }
            },
            "testcase": {
                "_parent": {
                    "type": "testsuite"
                }
            }
        }
        }

        # connects to elasticsearch and stores  tesctsuit,
        # testjob and testcases information into data

        r = requests.put(
            "http://104.130.136.105:9200/" + self.project, data=json.dumps(xunitMapping))
        # TODO : make this api call work
        #self.es.indices.put_mapping
        print r.json()

    def postXunitReports(self):
        """
        building url, gettting reponse from jenkins
        and parsing from xml to python dictionary
        """
        buildUrls = self.getNewBuilds(self.jobUrl, self.lastBuildNumber)
        for k in buildUrls:
            response_json = self.callJenkins(k + '/api/json')
            self.indexTestJob(k, response_json["fullDisplayName"], response_json["id"],
                              response_json[
                                  "timestamp"], response_json["result"],
                              response_json["duration"])
            urls = self.getXunitReportUrls(k, response_json["artifacts"])
            for u in urls:
                self.testSuiteCounter = 0
                report = xmltodict.parse(
                    requests.get(u, auth=HTTPBasicAuth(self.user, self.password)).content)
                testSuite = report["testsuites"]["testsuite"]
                print u
                # TODO : fix duplicate code
                if isinstance(testSuite, list):
                    for t in testSuite:
                        id = self.indexTestSuite(t, k)
                        try:
                            self.indexTestcase(t["testcase"], id)
                        except KeyError:
                            print "no testcase found"
                else:
                    id = self.indexTestSuite(testSuite, k)
                    try:
                        self.indexTestcase(testSuite["testcase"], id)
                    except KeyError:
                        print "no testcase found"

    def indexTestcase(self, testcases, testSuiteId):
        """
        checking the number of test cases
        and displaying the testcases details
        """
        # if a suite has just one testcase, cml2dict returns an object instead
        # of dict, handling that scenario
        self.testCaseCounter = 0
        # TODO : fix duplicate code
        if isinstance(testcases, list):
            for t in testcases:
                self.testCaseCounter += 1
                testCaseId = testSuiteId + "/testcase/" + \
                    str(self.testCaseCounter)
                self.es.index(index=self.project, id=testCaseId,
                              doc_type="testcase", body=t, parent=testSuiteId)
        else:
            self.testCaseCounter += 1
            testCaseId = testSuiteId + "/testcase/" + str(self.testCaseCounter)
            self.es.index(index=self.project, id=testCaseId,
                          doc_type="testcase", body=testcases, parent=testSuiteId)

    def indexTestJob(self, url, name, id, time, result, duration):
        """defining testjob index"""
        testJob = {
            "name": name,
            "id": int(id),
            "time": datetime.datetime.fromtimestamp(int(time) / 1000).strftime('%Y-%m-%dT%H:%M:%S'),
            "result": result,
            "duration": duration
        }

        self.es.index(
            index=self.project, doc_type="testjob", id=url, body=testJob)

    def indexTestSuite(self, testSuite, buildUrl):
        """defining testsuit index"""
        try:
            # testSuite.pop("testcase")
            self.testSuiteCounter += 1
            testSuiteId = buildUrl + "testsuite/" + str(self.testSuiteCounter)

            self.es.index(index=self.project, id=testSuiteId,
                          doc_type="testsuite", body=testSuite, parent=buildUrl)
            return testSuiteId
        except KeyError:
            print "No Testcase found"

        # self.es.index()

    def callJenkins(self, url):
        """
        calling jenkins by passing credentials
        """
        r = requests.get(url, auth=HTTPBasicAuth(self.user, self.password))
        return r.json()

    def getNewBuilds(self, jobUrl, lastBuildNumber):
        """
        getting new bulds from jenkins
        """
        builds = []
        response_json = self.callJenkins(jobUrl + 'api/json')

        for b in response_json["builds"]:
            if b["number"] > lastBuildNumber:
                builds.append(b["url"])

        return builds

    def getXunitReportUrls(self, jobUrl, artifacts):
        """
        checking for the xml and appending url with artifacts
        and relativepath
        """
        urls = []

        for a in artifacts:
            if ".xml" in a["relativePath"]:
                urls.append(jobUrl + "artifact/" + a["relativePath"])

        return urls
