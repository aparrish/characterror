# Copyright (c) 2011, Adam Parrish <adam@decontextualize.com>
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

def yield_keys_recurse(d, depth):
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
		if d is None:
			d = self.data
		if len(word) > 0:
			if word[0] in d:
				return self.is_prefix(word[1:], d[word[0]])
			else:
				return False
		else:
			return True

	def is_terminal(self, word):
		try:
			alts = list(set(self.alts(word)))
			if len(alts) == 1 and alts[0] == '$':
				return True
			return False
		except KeyError:
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

	for word in ['a', 'foo', 'bar', 'baz', 'quux', 'pants', 'squirm', 'purplk', 'internationa', 'aardvarks']:
		print word + " is a word? " + str(tree.is_word(word))
		print word + " is a prefix? " + str(tree.is_prefix(word))
		print word + " is terminal? " + str(tree.is_terminal(word))

	for word in ['pan', 'shirt', 'intense', 'ax']:
		print word + ' suggestions: ' + ', '.join([str(x) for x in tree.alts(word)])
