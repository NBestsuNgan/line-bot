# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class SessionState:
    def __init__(self, did_welcome: bool = False):
        self.did_welcome_user = did_welcome
        self.count_messages = 0
        self.cache_question_response = {} # {reply_to_id: {question: str, response: str}}
