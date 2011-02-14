import random
import string
from threading import Thread

from gamestate import GameState, GameStateManager
from lettertree import LetterTree

from tweener import Tweener

from java import lang
from ddf.minim import Minim

# janky but accurate!
initletterprob = ''.join([
	'x' * 1,
	'y' * 1,
	'z' * 1,
	'q' * 1,
	'j' * 2,
	'k' * 3,
	'v' * 4,
	'n' * 5,
	'w' * 5,
	'i' * 6,
	'u' * 7,
	'o' * 7,
	'l' * 7,
	'h' * 8,
	'g' * 8,
	'e' * 9,
	'f' * 9,
	't' * 12,
	'r' * 13,
	'm' * 13,
	'd' * 13,
	'a' * 13,
	'b' * 14,
	'p' * 19,
	'c' * 20,
	's' * 28])

play_offset_x = 100
fighter_offset_x = 250
play_offset_y = 100

def overdraw(things, count):
	return [random.choice(things) for i in range(count)]

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
		self.active = True
		self.unique = random.randrange(100)
	def subsume(self, letter):
		self.content += letter
		self.is_word = self.tree.is_word(self.content)
		self.is_prefix = self.tree.is_prefix(self.content)
	def draw(self):
		if self.is_word:
			fill(0, 255, 0, self.alpha)
		elif self.is_prefix:
			fill(255, 255, 255, self.alpha)
		textSize(self.textsize)
		textAlign(LEFT)
		for i, ch in enumerate(self.content):
			if len(self.content) == 1 and i == 0:
				fill(255, 0, 0, self.alpha)
				xoff = sin(i + self.unique + millis() / 50.0) * 1.25
				yoff = cos(i + self.unique + millis() / 54.0) * 1.25
			else:
				xoff = sin(i + self.unique + millis() / 200.0) * 1.25
				yoff = cos(i + self.unique + millis() / 205.0) * 1.25
			text(ch, self.x + (i*16) + xoff, self.y + yoff)

class LetterSprite(object):
	def __init__(self, let, x, y):
		self.x = x
		self.y = y
		self.let = let
	def draw(self):
		fill(255)
		textAlign(LEFT)
		text(self.let, self.x, self.y)

class Fighter(object):
	def __init__(self, letterq, maxp=0, initp=0):
		self.maxp = maxp
		self.pos = initp
		self.letterq = letterq
		(self.x, self.y) = self.getxy_for_pos(initp)
		self.animation = ('<[@(#', '<[@(%', '<[@(*')
		self.colors = ((0,255,255),(0,192,192),(0,192,192),(0,255,255),(255,0,0))
		self.curframe = 0
	def getxy_for_pos(self, pos):
		return (fighter_offset_x + play_offset_x, play_offset_y+(pos*40))
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
		textAlign(LEFT)
		textSize(16)
		for i, (ch, col) in enumerate(zip(self.animation[self.curframe],
				self.colors)):
			fill(col[0],col[1],col[2])
			text(ch, self.x + (i*16), self.y)
		if frameCount % 5 == 0:
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
	def shuffle(self):
		random.shuffle(self.q)
	def draw(self):
		textAlign(LEFT)
		for i, ch in enumerate(self.letters()):
			fill(255 - i * 10)
			textSize(16 - i)
			yoff = sin(i + millis() / 300.0) * 1.8
			text(ch, self.x + (i*20), self.y + yoff)

class PlayfieldState(GameState):
	def __init__(self, tree, scorer, mode, slots=5):
		self.tree = tree
		self.letterq = LetterQueue(5, play_offset_x + fighter_offset_x + 96,
			play_offset_y)
		self.fighter = Fighter(self.letterq, slots-1, 0)
		self.targets = [None] * slots
		for i in range(slots):
			self.add_target_at_slot(i)
		self.populate_queue()
		self.letter_sprites = list()
		self.scorer = scorer
		self.paused = False
		self.mode = mode
		self.fire_listeners = list()

	def add_fire_listener(self, listener):
		self.fire_listeners.append(listener)

	def add_target_at_slot(self, idx):
		target = TargetString(random.choice(initletterprob),
			self.tree, x=-20, y=play_offset_y+(idx*40))
		T.addTween(target, x=(play_offset_x+20), tweenTime=200,
			tweenType=T.OUT_EXPO, tweenDelay=1000)
		self.targets[idx] = target

	def draw(self):

		textAlign(LEFT)
		# draw letter slots
		for i, ts in enumerate(self.targets):
			ts.draw()

		# draw sprites
		for sp in self.letter_sprites:
			sp.draw()

		self.fighter.draw()

		# draw letter queue
		fill(255)
		self.letterq.draw()

	def keyPressed(self):
		if self.paused: return
		if key == CODED:
			if keyCode == UP:
				self.fighter.up()
			elif keyCode == DOWN:
				self.fighter.down()
		if key == ord('\n'):
			self.detonate()
		elif key == ord('z'):
			self.fire()
		elif key == ord('x'):
			self.shuffle_queue()

	def shuffle_queue(self):
		self.letterq.shuffle()
		sounds['discard'].play(0)
		self.scorer.attenuate_multiplier(0.5)

	def detonate(self):
		t = self.targets[self.fighter.pos]
		if not(t.active):
			return
		t.active = False
		if self.tree.is_word(t.content):
			sounds['success'].play(0)
			self.score_target(t)
			T.addTween(t, alpha=-255, textsize=16,
				onCompleteFunction=lambda: self.remove_target(t))
		else:
			sounds['failure'].play(0)
			self.scorer.combobreak(t.x + len(t.content)*16, t.y)
			T.addTween(t, alpha=-255, textsize=16,
				onCompleteFunction=lambda: self.remove_target(t))

	def fire(self):
		# only fire if target able to accept
		t = self.targets[self.fighter.pos]
		if not(t.active):
			return
		sounds['shoot'].play(0)
		t.active = False
		popped = self.letterq.pop()
		# create sprite
		sprite = LetterSprite(popped, self.fighter.x, self.fighter.y)
		destx = play_offset_x + (len(self.targets[self.fighter.pos].content) * 16)
		desty = play_offset_y + (self.fighter.pos * 40)
		# tween sprite to new position, will call letter_arrived when
		# completed
		destpos = self.fighter.pos
		T.addTween(sprite, x=(destx-self.fighter.x), y=(desty-self.fighter.y),
			tweenTime=400, tweenType=T.OUT_EXPO,
			onCompleteFunction=lambda: self.letter_arrived(sprite, destpos))
		# add to list so we can draw it
		self.letter_sprites.append(sprite)
		for listener in self.fire_listeners:
			if hasattr(listener, 'fired'):
				listener.fired(popped)

	def letter_arrived(self, sprite, pos):
		# called from fire(), removes sprite, adds to string, populates
		# queue (also calculates score here)
		self.letter_sprites.remove(sprite)
		# add letter to target string, reactivate
		self.targets[pos].subsume(sprite.let)
		self.targets[pos].active = True
		if self.tree.is_prefix(self.targets[pos].content):
			self.scorer.score_letter(sprite.let, sprite.x, sprite.y)
		self.cull_and_score_terminals()
		self.populate_queue()

	def cull_and_score_terminals(self):
		compl = lambda x: self.remove_target(x)
		for t in self.targets:
			if self.tree.is_terminal(t.content):
				t.active = False
				if self.tree.is_word(t.content):
					sounds['success'].play(0)
					self.score_target(t)
					T.addTween(t, alpha=-255, textsize=16, tweenTime=500,
						onCompleteFunction=compl(t))
				else:
					sounds['failure'].play(0)
					self.scorer.combobreak(t.x + len(t.content)*16, t.y)
					T.addTween(t, alpha=-255, textsize=16, tweenTime=500,
						onCompleteFunction=compl(t))

	def remove_target(self, t):
		assert t in self.targets, "couldn't find target!"
		idx = self.targets.index(t)
		print "found target to remove at index %d" % idx
		self.add_target_at_slot(idx)

	def remove_target_idx(self, idx):
		self.add_target_at_slot(idx)

	def score_target(self, target):
		self.scorer.score_word(target.content, target.x + (len(target.content)*20),
			target.y)

	def populate_queue(self):
		words = [t.content for t in self.targets]
		suggested = list()
		all_possible = list()
		for word in words:
			if self.tree.is_prefix(word):
				word_possible = [x for x in self.tree.alts(word) if x != '$']
				# fill queue with more letters to finish longer words
				suggested += overdraw(word_possible, int(1.1*len(word)))
				all_possible += word_possible
		self.letterq.intersect(all_possible)
		self.letterq.fill_rand_from(suggested)

	def timer_done(self):
		self.paused = True
		sounds['etude2'].play(0)
		for sp in self.letter_sprites:
			T.removeTweeningFrom(sp)
		self.manager.add_state(DisplayScoreState(self.scorer.score, self.mode))

class DisplayScoreState(GameState):
	def __init__(self, score, mode):
		self.score = score
		self.mode = mode
	def draw(self):
		fill(0, 128)
		rect(0, 0, width, height)
		templ = \
"""
+---------------------------+
|        FINAL SCORE        |
|                           |
|                           |
|                           |
|       <Esc> for menu      |
| <C> to copy tweet w/score |
|     to your clipboard     |
+---------------------------+"""
		textAlign(CENTER, CENTER)
		textSize(16)
		fill(255)
		text(templ, width/2, height/2)
		textSize(32)
		text(str(self.score), width/2, height/2 - 16)
	def keyPressed(self):
		if key == 27:
			self.manager.remove_instances([PlayfieldState, ScoreState, TimerState,
				ChallengeState])
			titles = self.manager.get_instances([TitleScreenState])
			assert len(titles) == 1, "wrong number of title screen states"
			titles[0].fade_in()
			self.manager.remove_state(self)
		elif key == ord('c'):
			print 'attempting to copy'
			modestrs = {'90sec': 'in ninety seconds', '4min': 'in four minutes',
				'challenge': 'with only 50 letters'}
			modestr = modestrs.get(self.mode, '')
			from hashlib import md5
			shorthash = md5(str(self.score)+self.mode).hexdigest()[:6]
			from java.awt.datatransfer import StringSelection
			from java.awt import Toolkit
			clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
			clipboard.setContents(StringSelection("I just scored %d points %s on Characterror! http://shorturl/something?%s" % (self.score, modestr, shorthash)), None)

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
		self.multiplier = 10
		self.score_sprites = list()

	def score_letter(self, let, x, y):
		letscore = 100 * self.multiplier
		sprite = StringSprite(str(letscore), x, y, textsize=8)
		T.addTween(sprite, y=-32, a=-255, tweenTime=1500, tweenType=T.OUT_EXPO,
			onCompleteFunction=lambda: self.remove_sprite(sprite))
		self.score_sprites.append(sprite)
		self.score += letscore
		self.multiplier += 1

	def score_word(self, word, x, y):
		wordscore = int(((len(word)*len(word))*0.5) * 1000)
		wordscore = wordscore * self.multiplier
		sprite = StringSprite(str(wordscore), textsize=8, x=x, y=y, r=0, g=255, b=0)
		T.addTween(sprite, y=-32, g=0, a=-127, tweenTime=1000,
			tweenType=T.OUT_EXPO,
			onCompleteFunction=lambda: self.remove_sprite(sprite))
		self.score_sprites.append(sprite)
		self.score += wordscore
		self.multiplier += 10

	def combobreak(self, x, y):
		if self.multiplier > 10:
			self.multiplier = 10
		sprite = StringSprite("BREAK", x, y, textsize=8,
			r=255, g=0, b=0)
		T.addTween(sprite, y=-32, a=-127, tweenTime=1000, tweenType=T.OUT_EXPO,
			onCompleteFunction=lambda: self.remove_sprite(sprite))
		self.score_sprites.append(sprite)

	def attenuate_multiplier(self, amount):
		self.multiplier = int(self.multiplier * amount)

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

class ChallengeState(GameState):
	def __init__(self, target_count, callback):
		self.target_count = target_count
		self.fire_count = 0
		self.callback = callback
	def fired(self, let):
		self.fire_count += 1
		if self.fire_count >= self.target_count:
			self.callback()
	def draw(self):
		textSize(32)
		textAlign(CENTER)
		if self.fire_count > self.target_count * 0.9:
			fill(255, 0, 0)
		else:
			fill(255)
		text("%d / %d" % (self.fire_count, self.target_count), width/2, height-100)

class TimerState(GameState):
	def __init__(self, seconds, callback):
		self.seconds = seconds
		self.callback = callback
		self.called_callback = False
		self.last_remaining = 0
	def start(self):
		self.started = millis()
	def draw(self):
		delta = millis() - self.started
		delta_seconds = int(delta / 1000)
		remaining = self.seconds - delta_seconds

		# play tick if eight or fewer seconds left
		if remaining != self.last_remaining and remaining <= 8 and remaining > 0:
			sounds['tick'].play(0)
		self.last_remaining = remaining

		# red if only one eight of the time remains
		textSize(32)
		textAlign(CENTER)
		if remaining <= self.seconds / 8:
			fill(255, 0, 0)
		else:
			fill(255)

		# call callback if time's up
		if remaining <= 0:
			remaining = 0
			if self.called_callback is False:
				self.called_callback = True
				self.callback()

		minutes = remaining / 60
		second_remainder = remaining % 60
		text("%d:%02d" % (minutes, second_remainder), width/2, height - 100)

class StarFieldState(GameState):
	def __init__(self, layer_count=3, star_count=100):
		self.layers = list()
		self.layer_count = layer_count
		for i in range(layer_count):
			field = [(random.randrange(width),random.randrange(height)) for i \
					in range(star_count)]
			self.layers.append(field)
	def draw(self):
		textSize(8)
		for i, layer in enumerate(self.layers):
			for x, y in layer:
				fill((i + 1) * (255.0 / self.layer_count))
				xoff = (millis() / 25.0) * (i + 1)
				text(".", (x + xoff) % width, y)

def loadtree(callback):
	print "loading wordlist"
	tree = LetterTree()
	for line in open('wordlist_short'):
		line = line.strip()
		tree.feed(line + "$")
	callback(tree)

class TitleScreenState(GameState):
	def __init__(self):
		self.title = "CHARACTERROR"
		self.alpha = 255
		self.colors = [(64, 192, 0), (96, 224, 32), (128, 255, 64),
			(160, 0, 96), (192, 32, 128), (224, 64, 160),
			(255, 96, 192), (0, 128, 224), (32, 160, 255)]
		self.thread = None
		self.init_loading_threads()
		self.fading = False
		self.menu = [
			('instructions', 'How to play', 'Story and tutorial'),
			('90sec','Timed game: 90 seconds','Get the highest score in ninety seconds!'),
			('4min','Timed game: 4 minutes','You have four minutes. How high can you score?'),
			('challenge','50 letter challenge', "The timer's off. How many points can you score with just 50 letters?"),
			('credits', 'Credits', "Who made this game?")]
		self.selected = 0

	def init_loading_threads(self):
		# just running one thread to load resources for now
		self.thread = Thread(target=loadtree, args=(self.tree_load_done,))
		print "starting thread"
		self.thread.start()

	def tree_load_done(self, tree):
		self.tree = tree

	def draw(self):
		# draw banner
		textSize(48)
		textAlign(LEFT)
		xcenter = width / 2.0
		ypos = height / 3.0
		xstart = xcenter - (textWidth(self.title) / 2.0)
		pushMatrix()
		translate(xstart, ypos)
		idx = (frameCount / 32) % 9
		this_col = self.colors[idx:] + self.colors[:idx]
		for i, ch in enumerate(self.title):
			i = i % len(self.colors)
			fill(this_col[i][0], this_col[i][1], this_col[i][2], self.alpha)
			text(ch, 0, 0)
			translate(48, 0)
		popMatrix()

		# loading or menu
		textAlign(CENTER)
		fill(255, 255, 0, self.alpha)
		textSize(16)
		if self.thread.isAlive():
			num = (frameCount / 9) % 4
			ch = '|/-\\'
			text("LOADING " + ch[num], xcenter, 2 * height / 3.0)
		else:
			for i, (short, content, desc) in enumerate(self.menu):
				if self.selected == i:
					textSize(8)
					fill(255, self.alpha)
					text(desc, xcenter, height - 96)
				else:
					fill(192, self.alpha)
				textSize(16)
				text(content, xcenter, (2*(width/5)) + (i*24))
			textSize(8)
			fill(255, 255, 0, self.alpha)
			text("Choose option with UP and DOWN. Press <Z> to select.", xcenter, (height - 48))

	def keyPressed(self):
		if self.thread.isAlive():
			return
		if self.fading:
			return
		if key == CODED:
			if keyCode == UP:
				self.selected -= 1
			elif keyCode == DOWN:
				self.selected += 1
			self.selected = self.selected % len(self.menu)
		elif key == ord('z'):
			self.fading = True
			selected_option = self.menu[self.selected][0]
			T.addTween(self, alpha=-255, tweenTime=1000, tweenType=T.OUT_EXPO,
				onCompleteFunction=lambda: self.faded_out(selected_option))

	def faded_out(self, opt):
		# when fadeout completes, this is called
		self.manager.mute(self)
		if opt in ('90sec', '4min', 'challenge'):
			if opt == '90sec':
				remaining_time = 90
			elif opt == '4min':
				remaining_time = 240
			scorer = ScoreState()
			sketch.add_state(scorer)
			playfield = PlayfieldState(self.tree, scorer, opt)
			if opt == 'challenge':
				challenge = ChallengeState(50, lambda: playfield.timer_done())
				sketch.add_state(challenge)
				playfield.add_fire_listener(challenge)
			else:
				timer = TimerState(remaining_time, lambda: playfield.timer_done())
				sketch.add_state(timer)
				timer.start()
			sketch.add_state(playfield)
			sounds['etude1'].play(0)
		elif opt == 'instructions':
			sketch.add_state(InstructionsState(self, self.tree))
		elif opt == 'credits':
			sketch.add_state(CreditsState(self))

	def fade_in(self):
		self.manager.unmute(self)
		T.addTween(self, alpha=255, tweenTime=1000, tweenType=T.OUT_EXPO,
			onCompleteFunction=self.faded_in)

	def faded_in(self):
		self.fading = False

class InstructionsState(GameState):
	def __init__(self, title_screen, tree):
		self.title_screen = title_screen
		self.page = 0
		self.tree = tree
		self.init_demo()
	def init_demo(self):
		self.letterq = LetterQueue(5, play_offset_x + fighter_offset_x + 96,
			play_offset_y)
		for ch in 'cram':
			self.letterq.append(ch)
		self.fighter = Fighter(self.letterq, 1, 0)
		self.target = TargetString('s', self.tree, play_offset_x, play_offset_y)
		self.letter_sprites = list()
	def draw(self):
		if self.page == 0:
			fill(255)
			textAlign(CENTER)
			textSize(64)
			text("THE STORY", width/2, 64)
			textAlign(LEFT)
			textSize(16)
			text("""
You are CAPTAIN S. PELLER,
starfighter pilot extraordinaire.
Your mission: defeat the CHARAC-
TERRORS, evil space aliens bent on
galactic dominance. Their only
weakness: a CHARACTERROR will
subsume any letter fired into it.
CHARACTERRORS forming English words
can be detonated and thus destroyed.
""", 32, 96)
			pushMatrix()
			translate(0, 232)
			self.letterq.draw()
			self.fighter.draw()
			self.target.draw()
			for sp in self.letter_sprites:
				sp.draw()
			popMatrix()
			textAlign(CENTER)
			textSize(16)
			fill(255)
			text("Hit <Z> to fire letters, then\n<ENTER> when the word is green!",
				width/2, 390)
		elif self.page == 1:
			fill(255)
			textAlign(CENTER)
			textSize(64)
			text("CONTROLS", width/2, 64)
			textAlign(LEFT)
			textSize(16)
			text("""
<UP>/<DN> select target
<Z>       fire letter into target
<ENTER>   detonate target
<X>       shuffle letter magazine
<ESC>     help/quit

Words must be between three and ten
letters long. This game uses the
SOWPODS dictionary.

WARNING: Detonating a target that is
not green will reset your score
multiplier. Shuffling your magazine
may help you get at the letter you
want, but will cut your multiplier
in half.
""", 32, 96)
			textAlign(CENTER)
			text("Hit <Z> to continue.", width/2, 450)
		elif self.page == 2:
			fill(255)
			textAlign(CENTER)
			textSize(48)
			text("HINTS & TIPS", width/2, 64)
			textAlign(LEFT)
			textSize(16)
			text("""
* Longer words earn more points!
* Your score multiplier increases
  for every letter landed, and for
  every valid word detonated.
* If a target contains a string that
  could never begin a valid English
  word, the target is destroyed and
  your score multiplier reset.
* Your magazine will always *only*
  contain letters that can combine
  with targets to begin valid English
  words. Exercise your vocabulary!
* Words that can't be extended to
  form longer words will be detonated
  automatically.
""", 32, 96)
			textAlign(CENTER)
			text("Hit <Z> to continue.", width/2, 450)

	def fire(self):
		if not(self.target.active):
			return
		self.target.active = False
		sounds['shoot'].play(0)
		popped = self.letterq.pop()
		sprite = LetterSprite(popped, self.fighter.x, self.fighter.y)
		destx = play_offset_x + (len(self.target.content) * 16)
		desty = play_offset_y + (self.fighter.pos * 40)
		destpos = self.fighter.pos
		T.addTween(sprite, x=(destx-self.fighter.x), y=(desty-self.fighter.y),
			tweenTime=400, tweenType=T.OUT_EXPO,
			onCompleteFunction=lambda: self.letter_arrived(sprite, destpos))
		self.letter_sprites.append(sprite)

	def letter_arrived(self, sprite, pos):
		self.letter_sprites.remove(sprite)
		self.target.subsume(sprite.let)
		self.target.active = True

	def advance_page(self):
		self.page += 1

	def keyPressed(self):
		if self.page == 0:
			if key == ord('z') and self.target.content != "scram":
				self.fire()
			if key == ord('\n') and self.target.content == "scram":
				sounds['success'].play(0)
				T.addTween(self.target, alpha=-255, textsize=16, tweenTime=1000,
					onCompleteFunction=lambda: self.advance_page())
		elif self.page == 1:
			if key == ord('z'):
				self.page = 2
		elif self.page == 2:
			if key == ord('z'):
				self.title_screen.fade_in()
				self.manager.remove_state(self)

class CreditsState(GameState):
	def __init__(self, title_screen):
		self.title_screen = title_screen
	def draw(self):
		textAlign(CENTER)
		textSize(16)
		text("credits stuff here")
	def keyPressed(self):
		if key == ord('z'):
			self.title_screen.fade_in()
			self.manager.remove_state(self)

class Sketch(GameStateManager):
	def setup(self):
		frameRate(30)
		size(640, 480)
		fill(0)
		background(0)
		font = createFont("pcsenior.ttf", 16)
		textFont(font)
		sketch.add_state(StarFieldState())
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
minim = None
sounds = dict()

def setup():
	global minim
	sketch.setup()
	minim = Minim(this)
	sounds['shoot'] = minim.loadSnippet("shoot.wav")
	sounds['discard'] = minim.loadSnippet("discard.wav")
	sounds['failure'] = minim.loadSnippet("failure.wav")
	sounds['success'] = minim.loadSnippet("success.wav")
	sounds['etude1'] = minim.loadSnippet("etude1.wav")
	sounds['etude2'] = minim.loadSnippet("etude2.wav")
	sounds['tick'] = minim.loadSnippet("tick.wav")
def draw():
	sketch.draw()
def mouseClicked():
	sketch.mouseClicked()
def keyPressed():
	if key == 27:
		this.key = '\0'
	sketch.keyPressed()
def stop():
	for snip in sounds.vales():
		snip.close()
	minim.stop()

