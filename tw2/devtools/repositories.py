""" Helper functions for scraping repos (github and someday bitbucket) """

import github2.client
import urllib2
import simplejson
import multiprocessing
import datetime

## Some constants ##
# The number of results github returns 'per-page'
github_rate = 35
# How many pages we're going to try to get at once.
tries = 20
# A 'theoretical max' of the number of commits we can handle.
theoretical_max = github_rate * tries

api_url = "http://github.com/api/v2/json"
base_url = api_url + "/commits/list/{user}/{project}/{branch}"

def _get_commits(args):
    """ This gets called in parallel so we spam the hell out of github. """
    url, page = args
    commits = []
    try:
        p = urllib2.urlopen(url.format(page=page))
        commits = simplejson.loads(p.read())['commits']
        p.close()
    except urllib2.HTTPError as e:
        pass
    return commits

pool = multiprocessing.Pool(processes=tries)

def get_all_commits(user, project, branch):
    """ Get all commits for a github project.

    Github's api paginates the results at 35 commits per page.  That makes
    things very slow.  Here we do all the requests for all the pages in
    parallel which should drastically speed things up.

    Github also doesn't tell us how many commits there are, so we can't
    plan accordingly.  Right now, we just 'guess' there are no more than
    20 pages of commits.  If there are, we're screwed and we raise a
    ValueError.
    """
    url = base_url.format(**locals()) + "?page={page}"
    arg_pairs = zip([url] * tries, range(1, tries+1))
    commits = sum(pool.map(_get_commits, arg_pairs), [])

    if len(commits) >= theoretical_max:
        raise ValueError, "%s %s exceeded max commits.  Increase 'tries'" % (
            user, project)

    return commits

def commits_per_month(module):
    users = ['ralphbean']
    branch = 'master'
    date_format = '%Y-%m-%dT%H:%M:%S'
    # TODO -- guess the service and user here from some list.

    # Go talk to github
    commits = get_all_commits(users[0], module, branch)

    # Convert authored_date to a python datetime
    timestamps = [
        datetime.datetime.strptime(commit['authored_date'][:-6], date_format)
        for commit in commits
    ]

    # Do two things.
    # 1) Only keep commits from within the last year
    # 2) Mangle the month to be from 0-11, starting with this month.
    one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
    months = [(t.month + 12 - datetime.datetime.now().month)%12
              for t in timestamps if t > one_year_ago]

    # Count up the commits per month in buckets
    counts = dict([(i, 0) for i in range(12)])
    for month in months:
        counts[month] = counts[month] + 1

    # Format the data for protovis
    data = [counts[i] for i in range(12)]

    # Normalize the counts between zero and one
    maxd = max(data)+1
    data = [d/float(maxd) for d in data]
    return data

