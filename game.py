import random
import string
from threading import Thread

from gamestate import GameState, GameStateManager
from lettertree import LetterTree

from tweener import Tweener

from java import lang

# janky but accurate!
letterprob = ''.join([
	'qjx',
	'z' * 2,
	'v' * 5,
	'w' * 6,
	'k' * 7,
	'f' * 8,
	'y' * 9,
	'b' * 12,
	'h' * 14,
	'm' * 17,
	'p' * 17,
	'g' * 17,
	'u' * 20,
	'c' * 22,
	'd' * 22,
	'l' * 31,
	't' * 36,
	'n' * 37,
	'o' * 37,
	'r' * 42,
	'a' * 47,
	'i' * 48,
	's' * 56,
	'e' * 69])

class TargetString(object):
	def __init__(self, content, tree, x, y):
		self.content = content
		self.tree = tree
		self.x = x
		self.y = y
		self.is_word = False
		self.is_prefix = True # assuming our corpus contains every letter as initial
		self.alpha = 255
		self.textsize = 16
	def subsume(self, letter):
		self.content += letter
		self.is_word = self.tree.is_word(self.content)
		self.is_prefix = self.tree.is_prefix(self.content)
	def draw(self):
		if self.is_word:
			fill(0, 255, 0, self.alpha)
		elif self.is_prefix:
			fill(255, 255, 0, self.alpha)
		textSize(self.textsize)
		textAlign(LEFT)
		text(self.content, self.x, self.y)

class LetterSprite(object):
	def __init__(self, let, x, y):
		self.x = x
		self.y = y
		self.let = let
	def draw(self):
		fill(255)
		print self.x, self.y
		textAlign(LEFT)
		text(self.let, self.x, self.y)

class Fighter(object):
	def __init__(self, letterq, maxp=0, initp=0):
		self.maxp = maxp
		self.pos = initp
		self.letterq = letterq
		(self.x, self.y) = self.getxy_for_pos(initp)
		self.frames = 0
		self.animation = ('<@#', '<@%', '<@*')
		self.curframe = 0
	def getxy_for_pos(self, pos):
		return (300, 40+(pos*40))
	def up(self):
		self.pos -= 1
		if self.pos < 0: self.pos = 0
		(newx, newy) = self.getxy_for_pos(self.pos)
		T.addTween(self, y=(newy-self.y), tweenTime=200, tweenType=T.OUT_EXPO)
		T.addTween(self.letterq, y=(newy-self.y), tweenTime=250,
			tweenType=T.OUT_EXPO)
	def down(self):
		self.pos += 1
		if self.pos > self.maxp - 1: self.pos = self.maxp
		(newx, newy) = self.getxy_for_pos(self.pos)
		T.addTween(self, y=(newy-self.y), tweenTime=200, tweenType=T.OUT_EXPO)
		T.addTween(self.letterq, y=(newy-self.y), tweenTime=250,
			tweenType=T.OUT_EXPO)
	def draw(self):
		# draw fighter
		fill(255)
		textAlign(LEFT)
		text(self.animation[self.curframe], self.x, self.y)
		self.frames += 1
		if self.frames % 5 == 0:
			self.curframe += 1
			if self.curframe >= len(self.animation):
				self.curframe = 0

class LetterQueue(object):
	def __init__(self, length, x, y):
		assert type(length) is int, "length is not an integer"
		self.q = list()
		self.length = length
		self.x = x
		self.y = y
	def fillrand(self):
		for i in range(self.length):
			self.q.append(random.choice(letterprob))
	def append(self, letter):
		assert type(letter) is str, "letter is not string"
		assert len(letter) == 1, "letter is not string of length 1"
		self.q.append(letter)
		if len(self.q) > self.length:
			self.q = self.q[:length]
	def fill_rand_from(self, seq):
		# TODO check if seq is iterable
		while len(self.q) < self.length:
			self.q.append(random.choice(seq))
	def intersect(self, seq):
		tocheck = set(seq)
		newq = list()
		for ch in self.q:
			if ch in tocheck:
				newq.append(ch)
		self.q = newq
	def pop(self):
		return self.q.pop(0)
	def letters(self):
		return self.q
	def draw(self):
		textAlign(LEFT)
		text(" ".join(self.letters()), self.x, self.y)

class PlayfieldState(GameState):
	def __init__(self, tree, scorer, slots=5):
		self.tree = tree
		self.letterq = LetterQueue(5, 364, 40)
		self.fighter = Fighter(self.letterq, slots-1, 0)
		self.targets = [None] * slots
		for i in range(slots):
			self.add_target_at_slot(i)
		self.populate_queue()
		self.letter_sprites = list()
		self.scorer = scorer

	def add_target_at_slot(self, idx):
		target = TargetString(random.choice(letterprob),
			self.tree, x=-20, y=40+(idx*40))
		T.addTween(target, x=70, tweenTime=200, tweenType=T.OUT_EXPO,
			tweenDelay=1000)
		self.targets[idx] = target

	def draw(self):

		textAlign(LEFT)
		# draw letter slots
		for i, ts in enumerate(self.targets):
			ts.draw()

		# draw letter queue
		fill(255)
		self.letterq.draw()

		# draw sprites
		for sp in self.letter_sprites:
			sp.draw()

		self.fighter.draw()

	def keyPressed(self):
		if key == CODED:
			if keyCode == UP:
				self.fighter.up()
			if keyCode == DOWN:
				self.fighter.down()
			if keyCode == RIGHT: # discard letter
				self.letterq.pop()
				self.populate_queue()
		if key == ord('z'):
			self.fire()
		elif key == ord('x'):
			self.detonate()
		print [(t.content, self.tree.is_word(t.content)) for t in self.targets]

	def detonate(self):
		t = self.targets[self.fighter.pos]
		if self.tree.is_word(t.content):
			self.score_target(t)
			T.addTween(t, alpha=-255, textsize=16,
				onCompleteFunction=lambda: self.remove_target(t))
		else:
			self.scorer.combobreak(t.x, t.y)
			T.addTween(t, alpha=-255, textsize=16,
				onCompleteFunction=lambda: self.remove_target(t))

	def fire(self):
		popped = self.letterq.pop()
		# create sprite
		sprite = LetterSprite(popped, self.fighter.x, self.fighter.y)
		destx = 50 + (len(self.targets[self.fighter.pos].content) * 16)
		desty = 40 + (self.fighter.pos * 40)
		# tween sprite to new position, will call letter_arrived when
		# completed
		destpos = self.fighter.pos
		T.addTween(sprite, x=(destx-self.fighter.x), y=(desty-self.fighter.y),
			tweenTime=400, tweenType=T.OUT_EXPO,
			onCompleteFunction=lambda: self.letter_arrived(sprite, destpos))
		# add to list so we can draw it
		self.letter_sprites.append(sprite)
		self.scorer.score_letter(popped, destx, desty)

	def letter_arrived(self, sprite, pos):
		# called from fire(), removes sprite, adds to string, populates
		# queue (also calculates score here)
		self.letter_sprites.remove(sprite)
		self.targets[pos].subsume(sprite.let)
		self.cull_and_score_terminals()
		self.populate_queue()

	def cull_and_score_terminals(self):
		compl = lambda x: self.remove_target(x)
		for t in self.targets:
			if self.tree.is_terminal(t.content):
				if self.tree.is_word(t.content):
					self.score_target(t)
					T.addTween(t, alpha=-255, textsize=16, tweenTime=500,
						onCompleteFunction=compl(t))
				else:
					self.scorer.combobreak(t.x, t.y)
					T.addTween(t, alpha=-255, textsize=16, tweenTime=500,
						onCompleteFunction=compl(t))

	def remove_target(self, t):
		assert t in self.targets, "couldn't find target!"
		print t, t.content
		idx = self.targets.index(t)
		print "found target to remove at index %d" % idx
		self.add_target_at_slot(idx)

	def remove_target_idx(self, idx):
		self.add_target_at_slot(idx)

	def score_target(self, target):
		self.scorer.score_word(target.content, target.x, target.y)

	def populate_queue(self):
		words = [t.content for t in self.targets]
		suggested = list()
		all_possible = list()
		for word in words:
			if self.tree.is_prefix(word):
				word_possible = [x for x in self.tree.alts(word)]
				suggested += random.sample(word_possible,
					min(len(word), len(word_possible)))
				all_possible += word_possible
		self.letterq.intersect(all_possible)
		self.letterq.fill_rand_from(suggested)

class StringSprite(object):
	def __init__(self, content, x, y, textsize=16, r=255, g=255, b=255, a=255):
		self.content = content
		self.x = x
		self.y = y
		self.r = r
		self.g = g
		self.b = b
		self.a = a
		self.textsize = textsize
	def draw(self):
		textSize(self.textsize)
		fill(self.r, self.g, self.b, self.a)
		textAlign(CENTER)
		text(self.content, self.x, self.y)

class ScoreState(GameState):

	def __init__(self):
		self.score = 0
		self.multiplier = 1.0
		self.score_sprites = list()

	def score_letter(self, let, x, y):
		letscore = 100 * self.multiplier
		sprite = StringSprite(str(letscore), x, y, textsize=8)
		T.addTween(sprite, textsize=8, y=-32, a=-255, tweenTime=1000,
			tweenType=T.OUT_EXPO,
			onCompleteFunction=lambda: self.remove_sprite(sprite))
		self.score_sprites.append(sprite)
		self.score += letscore
		self.multiplier += 0.1

	def score_word(self, word, x, y):
		wordscore = 0
		for let in word:
			if let in 'qjxz':
				wordscore += 5000
			elif let in 'vwkf':
				wordscore += 2500
			else:
				wordscore += 1000
		wordscore = int(wordscore * self.multiplier)
		sprite = StringSprite(str(wordscore), textsize=8, x=x, y=y, r=0, g=255, b=0)
		T.addTween(sprite, textsize=8, y=(y-32), g=0, a=0, tweenTime=1000,
			tweenType=T.OUT_EXPO,
			onCompleteFunction=lambda: self.remove_sprite(sprite))
		self.score_sprites.append(sprite)
		self.score += wordscore
		self.multiplier += 1

	def combobreak(self, x, y):
		self.multiplier = 1.0
		sprite = StringSprite("BREAK", x, y, textsize=8,
			r=255, g=0, b=0)
		T.addTween(sprite, textsize=8, y=(y-32), a=0, tweenTime=1000,
			tweenType=T.OUT_EXPO,
			onCompleteFunction=lambda: self.remove_sprite(sprite))
		self.score_sprites.append(sprite)

	def remove_sprite(self, sprite):
		self.score_sprites.remove(sprite)

	def draw(self):
		for spr in self.score_sprites:
			spr.draw()
		fill(255)
		textSize(16)
		textAlign(LEFT)
		text(str(self.score), 16, 16)
		text(str(self.multiplier), width-100, 16)

def loadtree(callback):
	print "loading wordlist"
	tree = LetterTree()
	for line in open('wordlist_short'):
		line = line.strip()
		tree.feed(line + "$")
	callback(tree)

class TitleScreenState(GameState):
	def __init__(self):
		self.title = "LEXCONNEX"
		self.alpha = 255
		self.colors = [(64, 192, 0), (96, 224, 32), (128, 255, 64),
			(160, 0, 96), (192, 32, 128), (224, 64, 160),
			(255, 96, 192), (0, 128, 224), (32, 160, 255)]
		self.thread = None
		self.init_loading_threads()
		self.fading = False

	def init_loading_threads(self):
		# just running one thread to load resources for now
		self.thread = Thread(target=loadtree, args=(self.tree_load_done,))
		print "starting thread"
		self.thread.start()

	def tree_load_done(self, tree):
		self.tree = tree

	def draw(self):
		# draw banner
		textSize(64)
		xcenter = width / 2.0
		ypos = height / 3.0
		xstart = xcenter - (textWidth(self.title) / 2.0)
		pushMatrix()
		translate(xstart, ypos)
		idx = (frameCount / 32) % 9
		this_col = self.colors[idx:] + self.colors[:idx]
		for i, ch in enumerate(self.title):
			fill(this_col[i][0], this_col[i][1], this_col[i][2], self.alpha)
			text(ch, 0, 0)
			translate(64, 0)
		popMatrix()

		# loading or "Z to start"
		textAlign(CENTER)
		fill(255, 255, 0, self.alpha)
		textSize(16)
		if self.thread.isAlive():
			num = (frameCount / 9) % 4
			ch = '|/-\\'
			text("LOADING " + ch[num], xcenter, 2 * height / 3.0)
		else:
			text("PRESS <Z> TO START", xcenter, 2 * (height / 3.0))
		textAlign(LEFT)

	def keyPressed(self):
		if self.thread.isAlive():
			return
		if self.fading:
			return
		if key == ord('z'):
			self.fading = True
			T.addTween(self, alpha=-255, tweenTime=1000, tweenType=T.OUT_EXPO,
				onCompleteFunction=self.faded_out)

	def faded_out(self):
		# when fadeout completes, this is called
		self.manager.mute(self)
		scorer = ScoreState()
		sketch.add_state(scorer)
		sketch.add_state(PlayfieldState(self.tree, scorer))

class Sketch(GameStateManager):
	def setup(self):
		print "in sketch setup for some reason?"
		frameRate(30)
		size(800, 600)
		fill(0)
		background(0)
		font = createFont("pcsenior.ttf", 16)
		textFont(font)
		sketch.add_state(TitleScreenState())
		self.s = millis()
	def draw(self):
		background(0)
		tm = float(millis())
		delta = tm - self.s
		self.s = tm
		T.update(delta)
		super(Sketch, self).draw()

T = Tweener()
sketch = Sketch()

def setup():
	sketch.setup()
def draw():
	sketch.draw()
def mouseClicked():
	sketch.mouseClicked()
def keyPressed():
	sketch.keyPressed()

