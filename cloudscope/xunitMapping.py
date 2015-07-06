xunitMapping = { "mappings": {
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
                                "items": {
                                    "type": "list",
                                    "author": {
                                        "type": "object",
                                        "fullName": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "culprits": {
                                "type": "list",
                                "fullName": {
                                    "type": "string"
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
