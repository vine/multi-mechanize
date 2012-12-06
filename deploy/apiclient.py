import requests
import logging
import random
import time
import string
import simplejson as json
from collections import deque

class Transaction(object):

	actions = {
		'graphTimeline': 90,
		'explore': 30,
		'likePost': 45,
		'unlikePost': 5,
		'profile': 25,
		'followUser': 7,
		'unfollowUser': 5,
		'notifications': 30,
		'createPost': 20,
		'graphTimelinePaginate': 10,
		'comment': 15,
		'deletePost': 5,
		'authenticate': 0,
		#@todo implement additional actions:
		#'updateUsername': .5,
		#'reportPost': .5,
		#'tagFeed': 5,
		#'venueFeed': 5, 
	}

	def __init__(self):
		self.host = "http://api-stg.vineapp.com"
		self.custom_timers = {}
		self.popularityFactor = .5
		self.user = {}
		self.posts = []
		self.postCache = []
		self.following = []
		self.queue = deque()

		#create and authenciate a user to use for simulating requests
		self.setUp()

	def run(self, sleep = 1):
		"""Completes 1 iteration through the actions list (self.actions) and optionally
		sleeps afterwards. If the randomly selected number is less than the actions 
		weight it will be run. If the dry parameter is provided stats will be collected 
		but the methods will not run.
		"""
		self.sleep = sleep
		self.fillQueue()
		self.custom_timers = {}
		try:
			name = self.queue.popleft()
			logging.info("%s executing %s" % (self.user['username'],name))
			start_time = time.time()
			self.trans_start = start_time
			getattr(self, '_%s' % name)()
			self.custom_timers[name] = time.time() - start_time
		except Exception, e:
			logging.exception(' ')
			logging.error('Caught exception when running action %s: %s' % (name, e))
			raise
		finally:
			time.sleep(sleep)

	def fillQueue(self):
		while len(self.queue) == 0:
			roll = random.randrange(1, 100)
			for k, v in self.actions.items():
				if v >= roll:
					logging.info("%s:Adding %s to queue" % (self.user['username'],k))
					self.queue.append(k)

	def printSummary(self):
		print 'Client summary:'
		for k, v in self.stats['actions'].items():
			print '%s: %s' % (k, v)
		print 'Total errors: %d' % self.stats['errors']

	def request(self, endpoint, method='get', data={}, headers={}):
		"""A vineapi specific wrapper around the requests module that handles
		authentication and api errors consistently
		"""
		if 'key' in self.user:
			headers['vine-session-id'] = self.user['key']
			logging.debug("Set Key to:"+headers['vine-session-id'])
		else:
			headers = {}
			logging.debug("Blank Headers "+str(headers))
		method = method.lower()
		start_time = time.time()	
		try:
			if method in ['post', 'put']:
				response = getattr(requests, method)(self.host + endpoint, data=data, headers=headers)
			else:
				response = getattr(requests, method)(self.host + endpoint, params=data, headers=headers)
		except requests.exceptions.HTTPError, e:
			if int(response.status_code) == 500:
				pass
			else:
				raise
		except Exception, e:
			raise e
		content = response.json
		assert (response.status_code == 200 or response.status_code == 500), 'Bad Response: HTTP %s' % response.status_code
		#assert (response.status_code == 200 and not 'error' in content), 'User: %s receiver error message: %s' % (self.user,content['data']['error'])
		#if int(response.status_code) != 200:
		#	if not 'error' in content:
		#		#logging.error(content['error'])
		#		raise Exception()

		return content['data']

	def setUp(self):
		"""
		Creates a new user account and authenticates it in preperation
		for the simulated requests
		"""
		user = {
			'username': self._randomString(10),
			'email': '%s@gmail.com' % self._randomString(10),
			'password': 'dund3rm1fl1n',
			'description': 'Simulated user',
			'authenticate': 1
		}
		try:
			logging.info('Configuring new simulation user')
			user.update(self.request('/users', 'post', user))
			self.user = user
			logging.debug(json.dumps(self.user))
		except Exception, e:
			logging.error('Failed to create user with exception: %s' % e)
			raise e

	def _authenticate(self):
		#first log out
		self.request('/users/authenticate', 'delete')
		user = {
			'email': self.user['email'],
			'password': self.user['password']
		}
		self.user.pop('key')
		response = self.request('/users/authenticate', 'post', data=self.user)
		assert (response), "User: %s Error excepting response data" % (self.user['username'])
		self.user['key'] = response['key']
		return True

	def _comment(self):
		post = self._getRandomPost()
		if post:
			comment = {'comment': 'simulated comment'}
			self.request('/posts/%d/comments' % post['postId'])
			return True
		return False

	def _createPost(self):
		post = {
			'videoUrl': 'http://vines.s3.amazonaws.com/videos/75625AE1-37CF-4B5F-B8E0-4DAC7EDEA680-36383-000009C6FDBA3A4E_0.7.1.mp4',
			'thumbnailUrl': 'https://vines.s3.amazonaws.com/avatars/47616DAB-B4FC-40B0-898C-62AC2F0A1007-5012-00000D63E44C2FF2.jpg',
			'description': 'Simulated post #simulated'
		}
		response = self.request('/posts', 'post', data=post)
		assert (response), "User: %s Error excepting response data" % (self.user['username'])
		try:
			self.posts.append(response['postId'])
		except TypeError,e:
			logging.error("%s post failed because postId type error, response was %s" % (self.user['username'],response))
		return True

	def _deletePost(self):
		if len(self.posts) > 0:
			postId = self.posts.pop(random.randrange(len(self.posts)))
			self.request('/posts/%d' % postId, 'delete')
			return True
		return False

	def _explore(self):
		response = self.request('/posts/explore')
		assert (response), "User: %s Error excepting response data" % (self.user['username'])
		self._rebuildPostCache(response['popular']+response['recent'])
		return True

	def _followUser(self):
		for i in range(5):
			#try to find a user we can follow from the cache
			post = self._getRandomPost()
			try:
				if post['userId'] not in self.following and post['userId'] != self.user['userId']:
					self.request('/users/%d/followers' % post['userId'], 'post')
					return True
			except TypeError,e:
				pass
		return False

	def _getRandomPost(self):
		if len(self.postCache) > 0:
			return random.choice(self.postCache)
		return None

	def _graphTimeline(self):
		"""
		Retrieve the users graph timeline and store the posts in the cache.
		If there are no posts in the users graph than no posts are cached
		"""
		#retrieve a new set of posts
		response = self.request('/timelines/graph')
		assert (response), "User: %s Error excepting response data" % (self.user['username'])
		if response['count'] > 0:
			self._rebuildPostCache(response['records'])
		return True

	def _graphTimelinePaginate(self):
		response = self.request('/timelines/graph?page=%d' % random.randrange(4))
		assert (response), "User: %s Error excepting response data" % (self.user['username'])
		return True

	def _likePost(self):
		post = self._getRandomPost()
		if post:
			#like a random post from the post cache
			self.request('/posts/%d/likes' % post['postId'], 'post')
			return True
		return False

        def _unlikePost(self):
                post = self._getRandomPost()
                if post:
                        #like a random post from the post cache
                        self.request('/posts/%d/likes' % post['postId'], 'delete')
                        return True
                return False

	def _notifications(self):
		self.request('/users/%d/notifications' % self.user['userId'])
		return True

	def _profile(self):
		post = self._getRandomPost()
		if post:
			self.request('/users/profiles/%d' % post['userId'])
			return True
		return False

	def _randomString(self, length, chars=[]):
		if not chars:
			chars = string.ascii_lowercase + string.digits
		return ''.join(random.choice(chars) for _ in range(length))

	def _rebuildPostCache(self, posts):
		self.postCache = []
		for post in posts:
			#to save space only store the ids
			self.postCache.append({'postId': post['postId'], 'userId': post['userId']})	

	def _unfollowUser(self):
		if len(self.following) > 0:
			userId = self.following.pop(random.randrange(len(self.following)))
			self.request('/users/%d/following' % userId, 'delete')
			return True
		return False

if __name__ == '__main__':
	#logging.basicConfig(level=logging.DEBUG)
	trans = Transaction()
	trans.run()
	trans.printSummary()
