 
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