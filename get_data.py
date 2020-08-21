#!/usr/bin/env python3
# vim: set ts=4 sw=4 ts=4 et :

import argparse
import logging
import time

import csv
from datetime import datetime, timedelta
import json
import requests
import os

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()
logging.getLogger("urllib3").setLevel(logging.INFO)


def parse_args():
    parser = argparse.ArgumentParser(description="Default")
    parser.add_argument("--debug", help="debug", action="store_true")
    return parser.parse_args()

class RegulationsAPI:
    __base_url = "https://beta.regulations.gov/api"

    def __init__(self):
        self.s = None

    def init(self):
        self.s = requests.Session()

    def fini(self):
        self.s.close()

    def document(self, document_id):
        document = None
        endpoint = "documentdetails"
        url = f"{self.__base_url}/{endpoint}/{document_id}"
        resp = self.s.get(url)
        if resp.status_code == 200:
           data = resp.json()
           document = data["data"]
        return document

    def parse_date(self, date):
        return datetime.fromisoformat(date.replace("Z", "+00:00"))

    def fmt_date(self, date):
        return date.strftime("%m-%d-%Y")

    def comments(self, document_id):
        document = self.document(document_id)
        if document is None:
            log.info(f"No data found for {document_id}")
            return None

        endpoint = "comments"
        url = f"{self.__base_url}/{endpoint}"

        object_id = document["attributes"]["objectId"]
        oldest = self.parse_date(document["attributes"]["commentStartDate"])
        params = {
            "filter[commentOnId]": object_id,
            "page[number]": 1,
            "sort": "-postedDate",  # newest first
            "filter[postedDate]": self.fmt_date(oldest)
        }

        comments = dict()
        curr_date = oldest
        while self.fmt_date(curr_date) != self.fmt_date(datetime.now()):
            resp = self.s.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()

                comments.update({c["id"]: c for c in data["data"]})
                params["page[number]"] += 1

                if data["meta"]["lastPage"]:
                    curr_date += timedelta(days=1)
                    params["filter[postedDate]"] = self.fmt_date(curr_date)
                    params["page[number]"] = 1
            else:
                log.error(f"Failed to fetch comments for {document_id}")
                comments = None
                break

        return list(comments.values()) if comments else None

    def comment(self, comment_id):
        return self.document(comment_id)


def main():
    args = parse_args()

    log.info("Running {}".format(__file__))
    if args.debug:
        log.setLevel(logging.DEBUG)
        log.debug("Debug mode enabled")

    # profiling
    s = time.perf_counter()

    api = RegulationsAPI()
    api.init()

    doc_id = "FSA-2020-0004-0003"
    fname = f"{doc_id}.json"
    comments = None
    if not os.path.isfile(fname):
        comments = api.comments(doc_id)
        with open(fname, "w") as fd:
            json.dump(comments, fd, indent=2)
    else:
        with open(fname, "r") as fd:
            comments = json.load(fd)

    enriched_fname = f"enriched_{fname}"
    if not os.path.isfile(enriched_fname):
        for i, comment in enumerate(comments):
            log.debug(f"{i} of {len(comments)}")
            c = api.comment(comment["id"])
            if c:
                comment.update(c)

        with open(enriched_fname, "w") as fd:
            json.dump(comments, fd, indent=2)
    else:
        with open(enriched_fname, "r") as fd:
            comments = json.load(fd)

    cotton = list()
    for comment in comments:
        c_id = comment["id"]
        attributes = comment["attributes"]
        content = attributes["content"]
        a_url = list()
        attachments = attributes["attachments"]
        if attachments:
            for a in attachments:
                for f in a["fileFormats"]:
                    a_url.append(f["fileUrl"])
        if (content is not None) and ("cotton" in content or "Cotton" in
                content or "pima" in content or "Pima" in content):
            cotton.append({
                "id": c_id,
                "comment": content,
                "attachments": a_url
            })

    with open("cotton.json", "w") as fd:
        json.dump(cotton, fd, indent=2)

    with open("cotton.csv", "w") as fd:
        dw = csv.DictWriter(fd, fieldnames=["id", "comment", "attachments"])
        dw.writeheader()
        dw.writerows(cotton)

    api.fini()

    elapsed = time.perf_counter() - s
    log.info(f"{__file__} executed in {elapsed:0.5f} seconds.")


if __name__ == "__main__":
    main()

