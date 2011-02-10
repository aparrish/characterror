# FIXME: some way to keep track of frequencies

def yield_keys_recurse(d, depth):
#	print "what? " + str(d)
	if depth == 0: return
	for item in d.keys():
		if item != '_count':
			for i in range(d[item]['_count']):
				yield item
			if type(d[item]) == dict:
				for jtem in yield_keys_recurse(d[item], depth - 1):
					yield jtem

class LetterTree(object):
	def __init__(self):
		self.data = dict()

	def feed(self, word, d=None):
		#print word
		if d is None:
			d = self.data
		if len(word) > 0:
			if word[0] not in d:
				d[word[0]] = {'_count': 1}
			else:
				d[word[0]]['_count'] += 1
			self.feed(word[1:], d[word[0]])
		else:
			return

	def is_word(self, word, d=None):
		if d is None:
			d = self.data
		if len(word) > 0:
			if word[0] in d:
				return self.is_word(word[1:], d[word[0]])
			else:
				return False
		else:
			return '$' in d

	def is_prefix(self, word, d=None):
		#print "checking " + word
		if d is None:
			d = self.data
		if len(word) > 0:
			if word[0] in d:
				return self.is_prefix(word[1:], d[word[0]])
			else:
				return False
		else:
			return True

	def alts(self, word, depth=1, d=None):
		if d is None:
			d = self.data
		if len(word) == 1:
			return yield_keys_recurse(d[word], depth)
		else:
			return self.alts(word[1:], depth, d[word[0]])

	def dump(self):
		import pprint
		pprint.pprint(self.data['j'])

if __name__ == '__main__':
	import sys
	tree = LetterTree()
	for line in sys.stdin:
		line = line.strip()
		tree.feed(line + "$")

	for word in ['a', 'foo', 'bar', 'baz', 'quux', 'pants', 'squirm', 'purplk', 'internationa']:
		print word + " is a word? " + str(tree.is_word(word))
		print word + " is a prefix? " + str(tree.is_prefix(word))
	tree.dump()

	for word in ['pan', 'shirt', 'intense', 'ax']:
		print word + ' suggestions: ' + ', '.join([str(x) for x in tree.alts(word)])
