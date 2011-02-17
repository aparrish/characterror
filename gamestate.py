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

class GameState(object):
	def __init__(self):
		self.manager = None

class GameStateManager(object):
	def __init__(self):
		self.states = list()
		self.muted_states = set()
	def add_state(self, state):
		self.states.append(state)
		state.manager = self
	def remove_state(self, state):
		assert state in self.states, "can't remove state that hasn't been added"
		self.states.remove(state)
	def draw(self):
		for state in self.states:
			if state not in self.muted_states and hasattr(state, 'draw'):
				state.draw()
	def mouseClicked(self):
		for state in self.states:
			if state not in self.muted_states and hasattr(state, 'mouseClicked'):
				state.mouseClicked()
	def keyPressed(self):
		for state in self.states:
			if state not in self.muted_states and hasattr(state, 'keyPressed'):
				state.keyPressed()
	def mute(self, state):
		self.muted_states.add(state)
	def unmute(self, state):
		if state in self.muted_states:
			self.muted_states.remove(state)
	def remove_instances(self, classes):
		self.states = [state for state in self.states \
			if type(state) not in classes]
	def get_instances(self, classes):
		return [state for state in self.states if type(state) in classes]

class WatcherState(GameState):
	def mouseClicked(self):
		self.manager.add_state(StarfieldState())

class StarfieldState(GameState):
	def __init__(self):
		self.pts = list()
		for i in range(100):
			self.pts.append((random.randrange(800), random.randrange(600)))
	def draw(self):
		for pt in self.pts:
			stroke(255)
			point(pt[0], pt[1])
