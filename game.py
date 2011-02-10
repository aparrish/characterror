import random
import string
from threading import Thread

from gamestate import GameState, GameStateManager
from lettertree import LetterTree

from tweener import Tweener

class TargetString(object):
	def __init__(self, content):
		self.content = content
	def subsume(self, letter):
		self.content += letter

class LetterSprite(object):
	def __init__(self, let, x, y):
		self.x = x
		self.y = y
		self.let = let
	def draw(self):
		fill(255)
		text(self.let, self.x, self.y)

class Fighter(object):
	def __init__(self, maxp=0, initp=0):
		self.maxp = maxp
		self.pos = initp
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
	def down(self):
		self.pos += 1
		if self.pos > self.maxp - 1: self.pos = self.maxp
		(newx, newy) = self.getxy_for_pos(self.pos)
		T.addTween(self, y=(newy-self.y), tweenTime=200, tweenType=T.OUT_EXPO)
	def draw(self):
		# draw fighter
		fill(255)
		text(self.animation[self.curframe], self.x, self.y)
		self.frames += 1
		if self.frames % 5 == 0:
			self.curframe += 1
			if self.curframe >= len(self.animation):
				self.curframe = 0

class LetterQueue(object):
	def __init__(self, length):
		assert type(length) is int, "length is not an integer"
		self.q = list()
		self.length = length
	def fillrand(self):
		for i in range(self.length):
			self.q.append(random.choice('abcdefghijklmnopqrstuvwxyz'))
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

class PlayfieldState(GameState):
	def __init__(self, tree, slots=4):
		self.tree = tree
		self.fighter = Fighter(slots, 0)
		self.letterq = LetterQueue(5)
		self.targets = list()
		for i in range(slots):
			self.targets.append(TargetString(random.choice(string.ascii_lowercase)))
		self.populate_queue(5)
		self.letter_sprites = list()

	def draw(self):

		# draw letter slots
		for i, ts in enumerate(self.targets):
			if self.tree.is_word(ts.content):
				fill(0, 255, 0)
			elif self.tree.is_prefix(ts.content):
				fill(255, 255, 0)
			else:
				fill(255)
			text(ts.content, 50, 40+(i*40))

		# draw letter queue
		fill(255)
		for i, let in enumerate(self.letterq.letters()):
			text(let, 325, 200 + (i*32))

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
			if keyCode == LEFT:
				self.cull_and_score()
		if key == ord(' '):
			self.fire()
		print [(t.content, self.tree.is_word(t.content)) for t in self.targets]

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

	def letter_arrived(self, sprite, pos):
		# called from fire(), removes sprite, adds to string, populates
		# queue (also calculates score here)
		self.letter_sprites.remove(sprite)
		self.targets[pos].subsume(sprite.let)
		self.populate_queue()

	def cull_and_score(self):
		t = self.targets[self.fighter.pos]
		if self.tree.is_word(t.content):
			self.score_word(t.content)
		else:
			print "%s is not a word, no points!" % t.content

	def cull_and_score_terminals(self):
		to_remove = list()
		for t in self.targets:
			alts = self.tree.alts(t.content) 
			if len(alts) == 1 and alts[0] == '$':
				to_remove.append(t)
		for t in to_remove:
			print "terminal word %s" % t.content
			self.score_word(t.content)
			self.targets.remove(t)

	def score_word(self, word):
		print "word %s: score %d" % (word, len(word))

	def populate_queue(self, count=1):
		words = [t.content for t in self.targets]
		suggested = list()
		for word in words:
			suggested += [x for x in self.tree.alts(word)]
		self.letterq.intersect(suggested)
		self.letterq.fill_rand_from(suggested)

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
		sketch.add_state(PlayfieldState(self.tree))

class Sketch(GameStateManager):
	def setup(self):
		print "in sketch setup for some reason?"
		size(800, 600)
		fill(0)
		background(0)
		font = createFont("pcsenior.ttf", 16)
		textFont(font)
		sketch.add_state(TitleScreenState())
		self.s = millis()
	def draw(self):
		background(0)
		tm = millis()
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

