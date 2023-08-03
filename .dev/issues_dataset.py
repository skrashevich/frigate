#!/usr/bin/env python3

from github import Github
import json
import requests
from typing import List


def get_issues(token, user, repo, state):
    g = Github(token)

    labels = ["question", "support", "help wanted", "triage"]
    label_query = "label:" + ",".join(f"{label}" for label in labels)

    query = f"repo:{user}/{repo} is:issue state:{state} {label_query}"
    issues: List[Github.Issue.Issue] = []
    for issue in g.search_issues(query):
        print(issue.title)
        issues.append(issue)

    return issues


def preprocess_data(initial_question, comments, resulting_answer):
    data = {
        "initial_question": initial_question,
        "comments": comments,
        "resulting_answer": resulting_answer,
    }
    return data


def extract_data(issue):
    initial_question = issue.body
    comments_url = issue.comments_url

    comments_response = requests.get(comments_url)
    comments_data = json.loads(comments_response.text)
    comments = [
        comment["body"]
        for comment in comments_data
        if comment.get("user").get("type") != "Bot"
    ]

    # Delete from comments all strings, beginning from character ">"
    comments = [comment.split(">")[0] for comment in comments]

    if comments:
        resulting_answer = comments.pop()
    else:
        resulting_answer = None

    # TODO: delete last value from comments list
    return initial_question, comments, resulting_answer


def save_data(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f)


def print_data(data):
    print(json.dumps(data, indent=2))


def download(token, user, repo, filename, num_issues):
    issues = get_issues(token, user, repo, "closed")

    dataset = []
    count = 0
    for issue in issues:
        if count >= num_issues:
            break
        initial_question, comments, resulting_answer = extract_data(issue)
        preprocessed_data = preprocess_data(
            initial_question, comments, resulting_answer
        )
        dataset.append(preprocessed_data)
        count += 1

        # print_data(dataset)

    save_data(dataset, filename)


# Add your personal access token, the username, repo name, and filename here
download(
    "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",
    "blakeblackshear",
    "frigate",
    "issues.json",
    5000,
)
