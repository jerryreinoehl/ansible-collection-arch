#!/usr/bin/env python


class FilterModule():
    def filters(self):
        return {
            "quote": self.quote,
        }

    def quote(self, items):
        return [f'"{item}"' for item in items]
