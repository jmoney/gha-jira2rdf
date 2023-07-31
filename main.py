import argparse
import datetime
import jira
import os
import rdflib
import sys

from jira import JIRA

API_TOKEN=os.environ.get("JIRA_API_TOKEN")
JIRA_NS = rdflib.Namespace("https://jira.atlassian.net/")
DEFAULT = rdflib.Namespace("https://dataworld.atlassian.net/browse/")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="JIRA to RDF")
    parser.add_argument("--jira-server", type=str, required=True, help="JIRA server URL", dest="jira_server")
    parser.add_argument("--username", type=str, required=True, help="JIRA username", dest="username")
    parser.add_argument("--max-results", type=int, default=10, help="Max results to return")
    parser.add_argument("--jql", type=str, required=True, help="JQL query to run", dest="jql")
    parser.add_argument("--format", type=str, default="turtle", help="RDF format to output", dest="format")
    args = parser.parse_args()

    jira = JIRA(
        server=args.jira_server,
        basic_auth=(args.username, API_TOKEN), 
    )

    g = rdflib.Graph()
    g.bind("jira", JIRA_NS)
    g.bind("", DEFAULT)
    sprint_field = ""
    for field in jira.fields():
        if "Sprint" in field["clauseNames"]:
            sprint_field = field["key"]
    issues = jira.search_issues(jql_str=args.jql, fields="*all", startAt=0, maxResults=args.max_results)
    page = 1
    while len(issues) > 0:
        # print(len(issues))
        for issue in issues:
            g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), rdflib.RDF.type, JIRA_NS.Issue))
            g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.key, rdflib.Literal(issue.key)))
            g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.issuetype, rdflib.Literal(issue.get_field("issuetype"))))
            g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.project, rdflib.Literal(issue.get_field("project"))))
            g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.summary, rdflib.Literal(issue.get_field("summary"))))
            g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.status, rdflib.Literal(issue.get_field("status"))))
            g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.created, rdflib.Literal(issue.get_field("created"))))
            g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.updated, rdflib.Literal(issue.get_field("updated"))))
            g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.priority, rdflib.Literal(issue.get_field("priority"))))

            if issue.get_field("priority").name == "Not prioritized":
                g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.rank, rdflib.Literal(999, datatype=rdflib.XSD.integer)))
            elif issue.get_field("priority").name == "Highest":
                g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.rank, rdflib.Literal(1, datatype=rdflib.XSD.integer)))
            elif issue.get_field("priority").name == "High":
                g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.rank, rdflib.Literal(2, datatype=rdflib.XSD.integer)))
            elif issue.get_field("priority").name == "Medium":
                g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.rank, rdflib.Literal(3, datatype=rdflib.XSD.integer)))
            elif issue.get_field("priority").name == "Low":
                g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.rank, rdflib.Literal(4, datatype=rdflib.XSD.integer)))
            elif issue.get_field("priority").name == "Lowest":
                g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.rank, rdflib.Literal(5, datatype=rdflib.XSD.integer)))
            else:
                print("I don't know how to handle this priority", issue.get_field("priority"), file=sys.stderr)

            if issue.get_field("resolution") is not None:
                g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.resolution, rdflib.Literal(issue.get_field("resolution"))))

            if issue.get_field("resolutiondate") is not None:
                g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.resolved, rdflib.Literal(issue.get_field("resolutiondate"))))
                iso_datetime = datetime.datetime.strptime(issue.get_field("resolutiondate"), "%Y-%m-%dT%H:%M:%S.%f%z")
                g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.day_of_resolution, rdflib.Literal(iso_datetime.date(), datatype=rdflib.XSD.date)))
            if issue.get_field(sprint_field) is not None:
                for sprint in issue.get_field(sprint_field):
                    g.add((rdflib.URIRef(f'{jira.server_url}/browse/{issue.key}'), JIRA_NS.sprint, rdflib.Literal(sprint.name)))
            
        page += 1
        issues = jira.search_issues(jql_str=args.jql, fields="*all", startAt=page*args.max_results, maxResults=args.max_results)

    print(g.serialize(format=args.format))
        
        