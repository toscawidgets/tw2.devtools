""" Helper functions for scraping repos (github and someday bitbucket) """

import github2.client
import urllib2
import simplejson
import warnings
from datetime import datetime, timedelta

# NOTE -- we can't actually use multiprocessing here.
# b/c it eats up a tremendous amount of memory.
#import multiprocessing

## Some constants ##
# The number of results github returns 'per-page'
github_rate = 35
# How many pages we're going to try to get at once.
github_tries = 20
# A 'github_theoretical max' of the number of commits we can handle.
github_theoretical_max = github_rate * github_tries

def _get_commits(url):
    """ Workhorse function. """
    commits = {'commits':[]}
    try:
        p = urllib2.urlopen(url)
        commits = simplejson.loads(p.read())
        p.close()
    except urllib2.HTTPError, e:
        pass
    return commits

def _get_github_commits(args):
    """ This gets called in parallel so we spam the hell out of github. """
    url, page = args
    return _get_commits(url.format(page=page))['commits']

# NOTE -- we can't actually use multiprocessing here.
# b/c it eats up a tremendous amount of memory.
#pool = multiprocessing.Pool(processes=github_tries)

class ServiceHandler(object):
    """ Abstract Baseclass """

    def get_all_commit_timestamps(self, account, module, branch):
        raise NotImplementedError

    def has_package(self, account, module):
        raise NotImplementedError

class BitbucketHandler(ServiceHandler):
    """ Get info from bitbucket API """
    api_url = "https://api.bitbucket.org/1.0"

    def get_all_commit_timestamps(self, account, module, branch):
        """ Get all commits for a bitbucket project.

        The upshot is that bitbucket tells us the total count of commits
        for a repo, so we can be sane about how many we ask for.

        The downshot is, you can't ask for a 'range' of commits without knowing
        which commit (by a hash) the range starts on.  This means we cannot do
        this in parallel, which means we have wait and wait.  Sucks to your
        ass-mar, bitbucket.
        """

        limit = 50  # This is the max bitbucket limit
        date_format = '%Y-%m-%d %H:%M:%S'
        base_url = self.api_url+"/repositories/{account}/{module}/changesets/"
        url = base_url.format(**locals()) + "?limit=1"
        p = urllib2.urlopen(url)
        data = simplejson.loads(p.read())
        p.close()
        count, start = data['count'], data['changesets'][0]['node']

        commits = data['changesets']
        n = len(commits)
        while n < count:
            if count - n < limit:  limit = count - n + 1
            url = (base_url+"?start={start}&limit={limit}").format(**locals())
            p = urllib2.urlopen(url)
            data = simplejson.loads(p.read())
            p.close()
            commits += reversed(data['changesets'][:-1])
            n = len(commits)
            start = commits[-1]['node']

        if len(commits) != count:
            raise ValueError, "%s %s commits didn't line up."%(account, module)

        timestamps = [
            datetime.strptime(commit['timestamp'], date_format)
            for commit in commits
        ]

        return timestamps

    def has_package(self, account, module):
        """ Return true if `account` has a repo with name `module`. """
        base_url = self.api_url + "/users/{account}/"
        url = base_url.format(**locals())
        p = urllib2.urlopen(url)
        data = simplejson.loads(p.read())
        p.close()
        repos = data['repositories']
        return module in [repo['slug'] for repo in repos]

class GithubHandler(ServiceHandler):
    """ Get info from github API """
    api_url = "http://github.com/api/v2/json"

    def get_all_commit_timestamps(self, account, module, branch):
        """ Get all commits for a github project.

        Github's api paginates the results at 35 commits per page.  That makes
        things very slow.  Here we do all the requests for all the pages in
        parallel which should drastically speed things up.

        Github also doesn't tell us how many commits there are, so we can't
        plan accordingly.  Right now, we just 'guess' there are no more than
        20 pages of commits.  If there are, we're screwed and we raise a
        ValueError.
        """

        date_format = '%Y-%m-%dT%H:%M:%S'
        base_url = self.api_url+"/commits/list/{account}/{module}/{branch}"
        url = base_url.format(**locals()) + "?page={page}"
        arg_pairs = zip([url] * github_tries, range(1, github_tries+1))

        # NOTE -- we can't actually use multiprocessing here.
        # b/c it eats up a tremendous amount of memory.
        #commits = sum(pool.map(_get_github_commits, arg_pairs), [])
        commits = sum(map(_get_github_commits, arg_pairs), [])

        if len(commits) >= github_theoretical_max:
            # Try increasing `github_tries` if this happens to you.
            raise ValueError, "%s %s exceeded max commits." % (account, module)

        # Convert authored_date to a python datetime
        timestamps = [
            datetime.strptime(commit['authored_date'][:-6], date_format)
            for commit in commits
        ]

        return timestamps

    def has_package(self, account, module):
        """ Return true if `account` has a repo with name `module`. """
        base_url = self.api_url + "/repos/show/{account}/{module}"
        url = base_url.format(**locals())

        try:
            urllib2.urlopen(url).close()
        except urllib2.HTTPError, e:
            return False

        return True

def commits_per_month(module):
    # If you'd like to add your service/account here, please do.
    # Order matters.
    known_repos = [
        ('bitbucket',   'toscawidgets'),
        ('github',      'ralphbean'),
        ('bitbucket',   'ralphbean'),
        ('bitbucket',   'paj'),
        ('bitbucket',   'percious'),
        ('bitbucket',   'josephtate'),
        ('github',      'decause'),
    ]
    service_handlers = {
        'bitbucket' : BitbucketHandler(),
        'github' : GithubHandler(),
    }

    branch = 'master'

    for service, account in known_repos:
        handler = service_handlers[service]
        if not handler.has_package(account, module):
            continue
        else:
            # We've found a repo that has this module, so we'll
            # finish this loop and exit.
            pass

        # Go talk to github
        timestamps = handler.get_all_commit_timestamps(account, module, branch)

        # Do two things.
        # 1) Only keep commits from within the last year
        # 2) Mangle the month to be from 0-11, starting with this month.
        one_year_ago = datetime.now() - timedelta(days=365)
        months = [(t.month + 12 - datetime.now().month)%12
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

        # Exit the loop and function `prematurely`.
        return data

    # If we got here, then we never found a service/account combo that had
    # a repo with the module we wanted.  Therefore, we'll just return an
    # empty list signifying that we don't know about any commits.
    warnings.warn("No service/account pair: '%s'" % module)
    return []
