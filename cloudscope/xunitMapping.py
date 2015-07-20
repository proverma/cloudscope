xunitMapping = {"mappings": {
    "testjob": {
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
