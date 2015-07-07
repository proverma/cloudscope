xunitMapping = {"mappings": {
    "testjob": {
        "properties": {
            "duration": {
                "type": "long"
            },
            "id": {
                "type": "long"
            },
            "estimatedDuration": {
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
            },
            "changeSet": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "list",
                        "properties": {
                            "author": {
                                "type": "object",
                                "properties": {
                                    "fullName": {
                                        "type": "string"
                                    }
                                }
                            }
                        }

                    }
                }

            },
            "culprits": {
                "type": "list",
                "properties": {
                    "fullName": {
                        "type": "string"
                    }
                }
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
